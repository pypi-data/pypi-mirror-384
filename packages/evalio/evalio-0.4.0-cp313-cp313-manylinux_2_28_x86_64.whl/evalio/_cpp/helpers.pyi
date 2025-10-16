from collections.abc import Mapping, Sequence
import enum

import evalio._cpp.types


class DataType(enum.Enum):
    UINT8 = 2

    INT8 = 1

    UINT16 = 4

    UINT32 = 6

    INT16 = 3

    INT32 = 5

    FLOAT32 = 7

    FLOAT64 = 8

class Field:
    def __init__(self, *, name: str, datatype: DataType, offset: int) -> None: ...

    @property
    def name(self) -> str: ...

    @name.setter
    def name(self, arg: str, /) -> None: ...

    @property
    def datatype(self) -> DataType: ...

    @datatype.setter
    def datatype(self, arg: DataType, /) -> None: ...

    @property
    def offset(self) -> int: ...

    @offset.setter
    def offset(self, arg: int, /) -> None: ...

class PointCloudMetadata:
    def __init__(self, *, stamp: evalio._cpp.types.Stamp, width: int, height: int, point_step: int, row_step: int, is_bigendian: int, is_dense: int) -> None: ...

    @property
    def stamp(self) -> evalio._cpp.types.Stamp: ...

    @stamp.setter
    def stamp(self, arg: evalio._cpp.types.Stamp, /) -> None: ...

    @property
    def width(self) -> int: ...

    @width.setter
    def width(self, arg: int, /) -> None: ...

    @property
    def height(self) -> int: ...

    @height.setter
    def height(self, arg: int, /) -> None: ...

    @property
    def point_step(self) -> int: ...

    @point_step.setter
    def point_step(self, arg: int, /) -> None: ...

    @property
    def row_step(self) -> int: ...

    @row_step.setter
    def row_step(self, arg: int, /) -> None: ...

    @property
    def is_bigendian(self) -> int: ...

    @is_bigendian.setter
    def is_bigendian(self, arg: int, /) -> None: ...

    @property
    def is_dense(self) -> int: ...

    @is_dense.setter
    def is_dense(self, arg: int, /) -> None: ...

def pc2_to_evalio(arg0: PointCloudMetadata, arg1: Sequence[Field], arg2: bytes, /) -> evalio._cpp.types.LidarMeasurement: ...

def fill_col_row_major(arg: evalio._cpp.types.LidarMeasurement, /) -> None: ...

def fill_col_col_major(arg: evalio._cpp.types.LidarMeasurement, /) -> None: ...

def reorder_points(arg0: evalio._cpp.types.LidarMeasurement, arg1: int, arg2: int, /) -> None: ...

def shift_point_stamps(arg0: evalio._cpp.types.LidarMeasurement, arg1: evalio._cpp.types.Duration, /) -> None: ...

def helipr_bin_to_evalio(arg0: str, arg1: evalio._cpp.types.Stamp, arg2: evalio._cpp.types.LidarParams, /) -> evalio._cpp.types.LidarMeasurement: ...

def fill_col_split_row_velodyne(arg: evalio._cpp.types.LidarMeasurement, /) -> None: ...

def parse_csv_line(arg0: str, arg1: str, arg2: Mapping[str, int], /) -> tuple[evalio._cpp.types.Stamp, evalio._cpp.types.SE3]: ...

def closest(arg0: evalio._cpp.types.Stamp, arg1: evalio._cpp.types.Stamp, arg2: evalio._cpp.types.Stamp, /) -> bool: ...
