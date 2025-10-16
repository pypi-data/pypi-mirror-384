from collections.abc import Sequence
from typing import Annotated, Any, overload

import numpy
from numpy.typing import NDArray


class Duration:
    """
    Duration class for representing a positive or negative delta time. 

    Uses int64 as the underlying data storage for nanoseconds.
    """

    @staticmethod
    def from_sec(sec: float) -> Duration:
        """Create a Duration from seconds"""

    @staticmethod
    def from_nsec(nsec: int) -> Duration:
        """Create a Duration from nanoseconds"""

    def to_sec(self) -> float:
        """Convert to seconds"""

    def to_nsec(self) -> int:
        """Convert to nanoseconds"""

    @property
    def nsec(self) -> int:
        """Underlying nanoseconds representation"""

    def __lt__(self, arg: Duration, /) -> bool:
        """Compare two Durations"""

    def __gt__(self, arg: Duration, /) -> bool:
        """Compare two Durations"""

    def __eq__(self, arg: object, /) -> bool:
        """Check for equality"""

    def __ne__(self, arg: object, /) -> bool:
        """Check for inequality"""

    def __sub__(self, arg: Duration, /) -> Duration:
        """Compute the difference between two Durations"""

    def __add__(self, arg: Duration, /) -> Duration:
        """Add two Durations"""

    def __repr__(self) -> str: ...

    def __copy__(self) -> Duration: ...

    def __deepcopy__(self, memo: dict[Any, Any]) -> Duration: ...

    def __getstate__(self) -> tuple[int]: ...

    def __setstate__(self, arg: tuple[int], /) -> None: ...

class Stamp:
    """
    Stamp class for representing an absolute point in time.

    Uses uint32 as the underlying data storage for seconds and nanoseconds.
    """

    @overload
    def __init__(self, *, sec: int, nsec: int) -> None:
        """Create a Stamp from seconds and nanoseconds"""

    @overload
    def __init__(self, other: Stamp) -> None:
        """Copy constructor for Stamp."""

    @staticmethod
    def from_sec(sec: float) -> Stamp:
        """Create a Stamp from seconds"""

    @staticmethod
    def from_nsec(nsec: int) -> Stamp:
        """Create a Stamp from nanoseconds"""

    def to_sec(self) -> float:
        """Convert to seconds"""

    def to_nsec(self) -> int:
        """Convert to nanoseconds"""

    @property
    def sec(self) -> int:
        """Underlying seconds storage"""

    @property
    def nsec(self) -> int:
        """Underlying nanoseconds storage"""

    def __lt__(self, arg: Stamp, /) -> bool:
        """Compare two Stamps to see which happened first"""

    def __gt__(self, arg: Stamp, /) -> bool:
        """Compare two Stamps to see which happened first"""

    def __eq__(self, arg: object, /) -> bool:
        """Check for equality"""

    def __ne__(self, arg: object, /) -> bool:
        """Check for inequality"""

    @overload
    def __sub__(self, arg: Stamp, /) -> Duration:
        """Compute the difference between two Stamps, returning a duration"""

    @overload
    def __sub__(self, arg: Duration, /) -> Stamp:
        """Subtract a Duration from a Stamp"""

    def __add__(self, arg: Duration, /) -> Stamp:
        """Add a Duration to a Stamp"""

    def __repr__(self) -> str: ...

    def __copy__(self) -> Stamp: ...

    def __deepcopy__(self, memo: dict[Any, Any]) -> Stamp: ...

    def __getstate__(self) -> tuple[int, int]: ...

    def __setstate__(self, arg: tuple[int, int], /) -> None: ...

