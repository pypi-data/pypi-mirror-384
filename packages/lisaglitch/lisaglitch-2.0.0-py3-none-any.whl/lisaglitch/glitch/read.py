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
Glitches using data generated externally.

Authors:
    Jean-Baptiste Bayle <j2b.bayle@gmail.com>
    Eleonora Castelli <eleonora.castelli@unitn.it>
"""

import logging
import random
from typing import Any, List

import h5py
import numpy as np
from scipy.interpolate import InterpolatedUnivariateSpline

from .base import Glitch

logger = logging.getLogger(__name__)


class TimeSeriesGlitch(Glitch):
    """Glitch with signal from a Numpy array.

    To honor the glitch's sampling parameters, the input data may be resampled
    using spline interpolation. If you do not wish to interpolate, make sure to
    instantiate the glitch with sampling parameters matching your data.

    Args:
        t ((N,) array-like): times associated with ``tseries`` [s]
        tseries ((N,) array-like): glitch signal [injection point unit]
        interp_order (int): spline-interpolation order [one of 1, 2, 3, 4, 5]
        ext (str):
            extrapolation mode for elements out of range, see
            `scipy.interpolate.InterpolatedUnivariateSpline
            <https://docs.scipy.org/doc/scipy/reference/reference/generated/
            scipy.interpolate.InterpolatedUnivariateSpline.html>`_
        **kwargs: all other args from :class:`lisaglitch.Glitch`
    """

    def __init__(self, t, tseries, interp_order=1, ext="const", **kwargs) -> None:
        super().__init__(**kwargs)
        self.interp_order = int(interp_order)
        self.ext = str(ext)  #: Extrapolation mode for elements out of range.

        # Compute spline interpolation
        logger.info("Computing spline interpolation from time series")
        self.interpolant = InterpolatedUnivariateSpline(
            t + self.t_inj,
            tseries,
            k=self.interp_order,
            ext=self.ext,
            check_finite=True,
        )  #: Glitch signal interpolating function.

    def compute_signal(self, t) -> np.ndarray:
        return self.interpolant(t)


class HDF5Glitch(TimeSeriesGlitch):
    """Glitch with signal read from a HDF5 file.

    A glitch time-series is extracted from a dataset and injected at time
    ``t_inj``.

    Give the full path to a given dataset as ``node`` argument, or use the path
    to a group to pick a random dataset inside this group. Use the root ``/`` to
    pick a random dataset in the entire HDF5 file.

    To honor the glitch's sampling parameters, the input data may be resampled
    using spline interpolation. If you do not wish to interpolate, make sure to
    instantiate the glitch with sampling parameters matching your data.

    Args:
        path (str): path to HDF5 file
        node (str): path to dataset, or group to pick a random dataset
        exclude (list of str): datasets to exclude when picking a random dataset
    """

    def __init__(self, path, node="/", exclude=None, **kwargs) -> None:
        self.path = str(path)  #: Path to HDF5 file.
        logger.info("Opening HDF5 file '%s'", self.path)
        hdf5 = h5py.File(self.path, "r")

        # Exclude time dataset by default
        if exclude is None:
            exclude = ["t"]
        self.exclude = exclude

        # Pick dataset
        self.node = str(node)
        group = hdf5[self.node]
        if isinstance(group, h5py.Group):
            logger.debug("Picking a random dataset in group '%s'", self.node)
            dataset_names: List[str] = []
            group.visititems(
                lambda _, node: self._append_dataset_name(node, dataset_names)
            )
            self.dataset = random.choice(dataset_names)
            while self.dataset in self.exclude:
                self.dataset = random.choice(dataset_names)
        elif isinstance(group, h5py.Dataset):
            logger.debug("Using user-provided dataset '%s'", self.node)
            self.dataset = self.node  #: Glitch dataset.

        # Read dataset and time vector
        logger.info("Reading dataset '%s'", self.dataset)
        dataset = hdf5[self.dataset]

        hdf5_dt = float(self._get_closest_attr("dt", dataset))
        try:
            hdf5_t0 = float(self._get_closest_attr("t0", dataset))
        except KeyError:
            hdf5_t0 = 0
        try:
            hdf5_size = int(self._get_closest_attr("size", dataset))
        except KeyError:
            hdf5_size = len(dataset)

        hdf5_t = hdf5_t0 + np.arange(hdf5_size, dtype=np.float64) * hdf5_dt
        super().__init__(hdf5_t, dataset[:], **kwargs)

        logger.info("Closing HDF5 file '%s'", self.path)
        hdf5.close()

    @staticmethod
    def _append_dataset_name(node, datasets) -> None:
        """Append node's name to ``datasets`` if node is a dataset.

        Use this method with :meth:`h5py.Group.visititems` to list datasets in a
        group.

        Args:
            node (str): HDF5 node, either a dataset or a group
            datasets (list of str): list on which to append the dataset's name
        """
        if isinstance(node, h5py.Dataset):
            datasets.append(node.name)

    @staticmethod
    def _get_closest_attr(attr, node) -> Any:
        """Get value of attribute ``attr`` of the nearest ancestor of ``node``.

        We try to return the value of attribute ``attr`` on the node; if it does
        not exist, we go up the file hierarchy and try to read and return the
        attribute on the nearest ancestor.

        Args:
            node (str): a group or a dataset in an HDF5 file

        Raises:
            ``KeyError`` if no ancestor defines the attribute ``attr``.
        """
        if attr in node.attrs:
            return node.attrs[attr]
        if node.parent == node:
            raise KeyError(
                f"the attribute '{attr}' is not defined on '{node.file.filename}'"
            )
        return HDF5Glitch._get_closest_attr(attr, node.parent)

    def plot(self, *args, **kwargs) -> None:
        """Plot glitch signal.

        See `Glitch.plot()`.
        """
        if "title" not in kwargs:
            kwargs["title"] = f"Glitch from dataset '{self.dataset}' in '{self.path}'"
        super().plot(*args, **kwargs)
