# coding: utf-8

"""
Module to convert from (Bliss) .h5 to (Nexus Tomo-compliant) .nx format.
"""


class Tomo:
    class H5:
        """HDF5 settings for tomography"""

        VALID_CAMERA_NAMES: tuple[str, ...] = tuple()
        # Camera names are now deduced using the `get_nx_detectors` and
        # `guess_nx_detector` functions. Alternatively, a list of detector
        # names can be provided (supports Unix shell-style wildcards), such as:
        # ("pcolinux*", "basler", "frelon*", ...)

        ROT_ANGLE_KEYS = (
            "rotm",
            "mhsrot",
            "hsrot",
            "mrsrot",
            "hrsrot",
            "srot",
            "srot_eh2",
            "diffrz",
            "hrrz_trig",
            "rot",
        )
        """Keys used to find rotation angles."""

        TRANSLATION_Y_KEYS = ("yrot", "diffty", "hry")
        """Keys used to find the Y translation below the center of rotation."""

        TRANSLATION_Z_KEYS = ("sz", "difftz", "hrz", "pz", "ntz", "samtz", "mrsz")
        """Keys used to find the Z translation below or above the center of rotation."""

        SAMPLE_X_KEYS = ("samx", "psx", "sax", "fake_sx")
        """Keys used to find the X translation above the center of rotation (direction is independent of the rotation angle)."""

        SAMPLE_Y_KEYS = ("samy", "psv", "say", "fake_sy")
        """Keys used to find the Y translation above the center of rotation (direction is independent of the rotation angle)."""

        SAMPLE_U_KEYS = ("sau", "sx", "px", "ntx", "shtx", "hrx", "fake_su")
        """Keys used to find the U translation above the center of rotation (direction is dependent of the rotation angle)."""

        SAMPLE_V_KEYS = ("sav", "sy", "py", "nty", "shty", "hry2", "fake_sv")
        """Keys used to find the V translation above the center of rotation (direction is dependent of the rotation angle)."""

        DIODE_KEYS = ("fpico3",)
        """Keys used to store diode dataset."""

        ACQ_EXPO_TIME_KEYS = ("acq_expo_time",)
        """Keys used to store acquisition exposure time."""

        INIT_TITLES = (
            "tomo:basic",
            "tomo:fullturn",
            "sequence_of_scans",
            "tomo:halfturn",
            "tomo:multiturn",
            "tomo:helical",
            "tomo:holotomo",
        )
        """Initialization scan titles."""

        ZSERIE_INIT_TITLES = ("tomo:zseries",)
        """Specific titles for z-series scans."""

        MULTITOMO_INIT_TITLES = (
            "tomo:pcotomo",
            "pcotomo",
            "tomo:multitomo",
            "multitomo",
            "multitomo:basic",
            "tomo:multiturn",
            "multiturn",
        )
        """Specific titles for multi-tomo scans (also known as PCO scans)."""

        PCOTOMO_INIT_TITLES = MULTITOMO_INIT_TITLES
        """Deprecated. Replaced by 'MULTITOMO_INIT_TITLES'"""

        BACK_AND_FORTH_INIT_TITLES = (
            "tomo:backandforth",
            "backandforthtomo:basic",
            "backandforth",
            "tomo:back_and_forth",
            "back_and_forth",
        )
        """Specific titles for back and forth scans."""

        DARK_TITLES = ("dark images", "dark")
        """Titles for dark scans."""

        FLAT_TITLES = ("flat", "reference images", "ref", "refend")
        """Titles for reference scans (flat field images)."""

        PROJ_TITLES = ("projections", "ascan rot 0", "ascan diffrz 0 180 1600 0.1")
        """Titles for projection scans."""

        ALIGNMENT_TITLES = ("static images", "ascan diffrz 180 0 4 0.1")
        """Titles for alignment scans."""

        SAMPLE_X_PIXEL_SIZE_KEYS = ("technique/optic/sample_pixel_size",)
        """Possible paths to the pixel size along the x-axis."""

        SAMPLE_Y_PIXEL_SIZE_KEYS = ("technique/optic/sample_pixel_size",)
        """Possible paths to the pixel size along the y-axis."""

        DETECTOR_X_PIXEL_SIZE_KEYS = (
            "technique/optic/optics_pixel_size",
            "technique/scan/detector_pixel_size",
            "technique/detector/{detector_name}/pixel_size",
            "technique/detector/pixel_size",
        )

        DETECTOR_Y_PIXEL_SIZE_KEYS = (
            "technique/optic/optics_pixel_size",
            "technique/scan/detector_pixel_size",
            "technique/detector/{detector_name}/pixel_size",
            "technique/detector/pixel_size",
        )

        SAMPLE_DETECTOR_DISTANCE_KEYS = ("technique/scan/sample_detector_distance",)
        """Keys used to store the sample to detector distance."""

        SOURCE_SAMPLE_DISTANCE_KEYS = ("technique/scan/source_sample_distance",)
        """Keys used to store the source to sample distance."""

        MACHINE_CURRENT_KEYS = ("current",)
        """Keys used to store machine current values."""

    class EDF:
        """EDF settings for tomography"""

        MOTOR_POS = ("motor_pos",)
        """Keys for motor positions."""

        MOTOR_MNE = ("motor_mne",)
        """Keys for motor names (mnemonics)."""

        ROT_ANGLE = ("srot", "somega")
        """Keys used to find the rotation angle."""

        X_TRANS = ("sx",)
        """Keys used to find x translation in EDF format."""

        Y_TRANS = ("sy",)
        """Keys used to find y translation in EDF format."""

        Z_TRANS = ("sz",)
        """Keys used to find z translation in EDF format."""

        MACHINE_CURRENT = ("srcur", "srcurrent")
        """Keys used to store machine current values."""

        TO_IGNORE = ("_slice_",)
        """Fields to ignore when processing EDF files."""

        DARK_NAMES = ("darkend", "dark")
        """Names identifying dark images in EDF files."""

        REFS_NAMES = ("ref", "refHST")
        """Names identifying reference images in EDF files."""