class Point:
    """
    Point is the general point structure in evalio, with common point cloud attributes included.
    """

    def __init__(self, *, x: float = 0, y: float = 0, z: float = 0, intensity: float = 0, t: Duration = ..., range: int = 0, row: int = 0, col: int = 0) -> None:
        """Create a Point from x, y, z, intensity, t, range, row, col"""

    @property
    def x(self) -> float:
        """X coordinate"""

    @x.setter
    def x(self, arg: float, /) -> None: ...

    @property
    def y(self) -> float:
        """Y coordinate"""

    @y.setter
    def y(self, arg: float, /) -> None: ...

    @property
    def z(self) -> float:
        """Z coordinate"""

    @z.setter
    def z(self, arg: float, /) -> None: ...

    @property
    def intensity(self) -> float:
        """Intensity value as a float."""

    @intensity.setter
    def intensity(self, arg: float, /) -> None: ...

    @property
    def range(self) -> int:
        """Range value as a uint32."""

    @range.setter
    def range(self, arg: int, /) -> None: ...

    @property
    def t(self) -> Duration:
        """
        Timestamp of the point as a Duration. In evalio, this is always relative to the point cloud stamp, which occurs at the start of the scan.
        """

    @t.setter
    def t(self, arg: Duration, /) -> None: ...

    @property
    def row(self) -> int:
        """
        Row index of the point in the point cloud. Also known as the scanline index.
        """

    @row.setter
    def row(self, arg: int, /) -> None: ...

    @property
    def col(self) -> int:
        """Column index of the point in the point cloud."""

    @col.setter
    def col(self, arg: int, /) -> None: ...

    def __eq__(self, arg: object, /) -> bool:
        """Check for equality"""

    def __ne__(self, arg: object, /) -> bool:
        """Check for inequality"""

    def __repr__(self) -> str: ...

    def __getstate__(self) -> tuple[float, float, float, float, Duration, int, int, int]: ...

    def __setstate__(self, arg: tuple[float, float, float, float, Duration, int, int, int], /) -> None: ...

class LidarMeasurement:
    """
    LidarMeasurement is a structure for storing a point cloud measurement, with a timestamp and a vector of points.

    Note, the stamp always represents the _start_ of the scan. Additionally, the points are always in row major format.
    """

    @overload
    def __init__(self, stamp: Stamp) -> None: ...

    @overload
    def __init__(self, stamp: Stamp, points: Sequence[Point]) -> None: ...

    @property
    def stamp(self) -> Stamp:
        """Timestamp of the point cloud, always at the start of the scan."""

    @stamp.setter
    def stamp(self, arg: Stamp, /) -> None: ...

    @property
    def points(self) -> list[Point]:
        """
        List of points in the point cloud. Note, this is always in row major format.
        """

    @points.setter
    def points(self, arg: Sequence[Point], /) -> None: ...

    def to_vec_positions(self) -> list[Annotated[NDArray[numpy.float64], dict(shape=(3), order='C')]]:
        """Convert the point cloud to a (n,3) numpy array."""

    def to_vec_stamps(self) -> list[float]:
        """Convert the point stamps to a list of durations."""

    def __eq__(self, arg: object, /) -> bool:
        """Check for equality"""

    def __ne__(self, arg: object, /) -> bool:
        """Check for inequality"""

    def __repr__(self) -> str: ...

    def __getstate__(self) -> tuple[Stamp, list[Point]]: ...

    def __setstate__(self, arg: tuple[Stamp, Sequence[Point]], /) -> None: ...

class LidarParams:
    """
    LidarParams is a structure for storing the parameters of a lidar sensor.
    """

    def __init__(self, *, num_rows: int, num_columns: int, min_range: float, max_range: float, rate: float = 10.0, brand: str = '-', model: str = '-') -> None: ...

    @property
    def num_rows(self) -> int:
        """Number of rows in the point cloud, also known as the scanlines."""

    @property
    def num_columns(self) -> int:
        """
        Number of columns in the point cloud, also known as the number of points per scanline.
        """

    @property
    def min_range(self) -> float:
        """Minimum range of the lidar sensor, in meters."""

    @property
    def max_range(self) -> float:
        """Maximum range of the lidar sensor, in meters."""

    @property
    def rate(self) -> float:
        """Rate of the lidar sensor, in Hz."""

    @property
    def brand(self) -> str:
        """Brand of the lidar sensor."""

    @property
    def model(self) -> str:
        """Model of the lidar sensor."""

    def delta_time(self) -> Duration:
        """
        Get the time between two consecutive scans as a Duration. Inverse of the rate.
        """

    def __repr__(self) -> str: ...

