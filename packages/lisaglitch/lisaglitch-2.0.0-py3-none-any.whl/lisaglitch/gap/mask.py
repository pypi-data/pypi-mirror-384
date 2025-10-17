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
Gap mask generation module for LISA mission data processing.

This module provides the GapMaskGenerator class for creating realistic data gap masks
that simulate various types of mission interruptions including planned maintenance,
communication blackouts, and unplanned outages.

Authors:
    Ollie Burke <ollie.burke@glasgow.ac.uk>
    Eleonora Castelli <eleonora.castelli@unitn.it>
"""

import json
from pathlib import Path
from typing import Any, Union

import h5py
import numpy as np
from lisaconstants import TROPICALYEAR_J2000DAY
from numpy.typing import NDArray
from scipy.stats import expon

SECONDS_PER_YEAR = TROPICALYEAR_J2000DAY * 86400
AN_HOUR = 60 * 60


class GapMaskGenerator:
    """
    A class to generate and manage gap masks for time series data. Original code developed by
    Eleonora Castelli (NASA Goddard) and adapted by Ollie Burke (Glasgow)
    """

    def __init__(
        self,
        sim_t: NDArray[np.floating[Any]],
        gap_definitions: dict[str, dict[str, dict[str, Any]]],
        treat_as_nan: bool = True,
        planseed: int = 11071993,
        unplanseed: int = 16121997,
    ):
        """
        Parameters
        ----------
        sim_t : np.ndarray
            Array of simulation time values.
        gap_definitions : dict
            Dictionary defining planned and unplanned gaps. Each gap entry must include:
            - 'rate_per_year' (float)
            - 'duration_hr' (float)
        treat_as_nan : bool, optional
            If True, gaps are inserted as NaNs. If False, they are inserted as zeros.
        planseed : int
            Seed for planned gap randomization.
        unplanseed : int
            Seed for unplanned gap randomization.
        """

        # Initialise sampling properties
        self.sim_t = sim_t
        dt = sim_t[1] - sim_t[0]
        self.dt = dt
        self.n_data = len(sim_t)

        # Determine whether or not mask uses nans or zeros
        self.treat_as_nan = treat_as_nan

        # Set seeds
        self.planseed = planseed
        self.unplanseed = unplanseed

        # Read in gap definitions, rates, durations, types.
        self.gap_definitions: dict[str, dict[str, dict[str, float]]] = {}

        # Quick and simple error checking
        for kind in ("planned", "unplanned"):
            if kind not in gap_definitions:
                raise ValueError(f"Missing '{kind}' section in gap_definitions.")

            self.gap_definitions[kind] = {}

            for name, entry in gap_definitions[kind].items():
                if "rate_per_year" not in entry or "duration_hr" not in entry:
                    raise ValueError(
                        f"Gap '{name}' in '{kind}' must have 'rate_per_year' and 'duration_hr'."
                    )
                if entry["rate_per_year"] < 0 or entry["duration_hr"] < 0:
                    raise ValueError(
                        f"Gap '{name}' in '{kind}' has negative rate or duration."
                    )

                self.gap_definitions[kind][name] = {
                    "rate_per_year": entry["rate_per_year"],
                    "duration_hr": entry["duration_hr"],
                }
        # If the gap definitions pass (not empty, negative etc.)
        # then we can set the gap definitions
        self._update_gap_arrays()

    def _update_gap_arrays(self) -> None:
        """
        Helper function to update the gap arrays based on the gap definitions.
        This function is called during initialization and when gap definitions are updated.

        We convert the rate_per_year into rate_per_second and duration_hr into samples
        """

        # Extract gap types for planned/unplanned gaps
        self.planned_labels = list(self.gap_definitions["planned"].keys())
        self.unplanned_labels = list(self.gap_definitions["unplanned"].keys())

        self.planned_rates = (
            np.array(
                [
                    self.gap_definitions["planned"][k]["rate_per_year"]
                    / SECONDS_PER_YEAR
                    for k in self.planned_labels
                ]
            )
            * self.dt
        )
        self.planned_durations = (
            np.array(
                [
                    self.gap_definitions["planned"][k]["duration_hr"] * 3600
                    for k in self.planned_labels
                ]
            )
            / self.dt
        )

        self.unplanned_rates = (
            np.array(
                [
                    self.gap_definitions["unplanned"][k]["rate_per_year"]
                    / SECONDS_PER_YEAR
                    for k in self.unplanned_labels
                ]
            )
            * self.dt
        )
        self.unplanned_durations = (
            np.array(
                [
                    self.gap_definitions["unplanned"][k]["duration_hr"] * 3600
                    for k in self.unplanned_labels
                ]
            )
            / self.dt
        )

    def construct_planned_gap_mask(
        self,
        rate: float,
        gap_duration: float,
        seed: Union[int, None] = None,
    ) -> NDArray[Union[np.float64, np.int_]]:
        """
        Construct a planned gap mask with regular spacing and jitter.

        Parameters
        ----------
        rate : float
            Gap rate (in events/s).
        gap_duration : float
            Gap duration (in samples).
        seed : int or None
            Random seed.

        Returns
        -------
        np.ndarray
            Array with gaps represented as NaNs or zeros, but valid data always as integer 1.
        """
        # Set specific seed
        np.random.seed(seed)
        if self.treat_as_nan:
            mask = np.ones(self.n_data, dtype=np.float64)
        else:
            mask = np.ones(self.n_data, dtype=int)
        est_num_gaps = int(self.n_data * rate)

        jitter = 0.2 * gap_duration * (np.random.rand(est_num_gaps) - 0.5)
        gap_starts = (jitter + (1 / rate) * np.arange(1, est_num_gaps + 1)).astype(int)
        gap_ends = (gap_starts + gap_duration).astype(int)

        # Decide whether or not to treat gaps as NaNs or 0s.
        gap_val = self._gap_value()

        for start, end in zip(gap_starts, gap_ends):
            if end < self.n_data:
                mask[start:end] = gap_val

        return mask

    def construct_unplanned_gap_mask(
        self,
        rate: float,
        gap_duration: float,
        seed: Union[int, None] = None,
    ) -> NDArray[Union[np.float64, np.int_]]:
        """
        Construct an unplanned gap mask using an exponential distribution.

        Parameters
        ----------
        rate : float
            Gap rate (in events/s).
        gap_duration : float
            Gap duration (in seconds).
        seed : int or None
            Random seed.

        Returns
        -------
        np.ndarray
            Array with gaps represented as NaNs or zeros, but valid data always as integer 1.
        """
        np.random.seed(seed)
        if self.treat_as_nan:
            mask = np.ones(self.n_data, dtype=np.float64)
        else:
            mask = np.ones(self.n_data, dtype=int)

        est_num_gaps = int(self.n_data * rate)
        if est_num_gaps == 0 and np.random.rand() < rate * self.n_data:
            est_num_gaps = 1

        start_offsets = expon.rvs(scale=1 / rate, size=est_num_gaps).astype(int)
        gap_starts = np.cumsum(start_offsets)
        gap_starts = gap_starts[gap_starts + gap_duration < self.n_data]
        gap_ends = (gap_starts + gap_duration).astype(int)

        # Decide whether or not to treat gaps as NaNs or 0s.
        gap_val = self._gap_value()

        for start, end in zip(gap_starts, gap_ends):
            mask[start:end] = gap_val

        return mask

    def _gap_value(self) -> Union[float, int]:
        """
        Helper function to determine the value used for gaps in the mask.
        Returns NaN if treat_as_nan is True, otherwise returns 0.
        """
        return np.nan if self.treat_as_nan else 0

    def generate_mask(
        self,
        include_planned: bool = True,
        include_unplanned: bool = True,
    ) -> NDArray[Union[np.float64, np.int_]]:
        """
        Combine planned and unplanned masks into a final mask.

        Parameters
        ----------
        include_planned : bool
            Include planned gaps.
        include_unplanned : bool
            Include unplanned gaps.

        Returns
        -------
        np.ndarray
            Final gap mask with valid data as integer 1, gaps as 0 or NaN.
        """
        if self.treat_as_nan:
            mask = np.ones(self.n_data, dtype=np.float64)
        else:
            mask = np.ones(self.n_data, dtype=int)

        # Construct planned gap mask
        if include_planned:
            for rate, duration in zip(self.planned_rates, self.planned_durations):
                planned_mask = self.construct_planned_gap_mask(
                    rate, duration, seed=self.planseed
                )
                mask = mask * planned_mask.astype(mask.dtype)

        # Construct unplanned gap mask
        if include_unplanned:
            for rate, duration in zip(self.unplanned_rates, self.unplanned_durations):
                unplanned_mask = self.construct_unplanned_gap_mask(
                    rate, duration, seed=self.unplanseed
                )
                mask = mask * unplanned_mask.astype(mask.dtype)

        return mask

    def save_to_hdf5(
        self,
        mask: np.ndarray,
        filename: str = "gap_mask_data.h5",
        save_as_quality_flags: bool = False,
    ) -> None:
        """
        Save the gap mask and associated simulation metadata to an HDF5 file.

        Parameters
        ----------
        mask : np.ndarray
            The gap mask array, typically generated using `generate_mask()`.
            Should be of the same length as `sim_t`, and contain either 1s and 0s,
            or 1s and NaNs depending on the `treat_as_nan` setting.

        filename : str, optional
            Path to the HDF5 file to create. Defaults to "gap_mask_data.h5".

        save_as_quality_flags : bool, optional
            If True, converts the mask to quality data flags before saving:
            - 1 = gap/corrupt data (where original mask has NaN or 0)
            - 0 = valid data (where original mask has 1.0 or 1)
            If False (default), saves the mask in its original format.

        Notes
        -----
        This function stores:

        - The mask data under `"gap_mask"` (original format) or `"quality_flags"` (if save_as_quality_flags=True)
        - Metadata attributes:

          - `"dt"` (time step)
          - `"treat_as_nan"` (boolean mask type flag)
          - `"saved_as_quality_flags"` (boolean indicating storage format)

        - Gap configuration details in two groups:

          - `"planned_gaps"`: each with `rate_events_per_year` and `duration_hours`
          - `"unplanned_gaps"`: same structure as planned gaps

        The resulting file can be reloaded using the `from_hdf5()` class method given below.

        """
        with h5py.File(filename, "w") as f:
            # Convert mask to quality flags if requested
            if save_as_quality_flags:
                # Convert to quality flags: 1 = gap/corrupt, 0 = valid
                if self.treat_as_nan:
                    # Input mask: 1.0 = valid, NaN = gap
                    # Output flags: 0 = valid, 1 = gap
                    quality_flags = np.where(np.isnan(mask), 1, 0).astype(np.int32)
                else:
                    # Input mask: 1 = valid, 0 = gap
                    # Output flags: 0 = valid, 1 = gap
                    quality_flags = np.where(mask == 0, 1, 0).astype(np.int32)

                f.create_dataset("quality_flags", data=quality_flags, compression="lzf")
            else:
                # Save original mask format
                f.create_dataset("gap_mask", data=mask, compression="lzf")

            # Save simulation time metadata as (t_0, t_end, dt)
            f.attrs["sim_time_info -- [t0, t_end, dt]"] = (
                float(self.sim_t[0]),
                float(self.sim_t[-1]),
                float(self.dt),
            )
            f.attrs["treat_as_nan"] = self.treat_as_nan
            f.attrs["saved_as_quality_flags"] = save_as_quality_flags

            # Save planned gap info
            planned_grp = f.create_group("planned_gaps")
            for label in self.planned_labels:
                grp = planned_grp.create_group(label)
                grp.attrs["rate_events_per_year"] = self.gap_definitions["planned"][
                    label
                ]["rate_per_year"]
                grp.attrs["duration_hours"] = self.gap_definitions["planned"][label][
                    "duration_hr"
                ]

            # Save unplanned gap info
            unplanned_grp = f.create_group("unplanned_gaps")
            for label in self.unplanned_labels:
                grp = unplanned_grp.create_group(label)
                grp.attrs["rate_events_per_year"] = self.gap_definitions["unplanned"][
                    label
                ]["rate_per_year"]
                grp.attrs["duration_hours"] = self.gap_definitions["unplanned"][label][
                    "duration_hr"
                ]

    @classmethod
    def from_hdf5(cls, filename: str) -> "GapMaskGenerator":
        """
        Reconstruct a GapMaskGenerator object from an HDF5 file.
        classmethod, so no need to instantiate the class first.
        This method reads the gap mask, simulation time, and metadata from the file,
        and returns a new instance of GapMaskGenerator.

        Parameters
        ----------
        filename : str
            Path to the HDF5 file.

        Returns
        -------
        GapMaskGenerator
            A new instance reconstructed from the file.
        """

        with h5py.File(filename, "r") as f:
            # Store simulation time, sampling interval, and mask type.
            sim_time_info = f.attrs["sim_time_info -- [t0, t_end, dt]"]
            sim_time_array = np.array(sim_time_info)  # Ensure it's a numpy array
            t0, t_end, dt = (
                float(sim_time_array[0]),
                float(sim_time_array[1]),
                float(sim_time_array[2]),
            )
            sim_t = np.arange(t0, t_end + dt, dt)
            treat_as_nan = bool(
                f.attrs.get("treat_as_nan", True)
            )  # fallback True if not saved

            # Store information about the planned gaps
            planned_gaps = {}
            for key in f["planned_gaps"]:
                grp = f["planned_gaps"][key]
                planned_gaps[key] = {
                    "rate_per_year": float(grp.attrs["rate_events_per_year"]),
                    "duration_hr": float(grp.attrs["duration_hours"]),
                }

            # Store information about the unplanned gaps
            unplanned_gaps = {}
            for key in f["unplanned_gaps"]:
                grp = f["unplanned_gaps"][key]
                unplanned_gaps[key] = {
                    "rate_per_year": float(grp.attrs["rate_events_per_year"]),
                    "duration_hr": float(grp.attrs["duration_hours"]),
                }

            gap_definitions = {
                "planned": planned_gaps,
                "unplanned": unplanned_gaps,
            }
            # Return as class object
        return cls(
            sim_t=sim_t,
            gap_definitions=gap_definitions,
            treat_as_nan=treat_as_nan,
        )

    @staticmethod
    def load_mask_from_hdf5(
        filename: str, convert_to_mask: bool = True
    ) -> tuple[np.ndarray, dict[str, Any]]:
        """
        Load just the mask data from an HDF5 file, with optional conversion.

        Parameters
        ----------
        filename : str
            Path to the HDF5 file.
        convert_to_mask : bool, optional
            If True and the file contains quality flags, convert them back to a mask format.
            If False, return the data in its stored format.

        Returns
        -------
        tuple[np.ndarray, dict]
            The mask/quality flag data and metadata dictionary containing:
            - 'treat_as_nan': boolean indicating original mask type
            - 'saved_as_quality_flags': boolean indicating storage format
            - 'data_type': string describing what was returned

        Examples
        --------
        >>> # Load quality flags as-is
        >>> flags, meta = GapMaskGenerator.load_mask_from_hdf5("data.h5", convert_to_mask=False)
        >>> # Load and convert quality flags to mask format
        >>> mask, meta = GapMaskGenerator.load_mask_from_hdf5("data.h5", convert_to_mask=True)
        """
        with h5py.File(filename, "r") as f:
            treat_as_nan = bool(f.attrs.get("treat_as_nan", True))
            saved_as_quality_flags = bool(f.attrs.get("saved_as_quality_flags", False))

            metadata = {
                "treat_as_nan": treat_as_nan,
                "saved_as_quality_flags": saved_as_quality_flags,
                "data_type": "",  # Will be set below
            }

            if saved_as_quality_flags:
                # File contains quality flags (1=gap, 0=valid)
                quality_flags = f["quality_flags"][:]

                if convert_to_mask:
                    # Convert quality flags back to mask format
                    if treat_as_nan:
                        # Convert to NaN mask: 0->1.0 (valid), 1->NaN (gap)
                        mask_data = np.where(quality_flags == 0, 1.0, np.nan)
                        metadata["data_type"] = "converted_to_nan_mask"
                    else:
                        # Convert to binary mask: 0->1 (valid), 1->0 (gap)
                        mask_data = np.where(quality_flags == 0, 1, 0)
                        metadata["data_type"] = "converted_to_binary_mask"
                    return mask_data, metadata

                metadata["data_type"] = "quality_flags"
                return quality_flags, metadata

            # File contains original mask format
            mask_data = f["gap_mask"][:]
            metadata["data_type"] = "original_mask"
            return mask_data, metadata

    def summary(
        self,
        mask: Union[NDArray[np.float64], NDArray[np.int_], None] = None,
        export_json_path: Union[str, Path, None] = None,
    ) -> dict[str, Any]:
        """
        Return a structured dictionary summarising the gap configuration
        and optionally the content of a specific mask.

        Parameters
        ----------
        mask : np.ndarray, optional
            If provided, calculates duty cycle and number of gaps based on this mask.

        export_json_path : str or Path, optional
            If provided, writes the summary dictionary to a JSON file at the given path.

        Returns
        -------
        dict
            Summary of configuration and optionally mask content.
        """
        # Extract as much information as possible from the gap definitions
        # and the mask if provided.
        summary_dict: dict[str, Any] = {
            "simulation": {
                "dt": self.dt,
                "n_data": self.n_data,
                "duration_sec": self.n_data * self.dt,
                "duration_days": self.n_data * self.dt / 86400,
            },
            "seeds": {
                "planned": self.planseed,
                "unplanned": self.unplanseed,
            },
            "planned_gaps": {},
            "unplanned_gaps": {},
        }

        for kind in ("planned", "unplanned"):
            for name, info in self.gap_definitions[kind].items():
                duration_sec = info["duration_hr"] * 3600
                duration_samples = int(duration_sec / self.dt)
                rate_per_sec = info["rate_per_year"] / SECONDS_PER_YEAR

                summary_dict[f"{kind}_gaps"][name] = {
                    "rate_events_per_year": info["rate_per_year"],
                    "duration_hr": info["duration_hr"],
                    "rate_events_per_sec": rate_per_sec,
                    "duration_sec": duration_sec,
                    "duration_samples": duration_samples,
                }

        # Add dynamic information from mask if provided
        if mask is not None:
            is_gap = np.isnan(mask) if self.treat_as_nan else (mask == 0)
            duty_cycle = 1.0 - np.sum(is_gap) / len(mask)

            summary_dict["mask_analysis"] = {
                "duty_cycle_percent": round(100 * duty_cycle, 4),
                "total_gap_samples": int(np.sum(is_gap)),
                "total_gap_hours": round(np.sum(is_gap) * self.dt / 3600, 2),
            }

            # Optional: Count number of contiguous gaps
            gap_count = 0
            in_gap = False
            for val in is_gap:
                if val and not in_gap:
                    gap_count += 1
                    in_gap = True
                elif not val:
                    in_gap = False
            summary_dict["mask_analysis"]["number_of_gap_segments"] = gap_count

        if export_json_path is not None:
            with open(export_json_path, "w", encoding="utf-8") as f:
                json.dump(summary_dict, f, indent=4)
        return summary_dict

    def build_quality_flags(
        self, data_array: NDArray[np.float64], save_to_file: Union[str, None] = None
    ) -> NDArray[np.int_]:
        """
        Build a masking function based on the gap definitions and the provided data array.

        Parameters
        ----------
        data_array : np.ndarray
            The data array to be masked.
        save_to_file : str, optional
            If provided, saves the quality flags to an HDF5 file at the specified path.

        Returns
        -------
        np.ndarray
            A masking function that can be applied to the data array.
        """
        # Wherever nans appear, replace this with integer 1.
        # Else 0 for valid data product.
        mask = np.where(np.isnan(data_array), 1, 0).astype(np.int32)

        if save_to_file is not None:
            # Convert quality flags back to mask format for saving
            float_mask = self.quality_flags_to_mask(mask)
            self.save_to_hdf5(
                float_mask, filename=save_to_file, save_as_quality_flags=True
            )

        return mask

    @staticmethod
    def quality_flags_to_mask(quality_flags: NDArray[np.int_]) -> NDArray[np.float64]:
        """
        Convert integer quality flags to a float mask suitable for data multiplication.

        This utility function converts from the compact storage format (integers)
        to the working format (floats with NaNs) used for masking data arrays.

        Parameters
        ----------
        quality_flags : NDArray[np.int_]
            Integer array where:
            - 0 = valid data
            - 1 = corrupt/gap data

        Returns
        -------
        NDArray[np.float64]
            Float mask array where:
            - 1.0 = valid data (multiply by 1.0 = unchanged)
            - NaN = gap data (multiply by NaN = NaN)

        Examples
        --------
        >>> flags = np.array([0, 1, 0, 1, 0], dtype=int)
        >>> mask = GapMaskGenerator.quality_flags_to_mask(flags)
        >>> print(mask)
        [1.0, nan, 1.0, nan, 1.0]
        >>> data = np.array([10.0, 20.0, 30.0, 40.0, 50.0])
        >>> masked_data = data * mask
        >>> print(masked_data)
        [10.0, nan, 30.0, nan, 50.0]
        """
        # Convert 0->1.0 (valid data) and 1->NaN (corrupt data)
        return np.where(quality_flags == 0, 1.0, np.nan)

    def _match_gap_length_to_label(
        self, gap_length_samples: int
    ) -> Union[tuple[str, str], None]:
        """
        Match a gap length to one of the known planned/unplanned definitions.

        Parameters
        ----------
        gap_length_samples : int
            Length of the gap in samples.

        Returns
        -------
        tuple of (kind, label) or None
        """
        for kind in ("planned", "unplanned"):
            for label in self.gap_definitions[kind]:
                expected = int(
                    self.gap_definitions[kind][label]["duration_hr"] * 3600 / self.dt
                )
                if (
                    abs(gap_length_samples - expected) < 0.1 * expected
                ):  # allow 10% fuzz
                    return (kind, label)
        return None
