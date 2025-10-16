import logging
from posixpath import join
import numpy as np
import pint
from tomoscan.esrf.scan.h5utils import get_h5_value
from nxtomo.application.nxtomo import NXtomo
from nxtomo.nxobject.nxdetector import ImageKey
from tomoscan.esrf.scan.fscan import FscanDataset, list_datasets
from silx.utils.deprecation import deprecated

_logger = logging.getLogger(__name__)
_ureg = pint.get_application_registry()


__all__ = [
    "from_fscan_to_nx",
]


@deprecated(reason="Removed as unused", since_version="2.0")
def from_fscan_to_nx(
    fname,
    output_fname,
    detector_name="pcoedgehs",
    rotation_motor_name="hrrz",
    halftomo=False,
    ignore_last_n_projections=0,
    energy=None,
    distance=None,
):
    entries = list_datasets(fname)
    if len(entries) < 3:
        _logger.error(
            "Error: Expected at least three datasets, got only %d" % (len(entries))
        )
        return
    do_360 = False
    if len(entries) == 6:
        # 360 degrees scans are done in two parts: [1.1, 2.1, 3.1] and then [4.1, 5.1]
        do_360 = True

    projs = FscanDataset(fname, detector_name=detector_name, entry="1.1")
    flats = FscanDataset(fname, detector_name=detector_name, entry="2.1")
    darks = FscanDataset(fname, detector_name=detector_name, entry="3.1")
    if do_360:
        projs2 = FscanDataset(fname, detector_name=detector_name, entry="4.1")
        flats2 = FscanDataset(fname, detector_name=detector_name, entry="5.1")
        # Some datasets don't have the 6.1 entry.
        # Anyway nabu does not support several series of darks.
        # For now it's safer to ignore the second series of darks
        try:
            darks2 = FscanDataset(fname, detector_name=detector_name, entry="6.1")
        except ValueError:
            _logger.error("Could not find entry 6.1, proceeding")
            darks2 = None
        if darks2 is not None:
            _logger.warning(
                "Discarding entry 6.1 as nabu does not support several series of darks yet"
            )

    my_nxtomo = NXtomo()

    data_urls = [darks.dataset_hdf5_url, flats.dataset_hdf5_url, projs.dataset_hdf5_url]
    if do_360:
        data_urls.extend(
            [
                # darks2.dataset_hdf5_url,
                flats2.dataset_hdf5_url,
                projs2.dataset_hdf5_url,
            ]
        )
    my_nxtomo.instrument.detector.data = data_urls

    img_keys = [
        [ImageKey.DARK_FIELD] * darks.data_shape[0],
        [ImageKey.FLAT_FIELD] * flats.data_shape[0],
        [ImageKey.PROJECTION] * (projs.data_shape[0] - ignore_last_n_projections),
        [ImageKey.ALIGNMENT] * ignore_last_n_projections,
    ]
    if do_360:
        img_keys.extend(
            [
                # [ImageKey.DARK_FIELD] * darks2.data_shape[0],
                [ImageKey.FLAT_FIELD] * flats2.data_shape[0],
                [ImageKey.PROJECTION]
                * (projs2.data_shape[0] - ignore_last_n_projections),
                [ImageKey.ALIGNMENT] * ignore_last_n_projections,
            ]
        )

    my_nxtomo.instrument.detector.image_key_control = np.concatenate(img_keys)

    rotation_angles_path = join(projs.entry, f"instrument/{rotation_motor_name}/data")
    rotation_angles = get_h5_value(projs.fname, rotation_angles_path)
    # Sometimes values are in /data, sometimes in /value ... who needs a stable format anyway ?
    if rotation_angles is None:
        _logger.error(
            f"Could not find the rotation angles in {rotation_angles_path}, trying in /values"
        )
    rotation_angles_path = rotation_angles_path.replace("/data", "/value")
    # ---
    rotation_angles = get_h5_value(projs.fname, rotation_angles_path)
    if rotation_angles is not None:
        last_idx = None
        if ignore_last_n_projections > 0:
            last_idx = -ignore_last_n_projections
        rotation_angles = [
            [0] * darks.data_shape[0],
            [0] * flats.data_shape[0],
            rotation_angles[:last_idx],
            [0] * ignore_last_n_projections,
        ]
        if do_360:
            rotation_angles2 = get_h5_value(
                projs2.fname,
                join(projs2.entry, f"instrument/{rotation_motor_name}/data"),
            )
            rotation_angles.extend(
                [
                    # [0] * darks2.data_shape[0],
                    [0] * flats2.data_shape[0],
                    rotation_angles2[:last_idx],
                    [0] * ignore_last_n_projections,
                ]
            )
        my_nxtomo.sample.rotation_angle = np.concatenate(rotation_angles) * _ureg.degree

    my_nxtomo.instrument.detector.field_of_view = (
        "Half" if (halftomo and do_360) else "Full"
    )
    my_nxtomo.instrument.detector.x_pixel_size = (
        my_nxtomo.instrument.detector.y_pixel_size
    ) = (6.5 * 1e-6)

    n_frames = len(my_nxtomo.sample.rotation_angle)
    my_nxtomo.instrument.detector.sequence_number = np.linspace(
        start=0, stop=n_frames, num=n_frames, dtype=np.uint32, endpoint=False
    )

    if energy is not None:
        my_nxtomo.energy = energy  # in keV by default
    if distance is not None:
        my_nxtomo.instrument.detector.distance = distance  # in meter

    my_nxtomo.save(
        file_path=output_fname,
        data_path="entry",
        overwrite=True,
        nexus_path_version=1.1,
    )