class ImuMeasurement:
    """ImuMeasurement is a simple structure for storing an IMU measurement."""

    def __init__(self, stamp: Stamp, gyro: Annotated[NDArray[numpy.float64], dict(shape=(3), order='C')], accel: Annotated[NDArray[numpy.float64], dict(shape=(3), order='C')]) -> None: ...

    @property
    def stamp(self) -> Stamp:
        """Timestamp of the IMU measurement."""

    @property
    def gyro(self) -> Annotated[NDArray[numpy.float64], dict(shape=(3), order='C')]:
        """Gyroscope measurement as a 3D vector."""

    @property
    def accel(self) -> Annotated[NDArray[numpy.float64], dict(shape=(3), order='C')]:
        """Accelerometer measurement as a 3D vector."""

    def __eq__(self, arg: object, /) -> bool:
        """Check for equality"""

    def __ne__(self, arg: object, /) -> bool:
        """Check for inequality"""

    def __repr__(self) -> str: ...

    def __getstate__(self) -> tuple[Stamp, Annotated[NDArray[numpy.float64], dict(shape=(3), order='C')], Annotated[NDArray[numpy.float64], dict(shape=(3), order='C')]]: ...

    def __setstate__(self, arg: tuple[Stamp, Annotated[NDArray[numpy.float64], dict(shape=(3), order='C')], Annotated[NDArray[numpy.float64], dict(shape=(3), order='C')]], /) -> None: ...

class ImuParams:
    """ImuParams is a structure for storing the parameters of an IMU"""

    def __init__(self, *, gyro: float = 1e-05, accel: float = 1e-05, gyro_bias: float = 1e-06, accel_bias: float = 1e-06, bias_init: float = 1e-07, integration: float = 1e-07, gravity: Annotated[NDArray[numpy.float64], dict(shape=(3), order='C')] = ..., brand: str = '-', model: str = '-') -> None: ...

    @staticmethod
    def up() -> ImuParams:
        """Simple helper for initializing with an `up` gravity vector."""

    @staticmethod
    def down() -> ImuParams:
        """Simple helper for initializing with a `down` gravity vector."""

    @property
    def gyro(self) -> float:
        """Gyroscope standard deviation, in rad/s/sqrt(Hz)."""

    @property
    def accel(self) -> float:
        """Accelerometer standard deviation, in m/s^2/sqrt(Hz)."""

    @property
    def gyro_bias(self) -> float:
        """Gyroscope bias standard deviation, in rad/s^2/sqrt(Hz)."""

    @property
    def accel_bias(self) -> float:
        """Accelerometer bias standard deviation, in m/s^3/sqrt(Hz)."""

    @property
    def bias_init(self) -> float:
        """Initial bias standard deviation."""

    @property
    def integration(self) -> float:
        """Integration standard deviation."""

    @property
    def gravity(self) -> Annotated[NDArray[numpy.float64], dict(shape=(3), order='C')]:
        """Gravity vector as a 3D vector."""

    @property
    def brand(self) -> str:
        """Brand of the IMU sensor."""

    @property
    def model(self) -> str:
        """Model of the IMU sensor."""

    def __repr__(self) -> str: ...

