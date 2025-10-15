"""Python bindings for the libeismultiplexer library.

This package provides a thin wrapper around the native ``libeismultiplexer`` C
library, exposing a :class:`Multiplexer` class and several enumerations that
represent channels, trigger states and wait types.  The underlying C library is
loaded via ``ctypes`` and the high‑level API is implemented in C++ using
``pybind11`` (see :mod:`_core`).

Typical usage::

    from libeismultiplexer import Multiplexer, Channel, TriggerState

    mux = Multiplexer(serial=0)
    mux.connectChannel(Channel.A)
    mux.setTriggerState(0, TriggerState.HIGH)

The module ensures that the required ``libusb-1.0`` shared library is present
on the system before importing the compiled extension.
"""

import ctypes
import os
import libusb_package

# Resolve the path to the libusb shared library provided by the ``libusb_package``
# helper.  ``libusb_package.get_library_path()`` returns the absolute path to the
# library file.  We load it with ``ctypes`` so that the C++ bindings can locate
# the symbols at runtime.
_libusb_path = libusb_package.get_library_path()
if not os.path.exists(_libusb_path):
    raise FileNotFoundError(
        "libusb-1.0.so was not found on your system. Is the libusb package correctly installed?"
    )
# ``LoadLibrary`` will raise an ``OSError`` if the library cannot be loaded due
# to missing dependencies.
_ctypes_lib = ctypes.cdll.LoadLibrary(_libusb_path)

# Export the public API from the compiled ``_core`` module.
from ._core import __version__, Multiplexer, Channel, TriggerState, TriggerWaitType

__all__ = ["__version__", "Multiplexer", "Channel", "TriggerState", "TriggerWaitType"]
