#!/usr/bin/env python3
# -*- coding:utf-8 -*-
################################################################
# Copyright 2025 Dong Zhaorui. All rights reserved.
# Author: Dong Zhaorui 847235539@qq.com
# Date  : 2025-09-12
################################################################

import numpy as np

try:
    from ..cam_base import HexCamServerBase
    from .cam_berxel import HexCamBerxel
except (ImportError, ValueError):
    import sys
    from pathlib import Path
    this_file = Path(__file__).resolve()
    project_root = this_file.parents[3]
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
    from hex_zmq_servers.cam.cam_base import HexCamServerBase
    from hex_zmq_servers.cam.berxel.cam_berxel import HexCamBerxel

NET_CONFIG = {
    "ip": "127.0.0.1",
    "port": 12345,
    "client_timeout_ms": 200,
    "server_timeout_ms": 1_000,
    "server_num_workers": 4,
}

CAMERA_CONFIG = {
    "serial_number": 'P100RYB4C03M2B322',
    "exposure": 10000,
    "gain": 100,
    "frame_rate": 30,
    "sens_ts": True,
}


class HexCamBerxelServer(HexCamServerBase):

    def __init__(
        self,
        net_config: dict = NET_CONFIG,
        params_config: dict = CAMERA_CONFIG,
    ):
        HexCamServerBase.__init__(self, net_config)

        # camera
        self._device = HexCamBerxel(params_config)

    def _process_request(self, recv_hdr: dict, recv_buf: np.ndarray):
        if recv_hdr["cmd"] == "is_working":
            return self.no_ts_hdr(recv_hdr, self._device.is_working()), None
        elif recv_hdr["cmd"] == "get_intri":
            intri = self._device.get_intri()
            return self.no_ts_hdr(recv_hdr, intri is not None), intri
        elif recv_hdr["cmd"] == "get_rgb":
            return self._get_frame(recv_hdr, False)
        elif recv_hdr["cmd"] == "get_depth":
            return self._get_frame(recv_hdr, True)
        else:
            raise ValueError(f"unknown command: {recv_hdr['cmd']}")


if __name__ == "__main__":
    import argparse, json
    from hex_zmq_servers.zmq_base import hex_server_helper

    parser = argparse.ArgumentParser()
    parser.add_argument("--cfg", type=str, required=True)
    args = parser.parse_args()
    cfg = json.loads(args.cfg)

    hex_server_helper(cfg, HexCamBerxelServer)
