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
Mathematical glitches.

Defines glitches based on simple mathematical functions.

Authors:
    Jean-Baptiste Bayle <j2b.bayle@gmail.com>
    Eleonora Castelli <eleonora.castelli@unitn.it>
"""

import logging

import numpy as np

from .base import Glitch

logger = logging.getLogger(__name__)


class FunctionGlitch(Glitch):
    """Glitch with signal from a Python function.

    The function will be called with the time array as argument.

    Args:
        func (callable): function to compute the glitch signal, taking a time
            array as argument and returning an array of the same length
            [injection point unit]
        **kwargs: all other args from :class:`lisaglitch.Glitch`
    """

    def __init__(self, func, **kwargs) -> None:
        super().__init__(**kwargs)
        self.func = func

    def compute_signal(self, t) -> np.ndarray:
        return self.func(t)


class StepGlitch(Glitch):
    """Step glitch.

    A step glitch is vanishing before ``t_inj``, and is ``level`` after.

    Args:
        level (float): amplitude [injection point unit]
        **kwargs: all other args from :class:`lisaglitch.Glitch`
    """

    def __init__(self, level=1, **kwargs) -> None:
        super().__init__(**kwargs)
        self.level = float(level)  #: Amplitude [injection point unit].

    def compute_signal(self, t) -> np.ndarray:
        return np.where(t >= self.t_inj, self.level, 0)


class RectangleGlitch(Glitch):
    """Rectangular glitch.

    A rectangular glitch is vanishing except between ``t_inj`` and ``t_inj +
    width``, where it is ``level``.

    Args:
        width (float): width of the rectangle (glitch duration) [s]
        level (float): amplitude [injection point unit]
        **kwargs: all other args from :class:`lisaglitch.Glitch`
    """

    def __init__(self, width, level=1, **kwargs) -> None:
        super().__init__(**kwargs)
        self.width = float(width)  #: Glitch duration) [s].
        self.level = float(level)  #: Amplitude [injection point unit].

    def compute_signal(self, t) -> np.ndarray:
        inside = np.logical_and(t >= self.t_inj, t < self.t_inj + self.width)
        return np.where(inside, self.level, 0)
