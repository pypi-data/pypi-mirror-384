#!/usr/bin/env python3

"""Gathers all video metrics."""

from fractions import Fraction
import itertools
import logging
import os
import pathlib
import threading
import typing

import torch
import tqdm

from cutcutcodec.config.config import Config
from cutcutcodec.core.analysis.stream.rate_video import optimal_rate_video
from cutcutcodec.core.analysis.stream.shape import optimal_shape_video
from cutcutcodec.core.analysis.video.properties import get_duration_video
from cutcutcodec.core.classes.colorspace import Colorspace
from cutcutcodec.core.classes.frame_video import FrameVideo
from cutcutcodec.core.classes.stream_video import StreamVideo
from cutcutcodec.core.exceptions import OutOfTimeRange
from cutcutcodec.core.filter.video.colorspace import FilterVideoColorspace
from cutcutcodec.core.io.read_ffmpeg import ContainerInputFFMPEG
from cutcutcodec.core.opti.parallel.buffer import _FuncEvalThread, starmap
from cutcutcodec.utils import mround


__all__ = ["video_metrics"]


TORCH_LOCK = threading.Lock()


def _fill_missing_shape_and_rate(needs: dict[str, list], dis: StreamVideo, ref: StreamVideo | None):
    """Help for _yield_frames, change needs inplace."""
    for metric, (_, comparative, space, shape, _, rate) in needs.items():
        if shape is None:
            needs[metric][3] = (
                optimal_shape_video((ref if comparative else dis)[space]) or (720, 1080)
            )
        if rate is None:
            needs[metric][5] = (
                optimal_rate_video((ref if comparative else dis)[space]) or Fraction(3000, 1001)
            )


def _lpips_alex(ref: torch.Tensor, dis: torch.Tensor) -> torch.Tensor:
    from .quality import lpips
    with TORCH_LOCK:
        return lpips(ref, dis, net="alex", threads=os.cpu_count())


def _lpips_vgg(ref: torch.Tensor, dis: torch.Tensor) -> torch.Tensor:
    from .quality import lpips
    with TORCH_LOCK:
        return lpips(ref, dis, net="vgg", threads=os.cpu_count())


def _psnr(ref: torch.Tensor, dis: torch.Tensor) -> torch.Tensor:
    from .quality import psnr
    # the factors comes from https://github.com/fraunhoferhhi/vvenc/wiki/Encoder-Performance
    # and https://compression.ru/video/codec_comparison/2022/10_bit_report.html
    return psnr(ref, dis, weights=(6, 1, 1), threads=1)


def _read_paths(func: callable):
    """Decorate _yield_frames."""
    def _decorated_yield_frames(
        dis: pathlib.Path, ref: pathlib.Path or None, needs: dict[str]
    ) -> tuple[str, FrameVideo, FrameVideo] | tuple[str, FrameVideo]:
        if ref is None:
            with ContainerInputFFMPEG(dis) as dis_cont:
                dis_stream = dis_cont.out_select("video")[0]
                yield from func(dis_stream, None, needs)
        else:
            with ContainerInputFFMPEG(dis) as dis_cont, ContainerInputFFMPEG(ref) as ref_cont:
                dis_stream = dis_cont.out_select("video")[0]
                ref_stream = ref_cont.out_select("video")[0]
                yield from func(dis_stream, ref_stream, needs)
    return _decorated_yield_frames


def _ssim(ref: torch.Tensor, dis: torch.Tensor) -> torch.Tensor:
    from .quality import ssim
    # the factors comes from https://github.com/fraunhoferhhi/vvenc/wiki/Encoder-Performance
    # and https://compression.ru/video/codec_comparison/2022/10_bit_report.html
    return ssim(ref, dis, weights=(6, 1, 1), threads=1, data_range=1.0)


