from collections.abc import Mapping

import evalio._cpp.types


class Pipeline:
    """
    Base class for all pipelines. This class defines the interface for interacting with pipelines, and is intended to be subclassed by specific implementations.
    """

    def __init__(self) -> None:
        """Construct a new pipeline."""

    @staticmethod
    def name() -> str:
        """Name of the pipeline."""

    @staticmethod
    def default_params() -> dict[str, bool | int | float | str]:
        """Default parameters for the pipeline."""

    @staticmethod
    def url() -> str:
        """URL for more information about the pipeline."""

    @staticmethod
    def version() -> str:
        """Version of the pipeline."""

    def pose(self) -> evalio._cpp.types.SE3:
        """Most recent pose estimate."""

    def map(self) -> dict[str, list[evalio._cpp.types.Point]]:
        """Map of the environment."""

    def initialize(self) -> None:
        """
        Initialize the pipeline. Must be called after constructing the object and before setting parameters.
        """

    def add_imu(self, mm: evalio._cpp.types.ImuMeasurement) -> None:
        """Register an IMU measurement."""

    def add_lidar(self, mm: evalio._cpp.types.LidarMeasurement) -> dict[str, list[evalio._cpp.types.Point]]:
        """Register a LiDAR measurement."""

    def set_params(self, params: Mapping[str, bool | int | float | str]) -> dict[str, bool | int | float | str]:
        """
        Set parameters for the pipeline. This will override any default parameters.
        """

    def set_imu_params(self, params: evalio._cpp.types.ImuParams) -> None:
        """Set IMU parameters for the pipeline."""

    def set_lidar_params(self, params: evalio._cpp.types.LidarParams) -> None:
        """Set LiDAR parameters for the pipeline."""

    def set_imu_T_lidar(self, T: evalio._cpp.types.SE3) -> None:
        """Set the transformation from IMU to LiDAR frame."""

class KissICP(Pipeline):
    """
    KissICP LiDAR-only pipeline for point cloud registration. KissICP is designed to be simple and easy to use, while still providing good performance with minimal parameter tuning required across datasets.
    """

    def __init__(self) -> None: ...

    @staticmethod
    def name() -> str: ...

    @staticmethod
    def default_params() -> dict[str, bool | int | float | str]: ...

    @staticmethod
    def url() -> str: ...

    @staticmethod
    def version() -> str: ...

class LioSAM(Pipeline):
    """
    Lidar-Inertial Smoothing and Mapping (LioSAM) pipeline. LioSAM is an extension of LOAM (=> uses planar and edge features) that additionally utilizes an IMU for initializing ICP steps and for dewarping points
    """

    def __init__(self) -> None: ...

    @staticmethod
    def name() -> str: ...

    @staticmethod
    def default_params() -> dict[str, bool | int | float | str]: ...

    @staticmethod
    def url() -> str: ...

    @staticmethod
    def version() -> str: ...

class LOAM(Pipeline):
    """
    Lidar Odometry and Mapping (LOAM) pipeline. LOAM is a baseline lidar-only odometry method that pioneered feature-based ICP. Our implementation permits both scan-to-scan or scan-to-map matching.
    """

    def __init__(self) -> None: ...

    @staticmethod
    def name() -> str: ...

    @staticmethod
    def default_params() -> dict[str, bool | int | float | str]: ...

    @staticmethod
    def url() -> str: ...

    @staticmethod
    def version() -> str: ...

class GenZICP(Pipeline):
    """
    Genz-ICP LiDAR-only pipeline is an extension of KissICP that additionally estimates normals in the local submap voxel map for increased robustness. It also includes a novel weighting scheme for weighting point-to-plane and point-to-point correspondences.
    """

    def __init__(self) -> None: ...

    @staticmethod
    def name() -> str: ...

    @staticmethod
    def default_params() -> dict[str, bool | int | float | str]: ...

    @staticmethod
    def url() -> str: ...

    @staticmethod
    def version() -> str: ...

class MadICP(Pipeline):
    """
    MAD-ICP LiDAR-only pipeline is an extension of KissICP that utilizes a novel kd-tree representation that implicitly computes normals to perform point-to-plane registration.
    """

    def __init__(self) -> None: ...

    @staticmethod
    def name() -> str: ...

    @staticmethod
    def default_params() -> dict[str, bool | int | float | str]: ...

    @staticmethod
    def url() -> str: ...

    @staticmethod
    def version() -> str: ...

class CTICP(Pipeline):
    """
    CT-ICP LiDAR-only pipeline performs continuous-time ICP over a small window of scans to perform more accurate dewarping performance. This is the version based on the 2022-ICRA paper.
    """

    def __init__(self) -> None: ...

    @staticmethod
    def name() -> str: ...

    @staticmethod
    def default_params() -> dict[str, bool | int | float | str]: ...

    @staticmethod
    def url() -> str: ...

    @staticmethod
    def version() -> str: ...
