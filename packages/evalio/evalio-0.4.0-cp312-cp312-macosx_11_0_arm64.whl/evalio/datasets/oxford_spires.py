import os
from enum import auto
from pathlib import Path
from typing import Optional, Sequence

import numpy as np

from evalio.datasets.loaders import (
    LidarDensity,
    LidarFormatParams,
    LidarMajor,
    LidarPointStamp,
    LidarStamp,
    RosbagIter,
)
from evalio.types import SE3, SO3, Duration, ImuParams, LidarParams, Stamp, Trajectory

from .base import (
    Dataset,
    DatasetIterator,
)


class OxfordSpires(Dataset):
    """Dataset taken both indoors and outdoors on the Oxford campus.

    Note, we skip over a number of trajectories due to [missing ground truth data](https://docs.google.com/document/d/1RS9QSOP4rC7BWoCD6EYUCm9uV_oMkfa3b61krn9OLG8/edit?tab=t.0).

    Additionally, some of the ground truth has poses within a few milliseconds of each other - we skip over any ground truth values within 10 milliseconds of each other.
    """

    blenheim_palace_01 = auto()
    blenheim_palace_02 = auto()
    blenheim_palace_05 = auto()
    bodleian_library_02 = auto()
    christ_church_01 = auto()
    christ_church_02 = auto()
    christ_church_03 = auto()
    christ_church_05 = auto()
    keble_college_02 = auto()
    keble_college_03 = auto()
    keble_college_04 = auto()
    observatory_quarter_01 = auto()
    observatory_quarter_02 = auto()

    # ------------------------- For loading data ------------------------- #
    def data_iter(self) -> DatasetIterator:
        return RosbagIter(
            self.folder,
            "/hesai/pandar",
            "/alphasense_driver_ros/imu",
            self.lidar_params(),
            lidar_format=LidarFormatParams(
                stamp=LidarStamp.Start,
                point_stamp=LidarPointStamp.Start,
                major=LidarMajor.Column,
                density=LidarDensity.OnlyValidPoints,
            ),
        )

    def ground_truth_raw(self) -> Trajectory:
        # Some of these are within a few milliseconds of each other
        # skip over ones that are too close
        traj = Trajectory.from_csv(
            self.folder / "gt-tum.txt",
            ["sec", "x", "y", "z", "qx", "qy", "qz", "qw"],
            delimiter=" ",
        )

        poses: list[SE3] = []
        stamps: list[Stamp] = []
        for i in range(1, len(traj)):
            if traj.stamps[i] - traj.stamps[i - 1] > Duration.from_sec(1e-2):
                poses.append(traj.poses[i])
                stamps.append(traj.stamps[i])

        return Trajectory(metadata=traj.metadata, stamps=stamps, poses=poses)

    # ------------------------- For loading params ------------------------- #
    def cam_T_lidar(self) -> SE3:
        r = SO3(
            qx=0.5023769275907106,
            qy=0.49990425097844265,
            qz=-0.49648618825384844,
            qw=0.5012131556048427,
        )
        t = np.array([0.003242860366163889, -0.07368532755947366, -0.05485800045216396])
        return SE3(r, t)

    def cam_T_imu(self) -> SE3:
        r = SO3(
            qx=-0.003150684959962717,
            qy=0.7095105504964175,
            qz=-0.7046875827967661,
            qw=0.0005124164367280889,
        )
        t = np.array(
            [-0.005000230026155717, -0.0031440163748744266, -0.07336562959794378]
        )
        return SE3(r, t)

    def imu_T_lidar(self) -> SE3:
        return self.cam_T_imu().inverse() * self.cam_T_lidar()

    def imu_T_gt(self) -> SE3:
        # Ground truth was found in the lidar frame, but is reported in the "base frame"
        # We go back to the lidar frame (as this transform should be what they used as well)
        # then use calibration to go to imu frame
        # https://github.com/ori-drs/oxford_spires_dataset/blob/main/config/sensor.yaml
        gt_T_lidar = SE3(
            SO3(qx=0.0, qy=0.0, qz=1.0, qw=0.0), np.array([0.0, 0.0, 0.124])
        )
        return self.imu_T_lidar() * gt_T_lidar.inverse()

    def imu_params(self) -> ImuParams:
        # Same one as hilti
        # From their kalibur config (in pdf)
        # https://tp-public-facing.s3.eu-north-1.amazonaws.com/Challenges/2022/2022322_calibration_files.zip
        # https://www.bosch-sensortec.com/media/boschsensortec/downloads/datasheets/bst-bmi085-ds001.pdf
        return ImuParams(
            gyro=0.00019,
            accel=0.00132435,
            gyro_bias=0.000266,
            accel_bias=0.0043,
            bias_init=1e-8,
            integration=1e-8,
            gravity=np.array([0, 0, -9.81]),
            brand="Bosch",
            model="BMI085",
        )

    def lidar_params(self) -> LidarParams:
        return LidarParams(
            num_rows=64,
            num_columns=1200,
            min_range=1.0,
            max_range=60.0,
            brand="Hesai",
            model="QT-64",
        )

    # ------------------------- dataset info ------------------------- #
    @staticmethod
    def url() -> str:
        return "https://dynamic.robots.ox.ac.uk/datasets/oxford-spires/"

    def environment(self) -> str:
        if "observatory" in self.seq_name or "bodleian" in self.seq_name:
            return "Oxford Campus"
        else:
            return "Indoor & Oxford Campus"

    def vehicle(self) -> str:
        return "Backpack"

    # ------------------------- For downloading ------------------------- #
    def files(self) -> Sequence[str | Path]:
        return {
            "christ_church_02": [
                "1710754066_2024-03-18-09-27-47_0",
                "1710754066_2024-03-18-09-36-49_1",
                "gt-tum.txt",
            ],
            "blenheim_palace_01": [
                "1710406700_2024-03-14-08-58-21_0_blurred_filtered_compressed.db3",
                "gt-tum.txt",
                "metadata.yaml",
            ],
            "christ_church_05": [
                "1710926317_2024-03-20-09-18-38_0_blurred_filtered_compressed.db3",
                "gt-tum.txt",
                "metadata.yaml",
            ],
            "keble_college_03": [
                "1710256011_2024-03-12-15-06-52_0_blurred_filtered_compressed.db3",
                "gt-tum.txt",
                "metadata.yaml",
            ],
            "christ_church_01": [
                "1710752531_2024-03-18-09-02-12_0",
                "1710752531_2024-03-18-09-11-55_1",
                "gt-tum.txt",
            ],
            "bodleian_library_02": [
                "1716183690_2024-05-20-06-41-31_0_blurred_filtered_compressed.db3",
                "gt-tum.txt",
                "metadata.yaml",
            ],
            "blenheim_palace_02": [
                "1710407340_2024-03-14-09-09-01_0_blurred_filtered_compressed.db3",
                "gt-tum.txt",
                "metadata.yaml",
            ],
            "keble_college_04": [
                "1710256650_2024-03-12-15-17-31_0",
                "1710256650_2024-03-12-15-26-05_1",
                "gt-tum.txt",
            ],
            "observatory_quarter_01": [
                "1710338090_2024-03-13-13-54-51_blurred_filtered_compressed.db3",
                "gt-tum.txt",
                "metadata.yaml",
            ],
            "christ_church_03": [
                "1710755015_2024-03-18-09-43-36_0_blurred_filtered.db3",
                "gt-tum.txt",
                "metadata.yaml",
            ],
            "blenheim_palace_05": [
                "1710410169_2024-03-14-09-56-09_0_blurred_filtered.db3",
                "gt-tum.txt",
                "metadata.yaml",
            ],
            "observatory_quarter_02": [
                "1710338490_2024-03-13-14-01-30_blurred_filtered.db3",
                "gt-tum.txt",
                "metadata.yaml",
            ],
            "keble_college_02": [
                "1710255615_2024-03-12-15-00-16_0_blurred_filtered_compressed.db3",
                "gt-tum.txt",
                "metadata.yaml",
            ],
        }[self.seq_name]

    def download(self):
        folder_id = {
            "blenheim_palace_01": "1sQZhbdWZqyR0fLStesW2sJYuvIW9xyCD",
            "blenheim_palace_02": "1vaU7pn0cxbrBbJk1XKr9hOeeF7Zv00K9",
            "blenheim_palace_05": "1CZpiSX84g4391D-87E6AMlZI4ky1TG7p",
            "bodleian_library_02": "1koKUZrZ3dPazy2qwguPeFqla04V7-opp",
            # This one is split into two... figure out how to handle
            "christ_church_01": "1yd9jl1o4AEacKaYXCHV-AzV-FZTfRm6r",
            # This one is split into two... figure out how to handle
            "christ_church_02": "1f41VoG6mMAvpLxKciqGLhtOuj5iUK_3r",
            "christ_church_03": "14YTkMnxEWnE-iyrk30iu0I39QG-smREF",
            "christ_church_05": "1EDyyuFJ-KnLUv-S5IFv7OInNwPEFSHwl",
            "keble_college_02": "1qAocPo1_h8B2u-LdQoD2td49RJlD-1IW",
            "keble_college_03": "1u-QIvxQvjRXtt0k3vXYdB59XZQ61Khj9",
            # This one is split into two... figure out how to handle
            "keble_college_04": "1VJB8oIAoVVIhGCnbXKYz_uHfiNkwn9_i",
            "observatory_quarter_01": "1Wys3blrdfPVn-EFsXn_a0_0ngvzgSiFb",
            "observatory_quarter_02": "109uXFhqzYhn2bHv_37aQF7xPrJhOOu-_",
        }[self.seq_name]

        gt_url = {
            "blenheim_palace_01": "16et7vJhZ15yOCNYYU-i8HVOXemJM3puz",
            "blenheim_palace_02": "191MBEJuABCbb14LJhnJuvq4_ULqqbeQU",
            "blenheim_palace_05": "1jWYpiX4eUz1By1XN1g22ktzb-BCMyE7q",
            "bodleian_library_02": "1_EP7H_uO0XNhIKaFXB4nro8ymhpWB2qg",
            "christ_church_01": "1qXlfhf_0Jr6daeM3v9qmmhC-5yEI6TB5",
            "christ_church_02": "19vyhMivn4I1u-ZkLlIpoa7Nc3sdWNOU1",
            "christ_church_03": "13LbReIW7mJd6jMVBI6IcSRPWvpG6WP9c",
            "christ_church_05": "1Nxbjmwudu2b02Z2zWkJYO1I9rDPLe2Uf",
            "keble_college_02": "1hgNbsqIx8L0vM4rnPSX155sxxiIsDnJC",
            "keble_college_03": "1ybkRnb-wu4VMEqa37RUAHbUv2i-4UluB",
            "keble_college_04": "1iaGvgpDN-3CrwPPZzQjwAveXQOyQnAU4",
            "observatory_quarter_01": "1IOqvzepLesYecizYJh6JU0lJZu2WeW68",
            "observatory_quarter_02": "1iPQQD2zijlCf8a6J8YW5QBlVE2KsYRdZ",
        }[self.seq_name]

        import gdown

        print(f"Downloading to {self.folder}...")
        self.folder.mkdir(parents=True, exist_ok=True)
        gdown.download(id=gt_url, output=f"{self.folder}{os.sep}", resume=True)
        gdown.download_folder(id=folder_id, output=str(self.folder), resume=True)

    def quick_len(self) -> Optional[int]:
        # TODO: Missing some of the sequences here, need to figure out multi-folder mcap files
        return {
            "blenheim_palace_01": 4052,
            "blenheim_palace_02": 3674,
            "blenheim_palace_05": 3401,
            "bodleian_library_02": 5007,
            "christ_church_03": 3123,
            "christ_church_05": 8007,
            "keble_college_02": 3007,
            "keble_college_03": 2867,
            "observatory_quarter_01": 2894,
            "observatory_quarter_02": 2755,
        }.get(self.seq_name)
