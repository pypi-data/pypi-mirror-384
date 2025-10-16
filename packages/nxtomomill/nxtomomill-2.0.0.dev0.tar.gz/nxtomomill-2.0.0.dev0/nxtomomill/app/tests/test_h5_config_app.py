# coding: utf-8

import os
import tempfile

from nxtomomill.app.h5config import main


def test_h5_config_application():
    """test nxtomomill h5-config output_file"""

    with tempfile.TemporaryDirectory() as folder:
        output_file = os.path.join(folder, "config.cfg")
        assert not os.path.exists(output_file)
        main(["h5-config", output_file])
        assert os.path.exists(output_file)
