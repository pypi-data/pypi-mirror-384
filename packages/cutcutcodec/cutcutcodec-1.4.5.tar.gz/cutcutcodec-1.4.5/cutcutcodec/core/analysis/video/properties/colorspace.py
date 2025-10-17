#!/usr/bin/env python3

"""Find or guess the colorspace of a video stream."""

import pathlib

from cutcutcodec.core.classes.colorspace import Colorspace
from cutcutcodec.core.exceptions import DecodeError, MissingStreamError


def get_colorspace(
    filename: pathlib.Path | str | bytes, index: int = 0
) -> Colorspace:
    """Open the stream to read the colorspace.

    Parameters
    ----------
    filename : pathlike
        The pathlike of the file containing a video stream.
    index : int
        The relative index of the video stream being considered,
        by default the first stream encountered is selected.

    Returns
    -------
    colorspace : Colorspace
        The name of the guessed colorspace.

    Raises
    ------
    MissingStreamError
        If the file does not contain a playable video stream.

    Examples
    --------
    >>> from cutcutcodec.core.analysis.video.properties.colorspace import get_colorspace
    >>> from cutcutcodec.utils import get_project_root
    >>> media = get_project_root() / "media" / "video" / "intro.webm"
    >>> get_colorspace(media)
    Colorspace("y'pbpr", 'bt709', 'bt1361e, bt1361')
    >>>
    """
    from cutcutcodec.core.io.read_ffmpeg import ContainerInputFFMPEG
    assert isinstance(index, int), index.__class__.__name__
    try:
        with ContainerInputFFMPEG(filename) as container:
            stream = container.out_select("video")[index]
            return stream.colorspace
    except DecodeError as err:
        raise MissingStreamError from err
