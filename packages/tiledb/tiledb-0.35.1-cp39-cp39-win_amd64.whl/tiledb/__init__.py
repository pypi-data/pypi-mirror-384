"""""" # start delvewheel patch
def _delvewheel_patch_1_11_2():
    import ctypes
    import os
    import platform
    import sys
    libs_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir, 'tiledb.libs'))
    is_conda_cpython = platform.python_implementation() == 'CPython' and (hasattr(ctypes.pythonapi, 'Anaconda_GetVersion') or 'packaged by conda-forge' in sys.version)
    if sys.version_info[:2] >= (3, 8) and not is_conda_cpython or sys.version_info[:2] >= (3, 10):
        if os.path.isdir(libs_dir):
            os.add_dll_directory(libs_dir)
    else:
        load_order_filepath = os.path.join(libs_dir, '.load-order-tiledb-0.35.1')
        if os.path.isfile(load_order_filepath):
            import ctypes.wintypes
            with open(os.path.join(libs_dir, '.load-order-tiledb-0.35.1')) as file:
                load_order = file.read().split()
            kernel32 = ctypes.WinDLL('kernel32', use_last_error=True)
            kernel32.LoadLibraryExW.restype = ctypes.wintypes.HMODULE
            kernel32.LoadLibraryExW.argtypes = ctypes.wintypes.LPCWSTR, ctypes.wintypes.HANDLE, ctypes.wintypes.DWORD
            for lib in load_order:
                lib_path = os.path.join(os.path.join(libs_dir, lib))
                if os.path.isfile(lib_path) and not kernel32.LoadLibraryExW(lib_path, None, 8):
                    raise OSError('Error loading {}; {}'.format(lib, ctypes.FormatError(ctypes.get_last_error())))


_delvewheel_patch_1_11_2()
del _delvewheel_patch_1_11_2
# end delvewheel patch

import ctypes
import os
import sys
import warnings

if os.name == "posix":
    if sys.platform == "darwin":
        lib_name = "libtiledb.dylib"
    else:
        lib_name = "libtiledb.so"
else:
    lib_name = "tiledb"

import numpy as np

# TODO: get rid of this - It is currently used for unified numpy printing accross numpy versions
np.set_printoptions(
    legacy="1.21" if np.lib.NumpyVersion(np.__version__) >= "1.22.0" else False
)
del np

from tiledb.libtiledb import version as libtiledb_version

if libtiledb_version() >= (2, 26):
    from .current_domain import CurrentDomain
    from .ndrectangle import NDRectangle

if libtiledb_version() >= (2, 28, 1):
    from .profile import Profile

del libtiledb_version  # no longer needed

from .array import Array
from .array_schema import ArraySchema
from .attribute import Attr
from .consolidation_plan import ConsolidationPlan
from .ctx import Config, Ctx, default_ctx, scope_ctx
from .dataframe_ import from_csv, from_pandas, open_dataframe
from .dense_array import DenseArrayImpl
from .dimension import Dim
from .dimension_label import DimLabel
from .dimension_label_schema import DimLabelSchema
from .domain import Domain
from .enumeration import Enumeration
from .filestore import Filestore
from .filter import (
    BitShuffleFilter,
    BitWidthReductionFilter,
    ByteShuffleFilter,
    Bzip2Filter,
    ChecksumMD5Filter,
    ChecksumSHA256Filter,
    CompressionFilter,
    DeltaFilter,
    DictionaryFilter,
    DoubleDeltaFilter,
    Filter,
    FilterList,
    FloatScaleFilter,
    GzipFilter,
    LZ4Filter,
    NoOpFilter,
    PositiveDeltaFilter,
    RleFilter,
    WebpFilter,
    XORFilter,
    ZstdFilter,
)
from .fragment import (
    FragmentInfo,
    FragmentInfoList,
    copy_fragments_to_existing_array,
    create_array_from_fragments,
)
from .group import Group
from .highlevel import (
    array_exists,
    array_fragments,
    as_built,
    consolidate,
    empty_like,
    from_numpy,
    ls,
    move,
    object_type,
    open,
    remove,
    save,
    schema_like,
    vacuum,
    walk,
)
from .libtiledb import TileDBError
from .metadata import Metadata
from .multirange_indexing import EmptyRange
from .object import Object
from .parquet_ import from_parquet
from .query import Query
from .query_condition import QueryCondition
from .schema_evolution import ArraySchemaEvolution
from .sparse_array import SparseArrayImpl
from .stats import (
    stats_disable,
    stats_dump,
    stats_enable,
    stats_reset,
)
from .subarray import Subarray
from .version_helper import version
from .vfs import VFS, FileIO

__version__ = version.version
group_create = Group.create

# Note: we use a modified namespace packaging to allow continuity of existing TileDB-Py imports.
#       Therefore, 'tiledb/__init__.py' must *only* exist in this package.
#       Furthermore, in sub-packages, the `find_packages` helper will not work at the
#       root directory due to lack of 'tiledb/__init__.py'. Sub-package 'setup.py' scripts
#       must declare constituents accordingly, such as by running 'find_packages' on a sub-directory
#       and applying prefixes accordingly.
#   1) https://packaging.python.org/guides/packaging-namespace-packages/#native-namespace-packages
#   2) https://stackoverflow.com/a/53486554
#
# Note: 'pip -e' in particular will not work without this declaration:
__path__ = __import__("pkgutil").extend_path(__path__, __name__)

# If tiledb.cloud is installed, add CloudArray methods to TileDB arrays
try:
    from tiledb.cloud.cloudarray import CloudArray
except ImportError:

    class DenseArray(DenseArrayImpl):
        pass

    class SparseArray(SparseArrayImpl):
        pass

else:

    class DenseArray(DenseArrayImpl, CloudArray):
        pass

    class SparseArray(SparseArrayImpl, CloudArray):
        pass

    del CloudArray
