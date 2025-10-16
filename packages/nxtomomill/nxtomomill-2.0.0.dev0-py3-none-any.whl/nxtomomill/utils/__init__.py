"""module with various utils like modifying image_key values, checking if and HDF5 entry looks like an NXtomo entry..."""

from .frameappender import FrameAppender  # noqa F401
from .utils import FileExtension  # noqa F401
from .utils import add_dark_flat_nx_file  # noqa F401
from .utils import change_image_key_control  # noqa F401
from .utils import embed_url  # noqa F401
from .utils import get_file_name  # noqa F401
from .utils import get_tuple_of_keys_from_cmd  # noqa F401
from .utils import is_nx_tomo_entry  # noqa F401

# expose ImageKey from nxtomo
from nxtomo.nxobject.nxdetector import ImageKey  # noqa F401
