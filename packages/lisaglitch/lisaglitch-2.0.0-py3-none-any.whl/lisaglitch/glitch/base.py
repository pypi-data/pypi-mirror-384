#! /usr/bin/env python3
# -*- coding: utf-8 -*-
#
# BSD 3-Clause License
#
# Copyright 2022, by the California Institute of Technology.
# ALL RIGHTS RESERVED. United States Government Sponsorship acknowledged.
# Any commercial use must be negotiated with the Office of Technology Transfer
# at the California Institute of Technology.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# 1. Redistributions of source code must retain the above copyright notice, this
#    list of conditions and the following disclaimer.
#
# 2. Redistributions in binary form must reproduce the above copyright notice,
#    this list of conditions and the following disclaimer in the documentation
#    and/or other materials provided with the distribution.
#
# 3. Neither the name of the copyright holder nor the names of its
#    contributors may be used to endorse or promote products derived from
#    this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
# FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
# OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#
# This software may be subject to U.S. export control laws. By accepting this
# software, the user agrees to comply with all applicable U.S. export laws and
# regulations. User has the responsibility to obtain export licenses, or other
# export authority as may be required before exporting such information to
# foreign countries or providing access to foreign persons.
#
"""
Base class for glitches

All glitch classes inherit from this base class.

Authors:
    Jean-Baptiste Bayle <j2b.bayle@gmail.com>
    Eleonora Castelli <eleonora.castelli@unitn.it>
"""

import abc
import importlib
import logging
from typing import Optional, Tuple

import h5py
import matplotlib.pyplot as plt
import numpy as np

logger = logging.getLogger(__name__)

INJECTION_POINTS = [
    # Test-mass motion
    "tm_12",
    "tm_23",
    "tm_31",
    "tm_13",
    "tm_32",
    "tm_21",
    # Laser frequency jumps
    "laser_12",
    "laser_23",
    "laser_31",
    "laser_13",
    "laser_32",
    "laser_21",
    # Readout of carrier inter-spacecraft interferometers
    "readout_isi_carrier_12",
    "readout_isi_carrier_23",
    "readout_isi_carrier_31",
    "readout_isi_carrier_13",
    "readout_isi_carrier_32",
    "readout_isi_carrier_21",
    # Readout of upper sideband inter-spacecraft interferometers
    "readout_isi_usb_12",
    "readout_isi_usb_23",
    "readout_isi_usb_31",
    "readout_isi_usb_13",
    "readout_isi_usb_32",
    "readout_isi_usb_21",
    # Readout of carrier test-mass interferometers
    "readout_tmi_carrier_12",
    "readout_tmi_carrier_23",
    "readout_tmi_carrier_31",
    "readout_tmi_carrier_13",
    "readout_tmi_carrier_32",
    "readout_tmi_carrier_21",
    # Readout of upper sideband test-mass interferometers
    "readout_tmi_usb_12",
    "readout_tmi_usb_23",
    "readout_tmi_usb_31",
    "readout_tmi_usb_13",
    "readout_tmi_usb_32",
    "readout_tmi_usb_21",
    # Readout of carrier reference interferometers
    "readout_rfi_carrier_12",
    "readout_rfi_carrier_23",
    "readout_rfi_carrier_31",
    "readout_rfi_carrier_13",
    "readout_rfi_carrier_32",
    "readout_rfi_carrier_21",
    # Readout of upper sideband reference interferometers
    "readout_rfi_usb_12",
    "readout_rfi_usb_23",
    "readout_rfi_usb_31",
    "readout_rfi_usb_13",
    "readout_rfi_usb_32",
    "readout_rfi_usb_21",
]


