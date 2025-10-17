#!/usr/bin/env python
# -*- coding: utf-8 -*-

import io
import os
from io import BufferedWriter
from pathlib import Path
from typing import BinaryIO, Optional, Tuple, Union

from pythonwrench._core import _setup_output_fpath
from pythonwrench.functools import function_alias
from pythonwrench.importlib import Placeholder
from torch import Tensor

from torchwrench.core.packaging import _TORCHAUDIO_AVAILABLE

if not _TORCHAUDIO_AVAILABLE:
    msg = f"Cannot use python module {__file__} since torchaudio package is not installed."
    raise ImportError(msg)

import torchaudio

try:
    from torchaudio.io import CodecConfig  # type: ignore
except (ImportError, AttributeError):

    class CodecConfig(Placeholder): ...


def dump_with_torchaudio(
    src: Tensor,
    uri: Union[BinaryIO, str, Path, os.PathLike, None],
    sample_rate: int,
    channels_first: bool = True,
    format: Optional[str] = None,
    encoding: Optional[str] = None,
    bits_per_sample: Optional[int] = None,
    buffer_size: int = 4096,
    backend: Optional[str] = None,
    compression: Optional[Union[CodecConfig, float, int]] = None,
    *,
    overwrite: bool = True,
    make_parents: bool = True,
) -> bytes:
    """Dump tensors to audio waveform file. Requires torchaudio package installed."""
    if sample_rate <= 0:
        msg = f"Invalid argument {sample_rate=}. (expected positive value)"
        raise ValueError(msg)

    if isinstance(uri, (str, Path, os.PathLike)) or uri is None:
        uri = _setup_output_fpath(uri, overwrite, make_parents)

    buffer = io.BytesIO()
    torchaudio.save(  # type: ignore
        buffer,
        src,
        sample_rate,
        channels_first,
        format,
        encoding,
        bits_per_sample,
        buffer_size,
        backend,
        compression,  # type: ignore
    )
    content = buffer.getvalue()

    if isinstance(uri, Path):
        uri.write_bytes(content)
    elif isinstance(uri, (BinaryIO, BufferedWriter)):
        uri.write(content)
        uri.flush()

    return content


def load_with_torchaudio(
    uri: Union[BinaryIO, str, os.PathLike, Path],
    frame_offset: int = 0,
    num_frames: int = -1,
    normalize: bool = True,
    channels_first: bool = True,
    format: Optional[str] = None,
    buffer_size: int = 4096,
    backend: Optional[str] = None,
) -> Tuple[Tensor, int]:
    return torchaudio.load(  # type: ignore
        uri,
        frame_offset,
        num_frames,
        normalize,
        channels_first,
        format,
        buffer_size,
        backend,
    )


@function_alias(dump_with_torchaudio)
def dump_audio(*args, **kwargs): ...


@function_alias(load_with_torchaudio)
def load_audio(*args, **kwargs): ...
