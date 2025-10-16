import datetime

import pytest
from tomoscan.io import HDF5File
from tomoscan.esrf.scan.nxtomoscan import NXtomoScan

from nxtomomill.app.zstages2nxs import _convert_bliss2nx
from nxtomomill.tests.utils.bliss import MockBlissAcquisition as _MockBlissAcquisition
from nxtomomill.utils.flat_reducer import flat_reducer


class MockBlissAcquisition(_MockBlissAcquisition):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for sample in self.samples:
            # append machine current to the scan
            with HDF5File(sample.sample_file, mode="a") as h5f:
                for i_bliss_scan in range(
                    1, 1 + self._n_scan_per_sequence + self._n_darks + self._n_flats
                ):
                    node_name = f"{i_bliss_scan}.1"
                    h5f[f"{node_name}/instrument/machine/current"] = [
                        12.3,
                    ]
                    h5f[f"{node_name}/instrument/machine/current"].attrs["units"] = "mA"
                    if f"{node_name}/start_time" in h5f:
                        del h5f[f"{node_name}/start_time"]
                    h5f[f"{node_name}/start_time"] = str(datetime.datetime.now())
                    if f"{node_name}/end_time" in h5f:
                        del h5f[f"{node_name}/end_time"]
                    h5f[f"{node_name}/end_time"] = str(
                        datetime.datetime.now() + datetime.timedelta(minutes=10)
                    )


@pytest.mark.parametrize("stage_scan_have_flats", (True, False))
@pytest.mark.parametrize("save_intermediated", (True, False))
@pytest.mark.parametrize("reuse_intermediated", (True, False))
def test_flat_reducer(
    tmp_path, stage_scan_have_flats, save_intermediated, reuse_intermediated
):
    """
    test execution of `flat_reducer` function.
    This function is going through a set of bliss acquisition to create corresponding NXtomo and add them dark and flats obtained from
    'reference' acquisition (converting projections to reduced flats)
    """
    raw_data_dir = tmp_path / "raw"
    n_stage = 5
    # create bliss scan to be converted to NXtomo
    acqu = MockBlissAcquisition(
        n_sample=n_stage,
        n_sequence=1,
        n_scan_per_sequence=10,
        n_darks=2,
        n_flats=1 if stage_scan_have_flats else 0,
        output_dir=raw_data_dir,
        file_name_z_fill=4,
    )
    stages_bliss_file = [sample.sample_file for sample in acqu.samples]

    # scan for flat at start
    ref_start = MockBlissAcquisition(
        n_sample=1,
        n_sequence=1,
        n_scan_per_sequence=10,
        n_darks=2,
        n_flats=0,
        output_dir=raw_data_dir,
        file_name_prefix="REF_B_0000",
    )
    bliss_ref_start = ref_start.samples[0].sample_file
    nx_tomo_ref_start = bliss_ref_start.replace(".h5", ".nx")
    _convert_bliss2nx(
        bliss_ref_start,
        nx_tomo_ref_start,
    )
    # scan for flat at end
    ref_end = MockBlissAcquisition(
        n_sample=1,
        n_sequence=1,
        n_scan_per_sequence=10,
        n_darks=2,
        n_flats=0,
        output_dir=raw_data_dir,
        file_name_prefix="REF_E_0000",
    )
    bliss_ref_end = ref_end.samples[0].sample_file
    nx_tomo_ref_end = bliss_ref_end.replace(".h5", ".nx")
    _convert_bliss2nx(
        bliss_ref_end,
        nx_tomo_ref_end,
    )

    for i_stage, bliss_file_name in enumerate(stages_bliss_file):
        mixing_factor = (i_stage + 1) / (n_stage)

        # convert from .h5 to .nx
        output_nx_file = bliss_file_name.replace(".h5", ".nx")
        _convert_bliss2nx(
            bliss_file_name,
            output_nx_file,
        )

        # apply fly reducer
        flat_reducer(
            scan_filename=output_nx_file,
            ref_start_filename=nx_tomo_ref_start,
            ref_end_filename=nx_tomo_ref_end,
            mixing_factor=mixing_factor,
            save_intermediated=save_intermediated,
            reuse_intermediated=reuse_intermediated,
        )
        # make sure there is some reduced dark and flat for the nx

        i_stage_scan = NXtomoScan(output_nx_file, "entry0000")
        i_stage_reduced_flats = i_stage_scan.load_reduced_flats()
        i_stage_reduced_darks = i_stage_scan.load_reduced_darks()
        assert len(i_stage_reduced_flats) == 1
        assert len(i_stage_reduced_darks) == 1
