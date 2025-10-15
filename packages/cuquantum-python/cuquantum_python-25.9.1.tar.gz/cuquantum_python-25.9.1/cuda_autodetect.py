# Copyright (c) 2023, NVIDIA CORPORATION & AFFILIATES
#
# SPDX-License-Identifier: BSD-3-Clause
#
# =============================================================================
#
# Heavily influenced by https://github.com/cupy/cupy/blob/main/install/universal_pkg/setup.py.
# See also the discussion and refs in https://github.com/NVIDIA/cuda-python/issues/16.
# Below is the original copyright notice from cupy-wheel setup.py.
#
# Copyright (c) 2015-2023 Preferred Networks, Inc.
#
# SPDX-License-Identifier: MIT
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
# 
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

import ctypes
import pkg_resources
import os
import sys
from typing import Dict, List, Optional

try:
    from wheel.bdist_wheel import bdist_wheel as _bdist_wheel
except ImportError:
    _bdist_wheel = None


# This script is a general utility script, the variables below are to be set by
# the caller
PACKAGE_NAME = ''
PACKAGE_SUPPORTED_CUDA_VER = []

# ========================================================================

PACKAGE_RESOLUTION = None
CUDA_RESOLUTION = None


class AutoDetectionFailed(Exception):
    def __str__(self) -> str:
        return f'''
\n\n============================================================
{super().__str__()}
============================================================\n
'''


def _log(msg: str) -> None:
    sys.stdout.write(f'[{PACKAGE_NAME}] {msg}\n')
    sys.stdout.flush()


def _get_version_from_library(
        libnames: List[str],
        funcname: str,
        nvrtc: bool = False,
) -> Optional[int]:
    """Returns the library version from list of candidate libraries."""

    for libname in libnames:
        try:
            _log(f'Looking for library: {libname}')
            runtime_so = ctypes.CDLL(libname)
            break
        except Exception as e:
            _log(f'Failed to open {libname}: {e}')
    else:
        _log('No more candidate library to find')
        return None

    func = getattr(runtime_so, funcname, None)
    if func is None:
        raise AutoDetectionFailed(
            f'{libname}: {func} could not be found')
    func.restype = ctypes.c_int

    if nvrtc:
        # nvrtcVersion
        func.argtypes = [
            ctypes.POINTER(ctypes.c_int),
            ctypes.POINTER(ctypes.c_int),
        ]
        major = ctypes.c_int()
        minor = ctypes.c_int()
        retval = func(major, minor)
        version = major.value * 1000 + minor.value * 10
    else:
        # cudaRuntimeGetVersion
        func.argtypes = [
            ctypes.POINTER(ctypes.c_int),
        ]
        version_ref = ctypes.c_int()
        retval = func(version_ref)
        version = version_ref.value

    if retval != 0:  # NVRTC_SUCCESS or cudaSuccess
        raise AutoDetectionFailed(
            f'{libname}: {func} returned error: {retval}')
    _log(f'Detected version: {version}')
    return version


def _get_cuda_version() -> Optional[int]:
    """Returns the detected CUDA version or None."""

    version = None

    # First try NVRTC
    libnames = [
        'libnvrtc.so.13',
        'libnvrtc.so.12',
        'libnvrtc.so.11.2',
        'libnvrtc.so.11.1',
        'libnvrtc.so.11.0',
    ]
    _log(f'Trying to detect CUDA version from libraries: {libnames}')
    try:
        version = _get_version_from_library(libnames, 'nvrtcVersion', True)
    except Exception as e:
        _log(f"Error: {e}")  # log and move on
    if version is not None:
        return version

    # Next try CUDART
    libnames = [
        'libcudart.so.13',
        'libcudart.so.12',
        'libcudart.so.11.0',  # side-effect: a CUDA context would be initialized
    ]
    _log(f'Trying to detect CUDA version from libraries: {libnames}')
    try:
        version = _get_version_from_library(libnames, 'cudaRuntimeGetVersion', False)
    except Exception as e:
        _log(f"Error: {e}")  # log and move on
    if version is not None:
        return version

    _log("Autodetection failed")
    return None


