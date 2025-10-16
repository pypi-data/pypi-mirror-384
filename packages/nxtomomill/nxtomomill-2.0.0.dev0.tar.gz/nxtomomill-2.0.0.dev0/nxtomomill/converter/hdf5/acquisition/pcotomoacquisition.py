from .multitomo import MultiTomoAcquisition
from nxtomomill.utils.io import deprecated_warning


class PCOTomoAcquisition(MultiTomoAcquisition):
    def __init__(self, root_url, configuration, detector_sel_callback, start_index):
        deprecated_warning(
            type_="class",
            name=PCOTomoAcquisition,
            reason="rename PCOTomoAcquisition to MultiTomoAcquisition",
            replacement="nxtomomill.converter.hdf5.acquisition.multitomo.MultiTomoAcquisition",
            since_version="1.2",
        )
        super().__init__(root_url, configuration, detector_sel_callback, start_index)
