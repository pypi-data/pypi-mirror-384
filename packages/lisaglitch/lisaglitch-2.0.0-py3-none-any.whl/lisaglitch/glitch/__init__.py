#! /usr/bin/env python3
# -*- coding: utf-8 -*-
# pylint: disable=missing-module-docstring

import importlib.metadata

from .base import INJECTION_POINTS, Glitch
from .lpf import (
    IntegratedOneSidedDoubleExpGlitch,
    IntegratedShapeletGlitch,
    IntegratedTwoSidedDoubleExpGlitch,
    LPFLibraryGlitch,
    LPFLibraryModelGlitch,
    OneSidedDoubleExpGlitch,
    ShapeletGlitch,
    TwoSidedDoubleExpGlitch,
)
from .math import FunctionGlitch, RectangleGlitch, StepGlitch
from .read import HDF5Glitch, TimeSeriesGlitch

# Automatically set by `poetry dynamic-versioning`
__version__ = "0.0.0"


try:
    metadata = importlib.metadata.metadata("lisaglitch").json
    __author__ = metadata["author"]
    __email__ = metadata["author_email"]
except importlib.metadata.PackageNotFoundError:
    pass
