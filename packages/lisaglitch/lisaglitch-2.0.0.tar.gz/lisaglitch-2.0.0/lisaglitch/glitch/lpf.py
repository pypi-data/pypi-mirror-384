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
Models used to fit glitches in LISA Pathfinder data, and associated libraries.

Authors:
    Jean-Baptiste Bayle <j2b.bayle@gmail.com>
    Eleonora Castelli <eleonora.castelli@unitn.it>
    Natalia Korsakova <natalia.korsakova@obspm.fr>
"""

import logging
import random
from typing import Any

import h5py
import numpy as np
from scipy.special import eval_genlaguerre  # pylint: disable=no-name-in-module

from .base import Glitch
from .read import HDF5Glitch

logger = logging.getLogger(__name__)


def _safe_exp(x):
    """Safely compute exponential, suppressing overflow warnings."""
    with np.errstate(over="ignore", invalid="ignore"):
        return np.exp(x)


def _safe_subtract(a, b):
    """Safely subtract arrays, suppressing invalid operation warnings."""
    with np.errstate(invalid="ignore"):
        return a - b


def _safe_multiply(a, b):
    """Safely multiply arrays, suppressing overflow warnings."""
    with np.errstate(over="ignore", invalid="ignore"):
        return a * b


class OneSidedDoubleExpGlitch(Glitch):
    r"""One-sided double-exponential glitch (LPF) [m/s2].

    A one-sided double-exponential glitch begins at  begins at
    :math:`t_\text{inj}`, ramps up to an amplitude :math:`A / (t_\text{rise} -
    t_\text{fall})` via the :math:`t_\text{rise}` timescale, and flattens off
    via the :math:`t_\text{fall}` timescale to 0.

    Defining :math:`\delta t = t - t_\text{inj}`, the signal is given by

    .. math::

        \frac{A (e^{-\delta t / t_\text{rise}} - e^{-\delta t /
        t_\text{fall}})}{t_\text{rise} - t_\text{fall}},

    and converges to 0 when :math:`t` goes to infinity.

    When :math:`t_\text{fise} = t_\text{fall}`, the previous equation becomes
    singular. We use the following continuous extension,

    .. math::

        \frac{A \delta t  e^{-\delta t / t_\text{fall}}}{t_\text{fall}^2}.

    Args:
        t_rise: rise timescale [s]
        t_fall: fall timescale [s]
        level: amplitude [injection point unit]
    """

    def __init__(
        self, t_rise: float, t_fall: float, level: float = 1.0, **kwargs
    ) -> None:
        super().__init__(**kwargs)
        self.t_rise = float(t_rise)  #: Rise timescale [s].
        self.t_fall = float(t_fall)  #: Fall timescale [s].
        self.level = float(level)  #: Amplitude [injection point unit].

    def compute_signal(self, t: np.ndarray) -> np.ndarray:
        delta_t = t - self.t_inj
        if self.t_fall != self.t_rise:
            dbexp = _safe_subtract(
                _safe_exp(-delta_t / self.t_rise), _safe_exp(-delta_t / self.t_fall)
            )
            y_inside = self.level * dbexp / (self.t_rise - self.t_fall)
        else:
            y_inside = (
                self.level
                * delta_t
                * _safe_exp(-delta_t / self.t_fall)
                / self.t_fall**2
            )
        return np.where(delta_t >= 0, y_inside, 0)


class IntegratedOneSidedDoubleExpGlitch(Glitch):
    r"""Integrated one-sided double-exponential glitch (LPF) [m/s].

    The integrated signal implemented here is given by

    .. math::

        A \qty[1 - \frac{t_\text{rise} e^{-\delta t / t_\text{rise}} -
        t_\text{fall} e^{-\delta t / t_\text{fall}}}{t_\text{rise} -
        t_\text{fall}}],

    and converges to :math:`A` when :math:`t` goes to infinity.

    When :math:`t_\text{rise} = t_\text{fall} \neq 0`, the previous expression
    becomes singular. We use use the following continuous extension,

    .. math::

        A \qty[1 - \qty(1 + \frac{\delta t}{t_\text{fall}}) e^{-\delta t /
        t_\text{fall}}].

    Args:
        t_rise (float): rise timescale [s]
        t_fall (float): fall timescale [s]
        level (float): amplitude [injection point unit]
    """

    def __init__(
        self, t_rise: float, t_fall: float, level: float = 1.0, **kwargs
    ) -> None:
        super().__init__(**kwargs)
        self.t_rise = float(t_rise)  #: Rise timescale [s].
        self.t_fall = float(t_fall)  #: Fall timescale [s].
        self.level = float(level)  #: Amplitude [injection point unit].

    def compute_signal(self, t: np.ndarray) -> np.ndarray:
        delta_t = t - self.t_inj
        if self.t_fall != self.t_rise:
            dbexp = _safe_subtract(
                _safe_multiply(self.t_rise, _safe_exp(-delta_t / self.t_rise)),
                _safe_multiply(self.t_fall, _safe_exp(-delta_t / self.t_fall)),
            )
            y_inside = self.level * (1 - dbexp / (self.t_rise - self.t_fall))
        else:
            y_inside = self.level * (
                1 - (1 + delta_t / self.t_fall) * _safe_exp(-delta_t / self.t_fall)
            )
        return np.where(delta_t >= 0, y_inside, 0)


class TwoSidedDoubleExpGlitch(Glitch):
    r"""Integrated two-sided double-exponential glitch (LPF) [m/s2].

    A two-sided double-exponential glitch begins at :math:`t_\text{inj}`, ramps
    up to level :math:`A` via the :math:`t_\text{rise}` timescale, oscillates
    around zero and then and flattens off via the :math: `t_\text{fall}`
    timescale to 0.

    Defining :math:`\delta t = t - t_\text{inj}`, the signal is given by

    .. math::

        \frac{1}{t_\text{fall} - t_\text{rise}} \qty[\frac{D + t_\text{fall}
        A}{t_\text{rise}} e^{-\delta t / t_\text{rise}} - \frac{D +
        t_\text{rise} A}{t_\text{fall}} e^{-\delta t / t_\text{fall}}],

    and falls back to 0 when :math:`t` goes to infinity.

    When :math:`t_\text{fise} = t_\text{fall}`, the previous equation becomes
    singular. We use the following continuous extension,

    .. math::

        A \qty[1 - \qty(1 - \frac{\delta t}{t_\text{fall}} - \delta t \frac{D}{A
        t_\text{fall}^2}) e^{-\delta t / t_\text{fall}}].

    Args:
        t_rise (float): rise timescale [s]
        t_fall (float): fall timescale [s]
        level (float): amplitude [injection point unit]
        displacement (float): induced displacement [m]
    """

    def __init__(
        self,
        t_rise: float,
        t_fall: float,
        level: float = 1.0,
        displacement: float = 1.0,
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)
        self.t_rise = float(t_rise)  #: Rise timescale [s].
        self.t_fall = float(t_fall)  #: Fall timescale [s].
        self.level = float(level)  #: Amplitude [injection point unit].
        self.displacement = float(displacement)  #: Induced displacement [m].

    def compute_signal(self, t: np.ndarray) -> np.ndarray:
        delta_t = t - self.t_inj
        if self.t_fall != self.t_rise:
            dbexp = (
                self.displacement + self.level * self.t_fall
            ) / self.t_rise * np.exp(-delta_t / self.t_rise) - (
                self.displacement + self.level * self.t_rise
            ) / self.t_fall * np.exp(
                -delta_t / self.t_fall
            )
            y_inside = dbexp / (self.t_rise - self.t_fall)
        else:
            dbexp = -delta_t * (
                self.displacement + self.level * self.t_fall
            ) + self.t_fall * (self.displacement + 2 * self.level * self.t_fall)
            y_inside = dbexp * np.exp(-delta_t / self.t_fall) / self.t_fall**3
        return np.where(delta_t >= 0, y_inside, 0)


class IntegratedTwoSidedDoubleExpGlitch(Glitch):
    r"""Integrated two-sided double-exponential glitch (LPF) [m/s].

    The integrated signal implemented here is given by

    .. math::

        A + \frac{\qty[e^{-\delta t / t_\text{rise}} (D + A t_\text{fall}) -
        e^{-\delta t / t_\text{fall}} (D + A t_\text{rise})]}{t_\text{fall} -
        t_\text{rise}},

    and falls back to 0 when :math:`t` goes to infinity.

    When :math:`t_\text{fise} = t_\text{fall}`, the previous equation becomes
    singular. We use the following continuous extension,

    .. math::

        A \qty[1 - \qty(1 - \frac{\delta t}{t_\text{fall}} - \frac{D \delta t}{A
        t_\text{fall}^2}) e^{-\delta t / t_\text{fall}}].

    Args:
        t_rise (float): rise timescale [s]
        t_fall (float): fall timescale [s]
        level (float): amplitude [injection point unit]
        displacement (float): induced displacement [m]
    """

    def __init__(
        self,
        t_rise: float,
        t_fall: float,
        level: float = 1.0,
        displacement: float = 1.0,
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)
        self.t_rise = float(t_rise)  #: Rise timescale [s].
        self.t_fall = float(t_fall)  #: Fall timescale [s].
        self.level = float(level)  #: Amplitude [injection point unit].
        self.displacement = float(displacement)  #: Induced displacement [m].

    def compute_signal(self, t: np.ndarray) -> np.ndarray:
        delta_t = t - self.t_inj
        if self.t_fall != self.t_rise:
            dbexp = (self.displacement + self.level * self.t_fall) * np.exp(
                -delta_t / self.t_rise
            ) - (self.displacement + self.level * self.t_rise) * np.exp(
                -delta_t / self.t_fall
            )
            y_inside = self.level + dbexp / (self.t_rise - self.t_fall)
        else:
            y_inside = self.level * (
                1
                - (
                    1
                    - delta_t / self.t_fall
                    - delta_t * self.displacement / (self.level * self.t_fall**2)
                )
                * np.exp(-delta_t / self.t_fall)
            )
        return np.where(delta_t >= 0, y_inside, 0)


class ShapeletGlitch(Glitch):
    r"""Exponential shapelet glitch. [m/s2]

    The glitch signal is given by the normalized 1D hydrogen atom wavefunctions.
    For the default case ``n = 1``, the signal is given by

    .. math::

        2 \alpha \frac{\delta t}{\beta} e^{-\delta t / \beta},

    where :math:`\alpha = \frac{A}{\beta}`, with :math:`A` the glitch amplitude
    and :math:`\beta` the glitch damping time, :math:`\delta t = t - t_\text{inj}`.

    For other values of ``n``,

    .. math::

        2 \alpha (-1)^{n-1} \frac{\delta t}{\beta} n^{-2.5} L^1_{n-1} \frac{\delta
        t}{n \beta} e^{-\delta t / (n \beta)},

    where :math:`L^1_{n-1}(t)` is the generalized Laguerre polynomial.

    This model was used to fit the LISA Pathfinder glitches and produce estimate
    of the the glitch distribution, as well as the production of LDC data.

    This model is equivalent to OneSidedDoubleExpGlitch with

    .. math::

        \lim_{t_\text{rise} \to t_\text{fall}} t_\text{fall} = \beta

    and

    .. math::

        \Delta v = 2 \alpha \beta

    Args:
        level (float): amplitude [injection point unit]
        beta (float): damping time [s]
        quantum_n (int): number of shapelet components (quantum energy level)
    """

    def __init__(
        self, level: float = 1, beta: float = 1.0, quantum_n: int = 1, **kwargs
    ) -> None:
        super().__init__(**kwargs)

        self.level = float(level)  #: Amplitude [injection point unit].
        self.beta = float(beta)  #: Damping time [s].
        self.quantum_n = int(
            quantum_n
        )  #: Number of shapelet components (quantum energy level).

    def compute_signal(self, t: np.ndarray) -> np.ndarray:
        alpha = self.level / self.beta / 2
        delta_t = t - self.t_inj
        t_inside = delta_t >= 0
        normalized_t = 2 * delta_t[t_inside] / (self.quantum_n * self.beta)

        # Scipy special functions are written in C, and are not
        # correctly recognized by Pylint, so disabling linting here
        laguerre = eval_genlaguerre(self.quantum_n - 1, 1, normalized_t)

        y_inside = np.zeros_like(t)
        y_inside[t_inside] = (
            2
            * alpha
            * (-1) ** (self.quantum_n - 1)
            * delta_t[t_inside]
            / self.beta
            * self.quantum_n ** (-2.5)
            * laguerre
            * np.exp(-normalized_t / 2)
        )

        return y_inside


class IntegratedShapeletGlitch(Glitch):
    r"""Single-component (``n = 1``) integrated exponential shapelet glitch. [m/s]

    The glitch signal is given by the normalized 1D hydrogen atom wavefunctions,
    which we integrate over time with ``n = 1``,

    .. math::

        2 \alpha \beta \qty[1 - \qty(1 + \frac{\delta t}{\beta}) e^{-
        \delta t / \beta}].

    where :math:`\alpha = \frac{A}{\beta}`, with :math:`A` the glitch amplitude
    and :math:`\beta` the glitch damping time, :math:`\delta t = t - t_\text{inj}`.

    This model was used to fit the LISA Pathfinder glitches and produce estimate
    of the the glitch distribution, as well as the production of LDC data.

    This model is equivalent to OneSidedDoubleExpGlitch with

    .. math::

        \lim_{t_\text{rise} \to t_\text{fall}} t_\text{fall} = \beta

    and

    .. math::

        \Delta v = 2 \alpha \beta

    Args:
        level (float): amplitude [injection point unit]
        beta (float): damping time [s]
    """

    def __init__(self, level: float = 1.0, beta: float = 1.0, **kwargs) -> None:
        super().__init__(**kwargs)
        self.level = float(level)  #: Amplitude [injection point unit].
        self.beta = float(beta)  #: Damping time [s].

    def compute_signal(self, t: np.ndarray) -> np.ndarray:
        alpha = self.level / self.beta / 2
        delta_t = t - self.t_inj
        t_inside = delta_t >= 0
        normalized_t = delta_t[t_inside] / self.beta

        result = np.zeros_like(t)
        result[t_inside] = (
            2 * alpha * self.beta * (1 - (1 + normalized_t) * np.exp(-normalized_t))
        )
        return result


class LPFLibraryGlitch(HDF5Glitch):
    """Glitch from a LISA Pathfinder glitch library.

    The LISA Pathfinder glitch library has the following structure::

        timeseries / runXX / glitchYY

    You can specify a run and glitch number, or leave them as ``None`` to let
    the class pick a random run and/or glitch.

    The latest LPF glitch library is available for download in the LISA Glitch
    project's `data repository
    <https://gitlab.in2p3.fr/lisa-simulation/glitch/-/tree/master/data>`_. The
    library provides acceleration signals, used by default by this class. If you
    wish to inject velocity glitch, use `integrated=True` to use an analytic
    time-integrated version of the signal.

    Args:
        path (str): path to LPF glitch library
        run (int or None): run number, or None to sample a random run
        glitch (int or None): glitch number, or None to sample a random glitch
        integrated (bool): whether to integrate glitch signal (use a velocity glitch)
    """

    def __init__(
        self,
        path: str,
        run: int | None = None,
        glitch: int | None = None,
        integrated: bool = False,
        **kwargs,
    ) -> None:

        self.library = str(path)  #: Path to LPF glitch library.
        logger.info("Opening LPF glitch library '%s'", self.library)
        hdf5 = h5py.File(self.library, "r")

        # Pick run
        if run is None:
            self.run = None
            logger.debug("Picking a random run in library '%s'", self.library)
            timeseries_group = hdf5.get("timeseries")
            assert isinstance(timeseries_group, h5py.Group)
            random_group = random.choice(list(timeseries_group.keys()))
            self.run_group = f"timeseries/{random_group}"
        else:
            self.run = int(run)
            logger.debug("Using user-provided run '%s'", self.run)
            self.run_group = f"timeseries/run{self.run:02}"

        try:
            run_group_object = hdf5[self.run_group]
        except KeyError as error:
            raise KeyError(
                f"run group '{self.run_group}' not found in '{self.library}'"
            ) from error
        assert isinstance(run_group_object, h5py.Group)

        # Pick glitch
        if glitch is None:
            self.glitch = None
            logger.debug("Picking a random glitch in run '%s'", self.run)
            random_dataset = random.choice(list(run_group_object.keys()))
            self.glitch_dataset = f"{self.run_group}/{random_dataset}"
        else:
            self.glitch = int(glitch)
            logger.debug("Using user-provided glitch '%s'", self.glitch)
            self.glitch_dataset = (
                f"{self.run_group}/glitch{self.glitch:02}"  #: Path to glitch dataset.
            )

        try:
            hdf5[self.glitch_dataset]
        except KeyError as error:
            raise KeyError(
                f"glitch dataset '{self.glitch_dataset}' not found in '{self.library}'"
            ) from error

        logger.info("Closing LPF glitch library '%s'", self.library)
        hdf5.close()

        super().__init__(self.library, self.glitch_dataset, **kwargs)

        self.integrated = bool(
            integrated
        )  #: Whether to integrate glitch signal (use a velocity glitch).
        if self.integrated:
            # Integrate interpolant once analytically
            logger.debug(
                "Integrating LPF library acceleration glitch signal to velocity"
            )
            self.interpolant = self.interpolant.antiderivative()


class LPFLibraryModelGlitch:
    r"""Double-exponential glitch using parameters from a LPF glitch library.

    Glitch parameters are read from the library, and either
    :class:`lisaglitch.OneSidedDoubleExpGlitch` or
    :class:`lisaglitch.TwoSidedDoubleExpGlitch` class is used to generate the
    signal.

    The LISA Pathfinder glitch library has the following structure::

        legacy_params / runXX / glitchYY

    You can specify a run and glitch number, or leave them as ``None`` to let
    the class pick a random run and/or glitch.

    The latest LPF glitch library is available for download in the LISA Glitch
    project's `data repository
    <https://gitlab.in2p3.fr/lisa-simulation/glitch/-/tree/master/data>`_. The
    libnrary provides acceleration signals, used by default by this class. If
    you wish to inject velocity glitch, use `integrated=True` to use an analytic
    time-integrated version of the signal.

    Args:
        path (str): path to LPF glitch library
        run (int or None): run number, or None to sample a random run
        glitch (int or None): glitch number, or None to sample a random glitch
        integrated (bool): whether to integrate glitch signal (use a velocity glitch)

    Attributes:
        library: Path to LPF glitch library.
        run_group: Path to run group.
        glitch_dataset: Path to glitch dataset.
        integrated: Whether to integrate glitch signal (use a velocity glitch).
    """

    def __new__(
        cls,
        path: str,
        run: int | None = None,
        glitch: int | None = None,
        integrated: bool = False,
        **kwargs,
    ) -> Any:

        library = str(path)
        logger.info("Opening LPF glitch library '%s'", library)
        hdf5 = h5py.File(library, "r")

        # Pick run
        if run is None:
            run = None
            logger.debug("Picking a random run in library '%s'", library)
            legacy_params_group = hdf5.get("legacy_params")
            assert isinstance(legacy_params_group, h5py.Group)
            random_group = random.choice(list(legacy_params_group.keys()))
            run_group = f"legacy_params/{random_group}"
        else:
            run = int(run)
            logger.debug("Using user-provided run '%s'", run)
            run_group = f"legacy_params/run{run:02}"

        try:
            run_group_object = hdf5[run_group]
        except KeyError as error:
            raise KeyError(
                f"run group '{run_group}' not found in '{library}'"
            ) from error
        assert isinstance(run_group_object, h5py.Group)

        # Pick glitch
        if glitch is None:
            glitch = None
            logger.debug("Picking a random glitch in run '%s'", run)
            random_dataset = random.choice(list(run_group_object.keys()))
            glitch_dataset = f"{run_group}/{random_dataset}"
        else:
            glitch = int(glitch)
            logger.debug("Using user-provided glitch '%s'", glitch)
            glitch_dataset = f"{run_group}/glitch{glitch:02}"

        try:
            legacy_params_ds = hdf5[glitch_dataset]
            assert isinstance(legacy_params_ds, h5py.Dataset)
            legacy_params = legacy_params_ds[:]
        except KeyError as error:
            raise KeyError(
                f"glitch dataset '{glitch_dataset}' not found in '{library}'"
            ) from error

        logger.info("Closing LPF glitch library '%s'", library)
        hdf5.close()

        # Retreive parameters
        level = float(legacy_params[0])
        t_rise = float(legacy_params[2])
        t_fall = float(legacy_params[3])
        displacement = float(legacy_params[4])

        if not integrated:
            # Initialize the acceleration glitch
            if displacement != 0:
                instance: Any = TwoSidedDoubleExpGlitch(
                    t_rise, t_fall, level, displacement, **kwargs
                )
            else:
                instance = OneSidedDoubleExpGlitch(t_rise, t_fall, level, **kwargs)
        else:
            # Initialize the (integrated) velocity glitch
            if displacement != 0:
                instance = IntegratedTwoSidedDoubleExpGlitch(
                    t_rise, t_fall, level, displacement, **kwargs
                )
            else:
                instance = IntegratedOneSidedDoubleExpGlitch(
                    t_rise, t_fall, level, **kwargs
                )

        # Set parameters as attributes on the glitch instance
        instance.library = library
        instance.integrated = integrated
        instance.run = run
        instance.run_group = run_group
        instance.glitch = glitch
        instance.glitch_dataset = glitch_dataset
        instance.legacy_params = legacy_params
        instance.plot = lambda *args, **kwargs: LPFLibraryModelGlitch.plot(
            instance, *args, **kwargs
        )

        return instance

    @staticmethod
    def plot(
        instance: "LPFLibraryModelGlitch",
        *args,
        **kwargs,
    ) -> None:
        """Plot glitch signal.

        See :meth:`lisaglitch.Glitch.plot`.
        """
        instance.__class__.plot(instance, *args, **kwargs)
