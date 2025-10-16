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
from evalio.types import SE3, SO3, ImuParams, LidarParams, Trajectory

from .base import (
    Dataset,
    DatasetIterator,
)


class NewerCollege2021(Dataset):
    """Dataset outdoors on oxford campus with a handheld device consisting of an alphasense core and a Ouster lidar.
    Ground truth is captured ICP matching against a laser scanner map.

    Note there are two IMUs present; we utilize the Ouster IMU (ICM-20948)) instead of the alphasense one (Bosch BMI085).
    We expect the Ouster IMU to have more accurate extrinsics and the specs between the two IMUs are fairly similar.
    """

    quad_easy = auto()
    quad_medium = auto()
    quad_hard = auto()
    stairs = auto()
    cloister = auto()
    park = auto()
    maths_easy = auto()
    maths_medium = auto()
    maths_hard = auto()

    # ------------------------- For loading data ------------------------- #
    def data_iter(self) -> DatasetIterator:
        return RosbagIter(
            self.folder,
            "/os_cloud_node/points",
            "/os_cloud_node/imu",
            self.lidar_params(),
            lidar_format=LidarFormatParams(
                stamp=LidarStamp.Start,
                point_stamp=LidarPointStamp.Start,
                major=LidarMajor.Row,
                density=LidarDensity.AllPoints,
            ),
        )

    def ground_truth_raw(self) -> Trajectory:
        gt_file = self.files()[-1]
        return Trajectory.from_csv(
            self.folder / gt_file,
            ["sec", "nsec", "x", "y", "z", "qx", "qy", "qz", "qw"],
        )

    # ------------------------- For loading params ------------------------- #
    def imu_T_lidar(self) -> SE3:
        return SE3(
            SO3(qx=0.0032925, qy=-0.004627, qz=-0.0024302, qw=0.99998),
            np.array([0.013801, -0.012207, -0.01514]),
        )

    def imu_T_gt(self) -> SE3:
        return SE3(
            SO3(qx=0.0032925, qy=-0.004627, qz=-0.0024302, qw=0.99998),
            np.array([0.013642, -0.011607, -0.10583]),
        )

    def imu_params(self) -> ImuParams:
        # ICM-20948
        # https://invensense.tdk.com/wp-content/uploads/2024/03/DS-000189-ICM-20948-v1.6.pdf
        return ImuParams(
            gyro=0.000261799387799,
            accel=0.0022563,
            gyro_bias=0.0000261799387799,
            accel_bias=0.00022563,
            bias_init=1e-8,
            integration=1e-8,
            gravity=np.array([0, 0, -9.81]),
            brand="TDK",
            model="ICM-20948",
        )

    def lidar_params(self) -> LidarParams:
        return LidarParams(
            num_rows=128,
            num_columns=1024,
            min_range=0.1,
            max_range=50.0,
            brand="Ouster",
            model="OS1-128",
        )

    # ------------------------- dataset info ------------------------- #
    @staticmethod
    def url() -> str:
        return "https://ori-drs.github.io/newer-college-dataset/multi-cam/"

    def environment(self) -> str:
        return "Oxford Campus"

    def vehicle(self) -> str:
        return "Handheld"

    # ------------------------- For downloading ------------------------- #
    def files(self) -> Sequence[str | Path]:
        # parse ground truth file
        if "maths" in self.seq_name:
            difficulty = self.seq_name.split("_")[1]
            gt_file = f"gt_state_{difficulty}.csv"
        else:
            name = self.seq_name.replace("_", "-")
            gt_file = f"gt-nc-{name}.csv"

        return {
            "cloister": [
                "2021-12-02-10-15-59_0-cloister.bag",
                "2021-12-02-10-19-05_1-cloister.bag",
            ],
            "maths_medium": [
                "2021-04-07-13-55-18-math-medium.bag",
            ],
            "quad_medium": [
                "2021-07-01-11-31-35_0-quad-medium.bag",
            ],
            "maths_hard": [
                "2021-04-07-13-58-54_0-math-hard.bag",
                "2021-04-07-14-02-18_1-math-hard.bag",
            ],
            "quad_hard": [
                "2021-07-01-11-35-14_0-quad-hard.bag",
            ],
            "quad_easy": [
                "2021-07-01-10-37-38-quad-easy.bag",
            ],
            "park": [
                "2021-11-30-17-09-49_0-park.bag",
                "2021-11-30-17-13-13_1-park.bag",
                "2021-11-30-17-16-38_2-park.bag",
                "2021-11-30-17-20-07_3-park.bag",
                "2021-11-30-17-23-25_4-park.bag",
                "2021-11-30-17-26-36_5-park.bag",
                "2021-11-30-17-30-06_6-park.bag",
                "2021-11-30-17-33-19_7-park.bag",
            ],
            "maths_easy": [
                "2021-04-07-13-49-03_0-math-easy.bag",
                "2021-04-07-13-52-31_1-math-easy.bag",
            ],
            "stairs": [
                "2021-07-01-10-40-50_0-stairs.bag",
            ],
        }[self.seq_name] + [gt_file]

    def download(self):
        bag_ids = {
            "quad_easy": ["1hF2h83E1THbFAvs7wpR6ORmrscIHxKMo"],
            "quad_medium": ["11bZfJce1MCM4G9YUTCyUifM715N7FSbO"],
            "quad_hard": ["1ss6KPSTZ4CRS7uHAMgqnd4GQ6tKEEiZD"],
            "stairs": ["1ql0C8el5PJs6O0x4xouqaW9n2RZy53q9"],
            "cloister": [
                "1zzX_ZrMkVOtpSoD2jQg6Gdrtv8-UjYbF",
                "1QNFQSb81gG1_jX338vO7RQkScKGT_hf1",
            ],
            "park": [
                "1KZo-gPVQTMJ4hRaiaqV3hfuVNaONScDp",
                "1eGVPwFSaG0M2M7Lci6IBjKQrEf1uqtVn",
                "1nhuoH0OcLbovbXkq3eW6whk6TIKk2SEu",
                "1pXBE1iD9iivFFliFFNs7uvWi1zjo1S0s",
                "1_eZ5i2CGL7fNHeowRd1P_sllX1nxGwGL",
                "1wMCZVbB7eaSuz6u3ObSTdGbgbRFyRQ7m",
                "10o1oR7guReYKiVk3nBiPrFWp1MnERTiH",
                "1VpLV_WUJqr770NBjF-O-DrXb5dhXRWyM",
            ],
            "maths_easy": [
                "1wRnRSni9bcBRauJEJ80sxHIaJaonrC3C",
                "1ORkYwGpQNvD48WRXICDDecbweg8MxYA8",
            ],
            "maths_medium": ["1IOq2e8Nfx79YFauBHCgdBSW9Ur5710GD"],
            "maths_hard": [
                "1qD147UWPo30B9lK3gABggCOxSAU6Pop2",
                "1_Mps_pCeUz3ZOc53lj6Hy_zDeJfPAqy8",
            ],
        }[self.seq_name]

        gt_ids = {
            "quad_easy": "1BdQiOhb_NW7VqjNtbbRAjI0JH56uKFI-",
            "quad_medium": "18aHhzTcVzXsppmk2WpiZnJhzOfREUwYP",
            "quad_hard": "1KMAG65pH8PsHUld-hTkFK4-SIIBqT5yP",
            "stairs": "17q_NYxn1SLBmUq20jgljO8HSlFF9LjDs",
            "cloister": "15I8qquSPWlySuY5_4ZBa_wL4UC7c-rQ7",
            "park": "1AkJ7lm5x2WdS3aGhKwe1PnUn6w0rbUjf",
            "maths_easy": "1dq1PqMODQBb4Hkn82h2Txgf5ZygS5udp",
            "maths_medium": "1H1U3aXv2AJQ_dexTnjaHIfzYfx8xVXpS",
            "maths_hard": "1Rb2TBKP7ISC2XzDGU68ix5lFjEB6jXeX",
        }[self.seq_name]

        import gdown

        print(f"Downloading to {self.folder}...")
        self.folder.mkdir(parents=True, exist_ok=True)
        gdown.download(id=gt_ids, output=f"{self.folder}{os.sep}", resume=True)
        for bid in bag_ids:
            gdown.download(id=bid, output=f"{self.folder}{os.sep}", resume=True)

    def quick_len(self) -> Optional[int]:
        return {
            "quad_easy": 1991,
            "quad_medium": 1910,
            "quad_hard": 1880,
            "stairs": 1190,
            "cloister": 2788,
            "park": 15722,
            "maths_easy": 2160,
            "maths_medium": 1770,
            "maths_hard": 2440,
        }[self.seq_name]