class SO3:
    """
    SO3 class for representing a 3D rotation using a quaternion.

    This is outfitted with some basic functionality, but mostly intended for storage and converting between types.
    """

    def __init__(self, *, qx: float, qy: float, qz: float, qw: float) -> None: ...

    @property
    def qx(self) -> float:
        """X component of the quaternion."""

    @property
    def qy(self) -> float:
        """Y component of the quaternion."""

    @property
    def qz(self) -> float:
        """Z component of the quaternion."""

    @property
    def qw(self) -> float:
        """Scalar component of the quaternion."""

    @staticmethod
    def identity() -> SO3:
        """Create an identity rotation."""

    @staticmethod
    def fromMat(mat: Annotated[NDArray[numpy.float64], dict(shape=(3, 3), order='F')]) -> SO3:
        """Create a rotation from a 3x3 rotation matrix."""

    @staticmethod
    def exp(v: Annotated[NDArray[numpy.float64], dict(shape=(3), order='C')]) -> SO3:
        """Create a rotation from a 3D vector."""

    def inverse(self) -> SO3:
        """Compute the inverse of the rotation."""

    def log(self) -> Annotated[NDArray[numpy.float64], dict(shape=(3), order='C')]:
        """Compute the logarithm of the rotation."""

    def toMat(self) -> Annotated[NDArray[numpy.float64], dict(shape=(3, 3), order='F')]:
        """Convert the rotation to a 3x3 matrix."""

    def rotate(self, v: Annotated[NDArray[numpy.float64], dict(shape=(3), order='C')]) -> Annotated[NDArray[numpy.float64], dict(shape=(3), order='C')]:
        """Rotate a 3D vector by the rotation."""

    def __mul__(self, arg: SO3, /) -> SO3:
        """Compose two rotations."""

    def __eq__(self, arg: object, /) -> bool:
        """Check for equality"""

    def __ne__(self, arg: object, /) -> bool:
        """Check for inequality"""

    def __repr__(self) -> str: ...

    def __copy__(self) -> SO3: ...

    def __deepcopy__(self, memo: dict[Any, Any]) -> SO3: ...

    def __getstate__(self) -> tuple[float, float, float, float]: ...

    def __setstate__(self, arg: tuple[float, float, float, float], /) -> None: ...

class SE3:
    """
    SE3 class for representing a 3D rigid body transformation using a quaternion and a translation vector.

    This is outfitted with some basic functionality, but is mostly intended for storage and converting between types.
    """

    @overload
    def __init__(self, rot: SO3, trans: Annotated[NDArray[numpy.float64], dict(shape=(3), order='C')]) -> None:
        """Create a SE3 from a rotation and translation."""

    @overload
    def __init__(self, other: SE3) -> None:
        """Copy constructor for SE3."""

    @staticmethod
    def identity() -> SE3:
        """Create an identity SE3."""

    @staticmethod
    def fromMat(mat: Annotated[NDArray[numpy.float64], dict(shape=(4, 4), order='F')]) -> SE3:
        """Create a SE3 from a 4x4 transformation matrix."""

    @property
    def rot(self) -> SO3:
        """Rotation as a SO3 object."""

    @property
    def trans(self) -> Annotated[NDArray[numpy.float64], dict(shape=(3), order='C')]:
        """Translation as a 3D vector."""

    def toMat(self) -> Annotated[NDArray[numpy.float64], dict(shape=(4, 4), order='F')]:
        """Convert to a 4x4 matrix."""

    def inverse(self) -> SE3:
        """Compute the inverse."""

    @staticmethod
    def error(a: SE3, b: SE3) -> tuple[float, float]:
        """
        Compute the rotational (degrees) and translational (meters) error between two SE3s as a tuple (rot, trans).
        """

    @staticmethod
    def distance(a: SE3, b: SE3) -> float:
        """Compute the distance between two SE3s."""

    @staticmethod
    def exp(xi: Annotated[NDArray[numpy.float64], dict(shape=(6), order='C')]) -> SE3:
        """Create a SE3 from a 3D vector."""

    def log(self) -> Annotated[NDArray[numpy.float64], dict(shape=(6), order='C')]:
        """Compute the logarithm of the transformation."""

    def __mul__(self, arg: SE3, /) -> SE3:
        """Compose two rigid body transformations."""

    def __eq__(self, arg: object, /) -> bool:
        """Check for equality"""

    def __ne__(self, arg: object, /) -> bool:
        """Check for inequality"""

    def __repr__(self) -> str: ...

    def __copy__(self) -> SE3: ...

    def __deepcopy__(self, memo: dict[Any, Any]) -> SE3: ...

    def __getstate__(self) -> tuple[float, float, float, float, float, float, float]: ...

    def __setstate__(self, arg: tuple[float, float, float, float, float, float, float], /) -> None: ...
