#!/usr/bin/env python3

"""Find the codec name of a video stream."""

import collections
import pathlib
import typing

import cv2  # pip install opencv-contrib-python-headless

from cutcutcodec.core.analysis._helper_properties import _check_pathexists_index, _mix_and_check
from cutcutcodec.core.analysis.ffprobe import _estimate_codec_ffmpeg, _map_index_rel_to_abs
from cutcutcodec.core.exceptions import MissingStreamError, MissingInformation


def _estimate_codec_cv2(filename: str, index: int) -> tuple[int, int]:
    """Retrieve via cv2, the metadata concerning the codec name.

    This function is fast because it reads only the header of the file.

    Examples
    --------
    >>> from cutcutcodec.core.analysis.video.properties.codec import _estimate_codec_cv2
    >>> from cutcutcodec.utils import get_project_root
    >>> media = str(get_project_root() / "media" / "video" / "intro.webm")
    >>> _estimate_codec_cv2(media, 0)
    'vp90'
    >>>
    """
    cap = cv2.VideoCapture(filename, index)
    if not cap.isOpened():
        raise MissingStreamError(f"impossible to open '{filename}' stream {index} with 'cv2'")
    if (fourcc := cap.get(cv2.CAP_PROP_FOURCC)) is None:  # CAP_PROP_CODEC_EXTRADATA_INDEX
        raise MissingInformation(
            f"'cv2' did not find the codec of '{filename}' stream {index}"
        )
    codec = "".join([chr((int(fourcc) >> 8 * i) & 0xFF) for i in range(4)])
    return codec.lower()


def get_codec_video(
    filename: pathlib.Path | str | bytes,
    index: int = 0,
    *,
    backend: typing.Optional[str] = None,
) -> str:
    """Recovers the codec name of a video stream.

    Parameters
    ----------
    filename : pathlike
        The pathlike of the file containing a video stream.
    index : int
        The relative index of the video stream being considered,
        by default the first video stream encountered is selected.
    backend : str, optional
        - None (default) : Try to read the stream by trying differents backends.
        - 'ffmpeg' : Uses the ``ffmpeg`` program in the background.
        - 'cv2' : Uses the module ``pip install opencv-contrib-python-headless``.

    Returns
    -------
    name : str
        The little codec name of the considered stream.

    Raises
    ------
    MissingStreamError
        If the file does not contain a playable video stream.
    MissingInformation
        If the information is unavailable.

    Examples
    --------
    >>> from cutcutcodec.core.analysis.video.properties.codec import get_codec_video
    >>> from cutcutcodec.utils import get_project_root
    >>> video = get_project_root() / "media" / "video" / "intro.webm"
    >>> get_codec_video(video)
    'vp9'
    >>>
    """
    _check_pathexists_index(filename, index)

    return _mix_and_check(
        backend, False, (str(pathlib.Path(filename)), index),
        collections.OrderedDict([
            (
                (
                    lambda filename, index: _estimate_codec_ffmpeg(
                        filename, _map_index_rel_to_abs(filename, index, "video")
                    )
                ),
                {"accurate": False, "backend": "ffmpeg"},
            ),
            (_estimate_codec_cv2, {"accurate": False, "backend": "cv2"}),
        ])
    )
