# coding: utf-8

import os
import tempfile

from tomoscan.esrf.mock import MockNXtomo

from nxtomomill.app.patch_nx import main


def test_patch_nx_application():
    """test nxtomomill patch-nx input_file entry --invalid-frames XX:YY"""

    with tempfile.TemporaryDirectory() as folder:
        nx_path = os.path.join(folder, "nexus_file.nx")
        dim = 55
        nproj = 20
        scan = MockNXtomo(
            scan_path=nx_path,
            n_proj=nproj,
            n_ini_proj=nproj,
            create_ini_dark=False,
            create_ini_flat=False,
            create_final_flat=False,
            dim=dim,
        ).scan
        main(
            [
                "patch-nx",
                scan.master_file,
                "entry",
                "--invalid-frames",
                "0:12",
            ]
        )
        scan.clear_cache()
        assert len(scan.projections) == 8, "Scan is expected to have 8 projections now"
