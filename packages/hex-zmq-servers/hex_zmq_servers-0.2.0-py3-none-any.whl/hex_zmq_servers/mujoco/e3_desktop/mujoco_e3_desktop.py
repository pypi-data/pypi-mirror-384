#!/usr/bin/env python3
# -*- coding:utf-8 -*-
################################################################
# Copyright 2025 Dong Zhaorui. All rights reserved.
# Author: Dong Zhaorui 847235539@qq.com
# Date  : 2025-09-17
################################################################

import os
import copy
import cv2
import numpy as np

import mujoco
from mujoco import viewer

from ..mujoco_base import HexMujocoBase
from ...zmq_base import (
    hex_zmq_ts_now,
    hex_zmq_ts_delta_ms,
    HexRate,
    HexSafeValue,
)

MUJOCO_CONFIG = {
    "states_rate": 250,
    "img_rate": 30,
    "headless": False,
    "sens_ts": True,
}


class HexMujocoE3Desktop(HexMujocoBase):

    def __init__(
        self,
        mujoco_config: dict = MUJOCO_CONFIG,
    ):
        HexMujocoBase.__init__(self)

        try:
            states_rate = mujoco_config["states_rate"]
            img_rate = mujoco_config["img_rate"]
            self.__headless = mujoco_config["headless"]
            self.__sens_ts = mujoco_config["sens_ts"]
        except KeyError as ke:
            missing_key = ke.args[0]
            raise ValueError(
                f"mujoco_config is not valid, missing key: {missing_key}")

        # mujoco init
        model_path = os.path.join(os.path.dirname(__file__), "model/scene.xml")
        self.__model = mujoco.MjModel.from_xml_path(model_path)
        self.__data = mujoco.MjData(self.__model)
        self.__sim_rate = int(1.0 / self.__model.opt.timestep)

        # state init
        self.__state_left_idx = [0, 1, 2, 3, 4, 5, 6]
        self.__state_right_idx = [14, 15, 16, 17, 18, 19, 20]
        self.__obj_pose_idx = [28, 29, 30, 31, 32, 33, 34]
        self.__ctrl_left_idx = [0, 1, 2, 3, 4, 5, 6]
        self.__ctrl_right_idx = [8, 9, 10, 11, 12, 13, 14]
        self._limits = np.stack(
            [
                self.__model.jnt_range[self.__state_left_idx, :],
                self.__model.jnt_range[self.__state_right_idx, :]
            ],
            axis=0,
        )
        self._dofs = np.array([
            len(self.__state_left_idx),
            len(self.__state_right_idx),
        ])
        keyframe_id = mujoco.mj_name2id(
            self.__model,
            mujoco.mjtObj.mjOBJ_KEY,
            "home",
        )
        self.__state_init = {
            "qpos": self.__model.key_qpos[keyframe_id],
            "qvel": np.zeros_like(self.__data.qvel),
            "ctrl": np.zeros_like(self.__data.ctrl),
        }
        self.__data.qpos = self.__state_init["qpos"]
        self.__data.qvel = self.__state_init["qvel"]
        self.__data.ctrl = self.__state_init["ctrl"]
        self.__states_trig_thresh = int(self.__sim_rate / states_rate)

        # camera init
        width, height = 400, 400
        head_fovy_rad = self.__model.cam_fovy[0] * np.pi / 180.0
        left_fovy_rad = self.__model.cam_fovy[1] * np.pi / 180.0
        right_fovy_rad = self.__model.cam_fovy[2] * np.pi / 180.0
        head_focal = 0.5 * height / np.tan(head_fovy_rad / 2.0)
        left_focal = 0.5 * height / np.tan(left_fovy_rad / 2.0)
        right_focal = 0.5 * height / np.tan(right_fovy_rad / 2.0)
        self._intri = np.array([
            [head_focal, head_focal, width / 2, height / 2],
            [left_focal, left_focal, width / 2, height / 2],
            [right_focal, right_focal, width / 2, height / 2],
        ])
        self.__rgb_cam = mujoco.Renderer(self.__model, height, width)
        self.__depth_cam = mujoco.Renderer(self.__model, height, width)
        self.__depth_cam.enable_depth_rendering()
        self.__img_trig_thresh = int(self.__sim_rate / img_rate)

        # viewer init
        mujoco.mj_forward(self.__model, self.__data)
        if not self.__headless:
            self.__viewer = viewer.launch_passive(self.__model, self.__data)

        # start work loop
        self._working.set()

    def __del__(self):
        HexMujocoBase.__del__(self)

    def reset(self) -> bool:
        self.__data.qpos = self.__state_init["qpos"]
        self.__data.qvel = self.__state_init["qvel"]
        self.__data.ctrl = self.__state_init["ctrl"]
        mujoco.mj_forward(self.__model, self.__data)
        if not self.__headless:
            self.__viewer.sync()
        return True

    def work_loop(self, hex_values: list[HexSafeValue]):
        states_left_value = hex_values[0]
        states_right_value = hex_values[1]
        states_obj_value = hex_values[2]
        cmds_left_value = hex_values[3]
        cmds_right_value = hex_values[4]
        head_rgb_value = hex_values[5]
        head_depth_value = hex_values[6]
        left_rgb_value = hex_values[7]
        left_depth_value = hex_values[8]
        right_rgb_value = hex_values[9]
        right_depth_value = hex_values[10]

        last_states_ts = {"s": 0, "ns": 0}
        states_left_count = 0
        states_right_count = 0
        states_obj_count = 0
        last_cmds_left_seq = -1
        last_cmds_right_seq = -1
        head_rgb_count = 0
        head_depth_count = 0
        left_rgb_count = 0
        left_depth_count = 0
        right_rgb_count = 0
        right_depth_count = 0

        rate = HexRate(self.__sim_rate)
        states_trig_count = 0
        img_trig_count = 0
        while self._working.is_set():
            states_trig_count += 1
            if states_trig_count >= self.__states_trig_thresh:
                states_trig_count = 0

                # states
                ts, states_left, states_right, states_obj = self.__get_states()
                if states_left is not None:
                    if hex_zmq_ts_delta_ms(ts, last_states_ts) > 1.0:
                        last_states_ts = ts
                        # states left
                        states_left_value.set(
                            (ts, states_left_count, states_left))
                        states_left_count = (states_left_count +
                                             1) % self._max_seq_num
                        # states right
                        states_right_value.set(
                            (ts, states_right_count, states_right))
                        states_right_count = (states_right_count +
                                              1) % self._max_seq_num
                        # states obj
                        states_obj_value.set(
                            (ts, states_obj_count, states_obj))
                        states_obj_count = (states_obj_count +
                                            1) % self._max_seq_num

                # cmds
                cmds_left_pack = cmds_left_value.get(timeout_s=-1.0)
                if cmds_left_pack is not None:
                    ts, seq, cmds_left = cmds_left_pack
                    delta_seq = (seq - last_cmds_left_seq) % self._max_seq_num
                    if delta_seq > 0 and delta_seq < 1e6:
                        last_cmds_left_seq = seq
                        if hex_zmq_ts_delta_ms(hex_zmq_ts_now(), ts) < 200.0:
                            self.__set_cmds(cmds_left, "left")

                cmds_right_pack = cmds_right_value.get(timeout_s=-1.0)
                if cmds_right_pack is not None:
                    ts, seq, cmds_right = cmds_right_pack
                    delta_seq = (seq - last_cmds_right_seq) % self._max_seq_num
                    if delta_seq > 0 and delta_seq < 1e6:
                        last_cmds_right_seq = seq
                        if hex_zmq_ts_delta_ms(hex_zmq_ts_now(), ts) < 200.0:
                            self.__set_cmds(cmds_right, "right")

            img_trig_count += 1
            if img_trig_count >= self.__img_trig_thresh:
                img_trig_count = 0

                # head rgb
                ts, rgb_img = self.__get_rgb("head_camera")
                if rgb_img is not None:
                    head_rgb_value.set((ts, head_rgb_count, rgb_img))
                    head_rgb_count = (head_rgb_count + 1) % self._max_seq_num

                # head depth
                ts, depth_img = self.__get_depth("head_camera")
                if depth_img is not None:
                    head_depth_value.set((ts, head_depth_count, depth_img))
                    head_depth_count = (head_depth_count +
                                        1) % self._max_seq_num

                # left rgb
                ts, rgb_img = self.__get_rgb("left_camera")
                if rgb_img is not None:
                    left_rgb_value.set((ts, left_rgb_count, rgb_img))
                    left_rgb_count = (left_rgb_count + 1) % self._max_seq_num

                # left depth
                ts, depth_img = self.__get_depth("left_camera")
                if depth_img is not None:
                    left_depth_value.set((ts, left_depth_count, depth_img))
                    left_depth_count = (left_depth_count +
                                        1) % self._max_seq_num

                # right rgb
                ts, rgb_img = self.__get_rgb("right_camera")
                if rgb_img is not None:
                    right_rgb_value.set((ts, right_rgb_count, rgb_img))
                    right_rgb_count = (right_rgb_count + 1) % self._max_seq_num

                # right depth
                ts, depth_img = self.__get_depth("right_camera")
                if depth_img is not None:
                    right_depth_value.set((ts, right_depth_count, depth_img))
                    right_depth_count = (right_depth_count +
                                         1) % self._max_seq_num

            # mujoco step
            mujoco.mj_step(self.__model, self.__data)
            if not self.__headless:
                self.__viewer.sync()

            # sleep
            rate.sleep()

    def __get_states(self):
        pos = copy.deepcopy(self.__data.qpos)
        vel = copy.deepcopy(self.__data.qvel)
        eff = copy.deepcopy(self.__data.qfrc_actuator)
        pos[self.__state_left_idx[-1]] = 0.8 - pos[self.__state_left_idx[-1]]
        vel[self.__state_left_idx[-1]] *= -1
        eff[self.__state_left_idx[-1]] *= -1
        pos[self.__state_right_idx[-1]] = 0.8 - pos[self.__state_right_idx[-1]]
        vel[self.__state_right_idx[-1]] *= -1
        eff[self.__state_right_idx[-1]] *= -1
        return self.__mujoco_ts() if self.__sens_ts else hex_zmq_ts_now(
        ), np.array([
            pos[self.__state_left_idx],
            vel[self.__state_left_idx],
            eff[self.__state_left_idx],
        ]).T, np.array([
            pos[self.__state_right_idx],
            vel[self.__state_right_idx],
            eff[self.__state_right_idx],
        ]).T, self.__data.qpos[self.__obj_pose_idx].copy()

    def __set_cmds(self, cmds: np.ndarray, robot_name: str):
        needed_idx = []
        if robot_name == "left":
            needed_idx = self.__ctrl_left_idx
        elif robot_name == "right":
            needed_idx = self.__ctrl_right_idx
        else:
            raise ValueError(f"unknown robot name: {robot_name}")
        self.__data.ctrl[needed_idx] = cmds
        self.__data.ctrl[needed_idx[-1]] = 0.8 - cmds[-1]
        self.__data.ctrl[needed_idx[-1] + 1] = self.__data.ctrl[needed_idx[-1]]

    def __get_rgb(self, camera_name: str):
        self.__rgb_cam.update_scene(self.__data, camera_name)
        rgb_img = self.__rgb_cam.render()
        return self.__mujoco_ts() if self.__sens_ts else hex_zmq_ts_now(
        ), cv2.cvtColor(rgb_img, cv2.COLOR_RGB2BGR)

    def __get_depth(self, camera_name: str):
        self.__depth_cam.update_scene(self.__data, camera_name)
        depth_m = self.__depth_cam.render().astype(np.float32)
        depth_img = np.clip(depth_m * 1000.0, 0, 65535).astype(np.uint16)
        return self.__mujoco_ts() if self.__sens_ts else hex_zmq_ts_now(
        ), depth_img

    def __mujoco_ts(self):
        mujoco_ts = self.__data.time
        return {
            "s": int(mujoco_ts // 1),
            "ns": int((mujoco_ts % 1) * 1_000_000_000),
        }

    def close(self):
        self._working.clear()
        self.__rgb_cam.close()
        self.__depth_cam.close()
        if not self.__headless:
            self.__viewer.close()