def _uvq(dis: torch.Tensor) -> torch.Tensor:
    from .quality import uvq
    with TORCH_LOCK:
        return uvq(dis, threads=max(2, os.cpu_count()//2))


@_read_paths
def _yield_frames(
    dis: StreamVideo, ref: StreamVideo | None, needs: dict[str, list]
) -> tuple[str, FrameVideo, FrameVideo] | tuple[str, FrameVideo]:
    """Read the file to yield the well formated frames."""
    # define the correct colour space for the reference
    ref_streams = {
        space: FilterVideoColorspace(
            [ref],
            Colorspace(
                space,
                ref.colorspace.primaries or Config().target_prim,
                ref.colorspace.transfer or Config().target_trc,
            ),
        ).out_streams[0]
        for space in {space for _, comparative, space, _, _, _ in needs.values() if comparative}
    }
    ref_streams = {  # optional squeeze no change colorspace
        s: ref if ref.colorspace == r.colorspace else r for s, r in ref_streams.items()
    }

    # define the correct color space for the distorded
    dis_streams = {
        space: FilterVideoColorspace(
            [dis],
            Colorspace(
                space,
                (
                    ref_streams[space].colorspace.primaries
                    if space in ref_streams else
                    (dis.colorspace.primaries or Config().target_prim)
                ),
                (
                    ref_streams[space].colorspace.transfer
                    if space in ref_streams else
                    (dis.colorspace.transfer or Config().target_trc)
                ),
            ),
        ).out_streams[0]
        for space in {space for _, _, space, _, _, _ in needs.values()}
    }
    dis_streams = {  # optional squeeze no change colorspace
        s: dis if dis.colorspace == d.colorspace else d for s, d in dis_streams.items()
    }

    # find missing shape and rate
    _fill_missing_shape_and_rate(needs, dis_streams, ref_streams)

    # retrieves all scenarios, sorted ensures repeatability to enable linear prediction
    config = sorted(
        {
            ("ref", space, shape, nbr, rate)
            for _, comparative, space, shape, nbr, rate in needs.values() if comparative
        } | {
            ("dis", space, shape, nbr, rate)
            for _, _, space, shape, nbr, rate in needs.values()
        }
    )

    # iterate until all frames are exhausted
    rate = optimal_rate_video(ref or dis) or Fraction(3000, 1001)
    for timestamp in itertools.count(1/(2*rate), 1/rate):
        # get all patches
        patches: dict[tuple, list[FrameVideo]] = {}
        for cat, space, shape, nbr, rate in config:
            try:
                patches[(cat, space, shape, nbr, rate)] = [
                    {"ref": ref_streams, "dis": dis_streams}[cat][space]
                    .snapshot(timestamp + i/rate, shape)
                    for i in range(nbr)
                ]
            except OutOfTimeRange:
                pass
        if not patches:  # if there is nothing left, it means we have reached the end
            break

        # combine patches
        for metric, (_, comparative, space, shape, nbr, rate) in needs.items():
            try:
                yield (
                    metric,
                    *((patches[("ref", space, shape, nbr, rate)],) if comparative else ()),
                    patches[("dis", space, shape, nbr, rate)],
                )
            except KeyError:
                pass


def _yield_frames_batch(
    dis: pathlib.Path, ref: pathlib.Path | None, needs: dict[str, list]
) -> tuple[str, Fraction, torch.Tensor, torch.Tensor] | tuple[str, Fraction, torch.Tensor]:
    """Gather frames in 128 Mo batches.

    Batches of shape (batch, nbr, height, width, channels).
    """
    def size(frames: list[tuple]) -> int:
        frame = frames[0][0][0]
        nbr = len(frames) * len(frames[0]) * len(frames[0][0])
        height, width, channels = frame.shape
        depth = torch.finfo(frame.dtype).bits // 8
        return nbr * height * width * channels * depth

    def cat(frames: list[tuple]) -> list[torch.Tensor]:
        return [
            torch.cat(
                [
                    patch.unsqueeze(0)
                    for patch in (
                        torch.cat([f.unsqueeze(0) for f in fs[i]], dim=0)
                        for fs in frames
                    )
                ],
                dim=0,
            )
            for i in range(len(frames[0]))
        ]

    batches: dict[str] = {}
    for metric, *ref_dis in _yield_frames(dis, ref, needs):
        batches[metric] = batches.get(metric, [])
        batches[metric].append(ref_dis)
        if size(batches[metric]) >= 128_000_000:
            yield (
                metric,
                batches[metric][0][0][0].time,
                *cat(batches[metric]),
            )
            del batches[metric]
    for metric, frames in batches.items():
        yield (
            metric,
            frames[0][0][0].time,
            *cat(frames),
        )


def video_metrics(
    dis: pathlib.Path | str | bytes,
    ref: typing.Optional[pathlib.Path | str | bytes] = None,
    **metrics,
) -> dict[str, list[float]]:
    """Simultaneously calculate multiple video metrics, comparative and no-reference.

    Parameters
    ----------
    dis : pathlike
        The distorted video file.
    ref : pathlike, optional
        The reference video file, used for comparative metrics only.
    lpips_alex : boolean, default=False
        Trigger the spacial comparative quality LPIPS metric with medium alex network.
        Call :py:func:`cutcutcodec.core.analysis.video.quality.lpips` on every frame.
    lpips_vgg : boolean, default=False
        Trigger the spacial comparative quality LPIPS metric with big vgg network.
        Call :py:func:`cutcutcodec.core.analysis.video.quality.lpips` on every frame.
    psnr : boolean, dafault=False
        Trigger the spacial comparative quality PSNR metric.
        Call :py:func:`cutcutcodec.core.analysis.video.quality.psnr` on every frame.
    ssim : boolean, default=False
        Trigger the spacial comparative quality SSIM metric.
        Call :py:func:`cutcutcodec.core.analysis.video.quality.ssim` on every frame.
    uvq : boolean, default=False
        Trigger the spacial and temporal no-reference quality UVQ metric.
        Call :py:func:`cutcutcodec.core.analysis.video.quality.uvq`.
    vmaf : boolean, default=False
        Trigger the spacial comparative quality VMAF metric.
        Call :py:func:`cutcutcodec.core.analysis.video.quality.vmaf.vmaf` on every frame.

    Returns
    -------
    metrics : dict[str, list[float]]
        Associate the corresponding scalar values with each metric.

    Notes
    -----
    The color space of the distorted video is converted to the same as the reference video.

    Examples
    --------
    >>> import pprint
    >>> from cutcutcodec.core.analysis.video.metrics import video_metrics
    >>> from cutcutcodec.utils import get_project_root
    >>> video = get_project_root() / "media" / "video" / "intro.webm"
    >>> res = video_metrics(video, video, psnr=True, ssim=True)
    >>> pprint.pprint(res)  # doctest: +ELLIPSIS
    {'psnr': [100.0,
              100.0,
              ...,
              100.0,
              100.0],
     'ssim': [1.0,
              1.0,
              ...,
              1.0,
              1.0]}
    >>>

    SeeAlso
    -------
    * `MSU Video Quality Measurement Tool <https://pypi.org/project/msu-vqmt/>`_.
    """
    dis = pathlib.Path(dis).expanduser()
    assert dis.exists(), f"the path {dis} doese not exists, it has to"
    if ref is not None:
        ref = pathlib.Path(ref).expanduser()
        assert ref.exists(), f"the path {ref} doese not exists, it has to"

    # predict video duration for progress bar
    duration = _FuncEvalThread(func=get_duration_video, arg=(dis,), daemon=True)

    # assess needs
    needs: dict[str, list] = {}  # metric: (func, comparative, space, shape, nbr, rate)
    for metric, value in metrics.items():
        match metric:
            case "lpips_alex":
                assert isinstance(value, bool), f"the lpips_alex arg must be a boolean, not {value}"
                if value:
                    assert ref is not None, \
                        "the lpips_alex comparative metric requires a reference video 'ref=...'"
                    needs["lpips_alex"] = [_lpips_alex, True, "r'g'b'", None, 1, None]
            case "lpips_vgg":
                assert isinstance(value, bool), f"the lpips_vgg arg must be a boolean, not {value}"
                if value:
                    assert ref is not None, \
                        "the lpips_vgg comparative metric requires a reference video 'ref=...'"
                    needs["lpips_vgg"] = [_lpips_vgg, True, "r'g'b'", None, 1, None]
            case "psnr":
                assert isinstance(value, bool), f"the psnr arg must be a boolean, not {value}"
                if value:
                    assert ref is not None, \
                        "the psnr comparative metric requires a reference video 'ref=...'"
                    needs["psnr"] = [_psnr, True, "y'pbpr", None, 1, None]
            case "ssim":
                assert isinstance(value, bool), f"the ssim arg must be a boolean, not {value}"
                if value:
                    assert ref is not None, \
                        "the ssim comparative metric requires a reference video 'ref=...'"
                    needs["ssim"] = [_ssim, True, "y'pbpr", None, 1, None]
            case "uvq":
                assert isinstance(value, bool), f"the uvq arg must be a boolean, not {value}"
                if value:
                    from .quality import uvq
                    needs["uvq"] = [uvq, False, "r'g'b'", (720, 1080), 5, Fraction(5)]
            case "vmaf":
                assert isinstance(value, bool), f"the vmaf arg must be a boolean, not {value}"
                if value:
                    assert ref is not None, \
                        "the vmaf comparative metric requires a reference video 'ref=...'"
                    from .quality import vmaf
                    needs["vmaf"] = [vmaf, True, "y'pbpr", None, 1, None]
            case _:
                logging.warning("the %s metric is unknown and ignored", metric)

    # calculate metrics in parallel on each batch
    metrics: dict[str, list[float]] = {}
    with tqdm.tqdm(
        desc="Video metrics",
        dynamic_ncols=True,
        leave=False,
        smoothing=1e-6,
        unit="sec_video",
    ) as progress_bar:
        for metric, timestamp, values in starmap(
            lambda metric, timestamp, *batches: (
                metric, round(float(timestamp), 2), needs[metric][0](*batches)
            ),
            _yield_frames_batch(dis, ref, needs),
            maxsize=os.cpu_count()
        ):
            metrics[metric] = metrics.get(metric, [])
            metrics[metric].extend(map(mround, values.ravel().tolist()))

            # progress bar
            progress_bar.total = max(
                progress_bar.total or round(float(duration.get()), 2), timestamp
            )
            progress_bar.update(timestamp - progress_bar.n)
        progress_bar.update(progress_bar.total or round(float(duration.get()), 2) - progress_bar.n)

    return metrics
