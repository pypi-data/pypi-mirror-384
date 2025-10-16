from __future__ import annotations

import os
import shutil
import pytest
import h5py
import numpy

from nxtomo import NXtomo
from nxtomo.utils.transformation import DetXFlipTransformation, DetYFlipTransformation
from nxtomomill.models.h52nx import H52nxModel
from nxtomomill.converter.hdf5.hdf5converter import from_h5_to_nx
from nxtomomill.tests.datasets import GitlabDataset


@pytest.fixture()
def dataset_id16a(tmp_path):
    source_file = GitlabDataset.get_dataset(
        "h5_datasets/holotomo/id16a/Atomium_S2_holo4_HT_010nm_0001.h5"
    )
    return shutil.copyfile(
        source_file,
        os.path.join(tmp_path, "Atomium_S2_holo1_HT_010nm_500proj_0003.h5"),
    )


@pytest.mark.parametrize("soft_flip", ((True, False), (False, True)))
@pytest.mark.parametrize("mechanical_flip", ((False, False), (True, True)))
def test_frame_flips(tmp_path, dataset_id16a, soft_flip, mechanical_flip):
    # edit
    with h5py.File(dataset_id16a, mode="a") as h5f:
        tomo_config = h5f["1.1/technique/detector/balor"]
        del tomo_config["flipping"]
        tomo_config["flipping"] = numpy.array(soft_flip)

    output_file = os.path.join(tmp_path, "my_nx.nx")
    assert not os.path.exists(output_file)

    # convert
    model = H52nxModel(
        input_file=dataset_id16a,
        output_file=output_file,
        mechanical_lr_flip=mechanical_flip[0],
        mechanical_ud_flip=mechanical_flip[1],
        single_file=True,
    )

    # check transformations matrix
    from_h5_to_nx(configuration=model)

    assert os.path.exists(output_file)

    nxtomo = NXtomo().load(file_path=output_file, data_path="entry0000")
    transformations = nxtomo.instrument.detector.transformations.transformations

    final_lr_flip = soft_flip[0] ^ mechanical_flip[0]
    final_ud_flip = soft_flip[1] ^ mechanical_flip[1]

    lr_flip_mat = DetXFlipTransformation(flip=final_ud_flip)
    ud_flip_mat = DetYFlipTransformation(flip=final_lr_flip)

    assert lr_flip_mat in transformations
    assert ud_flip_mat in transformations
