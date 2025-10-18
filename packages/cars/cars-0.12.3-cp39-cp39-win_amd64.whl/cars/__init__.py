#!/usr/bin/env python
# coding: utf8
#
# Copyright (c) 2020 Centre National d'Etudes Spatiales (CNES).
#
# This file is part of CARS
# (see https://github.com/CNES/cars).
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
"""
Cars module init file
"""


# start delvewheel patch
def _delvewheel_patch_1_11_2():
    import ctypes
    import os
    import platform
    import sys
    libs_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir, 'cars.libs'))
    is_conda_cpython = platform.python_implementation() == 'CPython' and (hasattr(ctypes.pythonapi, 'Anaconda_GetVersion') or 'packaged by conda-forge' in sys.version)
    if sys.version_info[:2] >= (3, 8) and not is_conda_cpython or sys.version_info[:2] >= (3, 10):
        if os.path.isdir(libs_dir):
            os.add_dll_directory(libs_dir)
    else:
        load_order_filepath = os.path.join(libs_dir, '.load-order-cars-0.12.3')
        if os.path.isfile(load_order_filepath):
            import ctypes.wintypes
            with open(os.path.join(libs_dir, '.load-order-cars-0.12.3')) as file:
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

import os
import sys
from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("cars")
except PackageNotFoundError:
    # package is not installed
    __version__ = "unknown"

# Standard imports
if sys.version_info < (3, 10):
    from importlib_metadata import entry_points
else:
    from importlib.metadata import entry_points


__author__ = "CNES"
__email__ = "cars@cnes.fr"

# Force the use of CARS dask configuration
dask_config_path = os.path.join(
    os.path.dirname(__file__), "orchestrator", "cluster", "dask_config"
)
if not os.path.isdir(dask_config_path):
    raise NotADirectoryError("Wrong dask config path")
os.environ["DASK_CONFIG"] = str(dask_config_path)

# Force monothread for child workers
os.environ["PANDORA_NUMBA_PARALLEL"] = str(False)
os.environ["PANDORA_NUMBA_CACHE"] = str(False)
os.environ["SHARELOC_NUMBA_PARALLEL"] = str(False)
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"
os.environ["GDAL_NUM_THREADS"] = "1"

# Limit GDAL cache per worker to 500MB
os.environ["GDAL_CACHEMAX"] = "500"


def import_plugins() -> None:
    """
    Load all the registered entry points
    :return: None
    """
    for entry_point in entry_points(group="cars.plugins"):
        entry_point.load()


import_plugins()