def _find_installed_packages() -> List[str]:
    """Returns the list of out packages installed in the environment."""

    f = lambda x: ''.join([f"{PACKAGE_NAME}-cu", x])
    found = []

    for pkg in list(map(f, PACKAGE_SUPPORTED_CUDA_VER)):
        try:
            pkg_resources.get_distribution(pkg)
            found.append(pkg)
        except pkg_resources.DistributionNotFound:
            pass
    return found


def _cuda_version_to_package(ver: int) -> str:
    # TODO: Don't hard-code 11/12, use PACKAGE_SUPPORTED_CUDA_VER instead?
    if ver < 11000:
        raise AutoDetectionFailed(
            f'Your CUDA version ({ver}) is too old.')
    elif ver < 12000:
        # CUDA 11.x
        raise RuntimeError(f'CUDA 11.x is not supported. Please install CUDA 12.x or later.')
    elif ver < 13000:
        # CUDA 12.x
        suffix = '12'
    elif ver < 14000:
        # CUDA 13.x
        suffix = '13'
    else:
        raise AutoDetectionFailed(
            f'Your CUDA version ({ver}) is too new.')
    return f'{PACKAGE_NAME}-cu{suffix}'


# ========================================================================

# "Public" API to the caller
def infer_best_package(package_name: str,
                       package_supported_cuda_ver: List[str] = ['12', '13']) -> str:
    """Returns the appropriate wheel name for the environment."""

    global PACKAGE_NAME, PACKAGE_SUPPORTED_CUDA_VER
    PACKAGE_NAME = package_name
    PACKAGE_SUPPORTED_CUDA_VER = sorted(package_supported_cuda_ver)

    # Find the existing wheel installation
    installed = _find_installed_packages()

    # Detect CUDA version
    version = _get_cuda_version()
    if version is not None:
        to_install = _cuda_version_to_package(version)
    else:
        # TODO: change this in the future
        message = (
            "See below for the error message and instruction.\n\n\n" +
            "************************************************************************\n" +
            "ERROR: Unable to detect NVIDIA CUDA Toolkit installation.\n" +
            "ERROR: If CUDA Toolkit is not installed, please install it first.\n" + 
            "ERROR: If CUDA Toolkit is installed but not detected, please explicitly specify the version and run\n" +
            f"ERROR: `pip install {PACKAGE_NAME}-cuXX`, with XX being the major\n" +
            "ERROR: version of your CUDA Toolkit installation.\n" +
            "************************************************************************\n\n"
        )
        raise AutoDetectionFailed(message)

    # Disallow -cu12 & -cu13 wheels from coexisting
    if len(installed) > 1 or (len(installed) == 1 and installed[0] != to_install):
        raise AutoDetectionFailed(
            f'You already have the {PACKAGE_NAME} package(s) installed: \n'
            f'  {installed}\n'
            'while you attempt to install:\n'
            f'  {to_install}\n'
            'Please uninstall all of them first, then try reinstalling.')

    global PACKAGE_RESOLUTION, CUDA_RESOLUTION
    PACKAGE_RESOLUTION = to_install
    CUDA_RESOLUTION = version
    _log(f"Installing {to_install}...")
    return to_install


# "Public" API to the caller
if _bdist_wheel is not None:

    # Technically we need a way to force reinstalling the sdist and ignored the cached wheel.
    # That said, I cannot reproduce the past-known behavior in my env. The sdist is always
    # reinstalled, though it could be due to certain combination of pip/setuptools/wheel/etc,
    # and it's still better to keep this WAR.

    class bdist_wheel(_bdist_wheel):

        # Adopted from https://discuss.python.org/t/wheel-caching-and-non-deterministic-builds/7687

        def finalize_options(self):
            super().finalize_options()

            # Use "cuXX" as the build tag to force re-running sdist if the
            # CUDA version in the user env has changed
            if PACKAGE_RESOLUTION is None:
                assert False, "something went wrong"
            build_tag = PACKAGE_RESOLUTION.split("-")[-1]

            # per PEP 427, build tag must start with a digit
            self.build_number = f"0_{build_tag}"

else:

    bdist_wheel = None
