"""An analytical kinematics engine for Reachy Mini, using Rust bindings.

The inverse kinematics use an analytical method, while the forward kinematics
use a numerical method (Newton).
"""

import json
from importlib.resources import files
from typing import Annotated

import numpy as np
from numpy.typing import NDArray
from reachy_mini_rust_kinematics import ReachyMiniRustKinematics

import reachy_mini

# Duplicated for now.
SLEEP_HEAD_POSE = np.array(
    [
        [0.911, 0.004, 0.413, -0.021],
        [-0.004, 1.0, -0.001, 0.001],
        [-0.413, -0.001, 0.911, -0.044],
        [0.0, 0.0, 0.0, 1.0],
    ]
)


class AnalyticalKinematics:
    """Reachy Mini Analytical Kinematics class, implemented in Rust with python bindings."""

    def __init__(self) -> None:
        """Initialize."""
        assets_root_path: str = str(files(reachy_mini).joinpath("assets/"))
        data_path = assets_root_path + "/kinematics_data.json"
        data = json.load(open(data_path, "rb"))

        self.head_z_offset = data["head_z_offset"]

        self.kin = ReachyMiniRustKinematics(
            data["motor_arm_length"], data["rod_length"]
        )

        self.start_body_yaw = 0.0

        self.motors = data["motors"]
        for motor in self.motors:
            self.kin.add_branch(
                motor["branch_position"],
                np.linalg.inv(motor["T_motor_world"]),  # type: ignore[arg-type]
                1 if motor["solution"] else -1,
            )

        sleep_head_pose = SLEEP_HEAD_POSE.copy()
        sleep_head_pose[:3, 3][2] += self.head_z_offset
        self.kin.reset_forward_kinematics(sleep_head_pose)  # type: ignore[arg-type]

    def ik(
        self,
        pose: Annotated[NDArray[np.float64], (4, 4)],
        body_yaw: float = 0.0,
        check_collision: bool = False,
        no_iterations: int = 0,
    ) -> Annotated[NDArray[np.float64], (7,)]:
        """Compute the inverse kinematics for a given head pose.

        check_collision and no_iterations are not used by AnalyticalKinematics. We keep them for compatibility with the other kinematics engines
        """
        _pose = pose.copy()
        _pose[:3, 3][2] += self.head_z_offset

        stewart_joints = self.kin.inverse_kinematics(_pose, body_yaw)  # type: ignore[arg-type]

        return np.array([body_yaw] + stewart_joints)

    def fk(
        self,
        joint_angles: Annotated[NDArray[np.float64], (7,)],
        check_collision: bool = False,
        no_iterations: int = 3,
    ) -> Annotated[NDArray[np.float64], (4, 4)]:
        """Compute the forward kinematics for a given set of joint angles.

        check_collision is not used by AnalyticalKinematics.
        """
        body_yaw = joint_angles[0]

        _joint_angles = joint_angles[1:].tolist()

        if no_iterations < 1:
            raise ValueError("no_iterations must be at least 1")

        T_world_platform = None
        for _ in range(no_iterations):
            T_world_platform = np.array(
                self.kin.forward_kinematics(_joint_angles, body_yaw)
            )

        assert T_world_platform is not None

        T_world_platform[:3, 3][2] -= self.head_z_offset

        return T_world_platform