class Glitch(abc.ABC):
    """Abstract base class to represent a single glitch signal.

    A glitch is a time-domain signal which is injected into the instrumental
    simulation at a given injection point and at a given time This abstract
    class provides a common structure for all glitch classes.

    .. admonition:: Units and time coordinates

        The physical unit and time coordinate associated with a glitch are
        defined by the associated injection point.

    Args:
        inj_point (str): injection point, see
            :const:`lisaglitch.INJECTION_POINTS` for a list of valid injection
            points
        t_inj (float): injection time [s]
    """

    def __init__(self, inj_point, t_inj=0) -> None:

        self.git_url = "https://gitlab.in2p3.fr/lisa-simulation/glitch"
        self.generator = self.__class__.__name__
        self.version = importlib.metadata.version("lisaglitch")
        logger.info("Initializing glitch (lisaglitch version %s)", self.version)

        if inj_point not in INJECTION_POINTS:
            raise ValueError(f"Invalid injection point '{inj_point}'")
        self.inj_point = inj_point  #: Injection point.
        self.t_inj = float(t_inj)  #: Injection time [s].

    @abc.abstractmethod
    def compute_signal(self, t) -> np.ndarray:
        """Compute the glitch time-domain signal.

        The time is expressed in the local coordinates of the injection. E.g.,
        glitches injected in the test-mass onboard spacecraft 1 are expressed in
        the spacecraft proper time (TPS) of spacecraft 1.

        If ``t`` is None, we use the default sampling parameters of the glitch
        object.

        Args:
            t ((N,) array-like): time [s]

        Return:
            Time-domain glitch signal, of shape (N,).
        """
        raise NotImplementedError

    def plot(self, t, output=None, title="Glitch signal") -> None:
        """Plot glitch signal.

        Args:
            t ((N,) array-like): time [s]
            output (str or None): output file, None to show the plots
            title (str): plot title
        """
        # Compute glitch signal
        logger.info("Computing glitch signal")
        signal = self.compute_signal(t)
        # Create a new figure for this plot
        plt.figure(figsize=(10, 6))
        # Plot glitch
        logger.info("Plotting glitch signal")
        plt.plot(t, signal)
        plt.xlabel("Time [s]")
        plt.ylabel("Signal")
        plt.title(title)
        plt.grid(True, alpha=0.3)
        # Save or show glitch
        if output is not None:
            logger.info("Saving plot to %s", output)
            plt.savefig(output, bbox_inches="tight", dpi=150)
            plt.close()  # Close the figure to free memory
        else:
            plt.show()

    def _write_metadata(self, hdf5, prefix=""):
        """Set all properties as HDF5 attributes on ``object``.

        Try to store all variables as attributes. If it is too large or its type
        is not supported, try to store a string representation; if this fails,
        log a warning.

        Args:
            hdf5 (h5py.File): an HDF5 file, or a dataset
            prefix (str): prefix for attribute names
        """
        for key, value in self.__dict__.items():
            pkey = f"{prefix}{key}"
            try:
                hdf5.attrs[pkey] = value
            except (TypeError, RuntimeError):
                try:
                    hdf5.attrs[pkey] = str(value)
                except RuntimeError:
                    logger.warning("Cannot write metadata '%s' on '%s'", pkey, hdf5)

    @staticmethod
    def read_file_sampling(path: str) -> Optional[Tuple[float, int, float]]:
        """Read the sampling parameters from a glitch file.

        Args:
            path (str): path to the glitch file

        Returns:
            ``(dt, size, t0)`` for the glitch file, or ``None`` if the file does
            does not exist or does not contain the sampling parameters.
        """
        logger.info("Reading sampling parameters from glitch file '%s'", path)
        try:
            with h5py.File(path, "r") as hdf5:
                dt = hdf5.attrs["dt"]
                assert isinstance(dt, (float, np.floating))
                size = hdf5.attrs["size"]
                assert isinstance(size, (int, np.integer))
                t0 = hdf5.attrs["t0"]
                assert isinstance(t0, (float, np.floating))
        except (FileNotFoundError, KeyError):
            logger.info("Cannot read sampling parameters from '%s'", path)
            return None

        return float(dt), int(size), float(t0)

    def write(self, path, dt=0.0625, size=2592000, t0=0.0, mode="a") -> None:
        """Write the glitch to a glitch file.

        If the file does not exist, it is created with a time axis matching
        ``dt``, ``size``, and ``t0`` arguments. The glitch signal is computed
        according to these parameters and written to file.

        If the file already exists, we make sure that ``dt``, ``size``, and
        ``t0`` match the values used to create the file and raise an error if
        they do not. Use :meth:`lisaglitch.Glitch.read_file_sampling` to get the
        value for these parameters from an existing file.

        When creating the glitch file, metadata are saved as attributes.

        When writing a glitch, we add attributes for each local variable on the
        associated injection point dataset, prefixed with ``inj<i>``, where i is
        the index of glitch in the injection point dataset.

        Args:
            path (str): path to the glitch file
            dt (float): time step [s]
            size (int): number of samples
            t0 (float): start time [s]
            mode (str): opening mode

        Raises:
            ValueError: if the file already exists and the sampling parameters
            do not match the values used to create the file
        """
        # Open orbit file
        with h5py.File(path, mode) as hdf5:
            # Write sampling parameters if needed
            sampling = self.read_file_sampling(path)
            if sampling is None:
                logger.info("New glitch file, writing sampling parameters")
                hdf5.attrs["dt"] = dt
                hdf5.attrs["size"] = size
                hdf5.attrs["t0"] = t0
                logger.info("Setting global metadata")
                self._write_metadata(hdf5)
            else:
                logger.info("Existing glitch file, checking sampling parameters")
                if sampling != (dt, size, t0):
                    raise ValueError("Sampling parameters do not match")
            # Create injection dataset if needed
            t = t0 + np.arange(size, dtype=np.float64) * dt
            dname = self.inj_point
            if dname not in hdf5:
                logger.info("Creating injection dataset '%s'", dname)
                hdf5.create_dataset(dname, data=np.zeros_like(t))
                hdf5[dname].attrs["injection_count"] = 0
            # Add glitch to injection dataset
            logger.info("Adding glitch to injection dataset '%s'", dname)
            ninj = int(hdf5[dname].attrs["injection_count"])
            hdf5[dname][:] += self.compute_signal(t)
            # Setting metadata
            logger.info("Setting injection metadata")
            hdf5[dname].attrs["injection_count"] = ninj + 1
            self._write_metadata(hdf5[dname], prefix=f"inj{ninj}_")
        # Closing file
        logger.info("Closing glitch file %s", path)
