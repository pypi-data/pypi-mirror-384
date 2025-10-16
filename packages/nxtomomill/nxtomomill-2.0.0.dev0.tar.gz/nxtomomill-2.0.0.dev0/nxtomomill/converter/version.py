"""module to get NXtomo versionning as it can evolve with time"""

LATEST_VERSION = 1.2

CURRENT_OUTPUT_VERSION = LATEST_VERSION


def version():
    return CURRENT_OUTPUT_VERSION


# Information regarding Format
# Format 1.0
#    NXtomo entry (one per acquisition)
#       |-> beam
#             |-> incident energy (optional 0D)
#       |-> instrument (NXinstrument)
#             |-> detector (NXdetector)
#                  |-> count_time (optional 1D dataset)
#                  |-> data (mandatory 3D dataset)
#                  |-> distance (optional 0D dataset)
#                  |-> field_of_fiew (optional str)
#                  |-> image_key (madatory 1D dataset)
#                  |-> image_key_control (optional 1D dataset)
#                  |-> x_pixel_size (float)
#                  |-> y_pixel_size (float)
#       |-> sample (NXsample)
#             |-> name (optional)
#             |-> rotation_angle - mandatory (1D dataset in degree)
#             |-> x_translation - optional (1D dataset)
#             |-> y_translation - optional (1D dataset)
#             |-> z_translation - optional (1D dataset)
#
# Format 1.1:
#    * move beam to the NXinstrument
#       * Keep compatibility by providing a link to beam at the root level
#    * add optional dataset instrument/name
#    * sample/name is moved to title
#    * sample/sample_name is moved to sample/name
#    * add NXsource under instrument:
#       |-> instrument (NXinstrument)
#              |-> source (optional NXsource)
#                   |-> name (optional)
#                   |-> type (optional)
