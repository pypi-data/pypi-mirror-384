import os
from typing import ClassVar

import numpy
import numpy.typing as npt

class IrapHeader:
    id: ClassVar[int] = ...  # read-only
    ncol: int
    nrow: int
    rot: float
    xinc: float
    xmax: float
    xori: float
    xrot: float
    yinc: float
    ymax: float
    yori: float
    yrot: float
    def __init__(
        self,
        ncol: int,
        nrow: int,
        xori: float = ...,
        yori: float = ...,
        xmax: float = ...,
        ymax: float = ...,
        xinc: float = ...,
        yinc: float = ...,
        rot: float = ...,
        xrot: float = ...,
        yrot: float = ...,
    ) -> None: ...
    def __eq__(self, arg0: object) -> bool: ...
    def __ne__(self, arg0: object) -> bool: ...

class IrapSurface:
    header: IrapHeader
    values: npt.NDArray[numpy.float32]
    def __init__(
        self, header: IrapHeader, values: npt.NDArray[numpy.float32]
    ) -> None: ...
    @staticmethod
    def from_ascii_file(arg0: os.PathLike) -> IrapSurface: ...
    @staticmethod
    def from_ascii_string(arg0: str) -> IrapSurface: ...
    @staticmethod
    def from_binary_buffer(arg0: bytes) -> IrapSurface: ...
    @staticmethod
    def from_binary_file(arg0: os.PathLike) -> IrapSurface: ...
    def to_ascii_file(self, arg0: os.PathLike) -> None: ...
    def to_ascii_string(self) -> str: ...
    def to_binary_buffer(self) -> bytes: ...
    def to_binary_file(self, arg0: os.PathLike) -> None: ...
