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
Helper functions to build a LPF distribution and sample glitches from it.

Authors:
    Natalia Korsakova <natalia.korsakova@obspm.fr>
    Jean-Baptiste Bayle <j2b.bayle@gmail.com>
"""

import itertools
import logging

import numpy as np
import torch
from torch import optim
from torch.distributions import MultivariateNormal

from .flow import ActNorm, Invertible1x1Conv, NormalizingFlowModel
from .nsflow import NSF_CL

logger = logging.getLogger(__name__)


def initialise_network(dev):
    """Initialize network architecture that will be used for training and sampling.

    Initialize prior distribution, the flow and optimizer.

    Args:
        dev: device to use ('cuda:0' or 'cpu')

    Returns:
        2-tuple (mode, optimizer).
    """
    prior = MultivariateNormal(torch.zeros(2), torch.eye(2))

    # Neural splines, coupling
    nfs_flow = NSF_CL
    flows = [nfs_flow(dim=2, K=8, B=3, hidden_dim=256) for _ in range(9)]
    convs = [Invertible1x1Conv(dim=2) for _ in flows]
    norms = [ActNorm(dim=2) for _ in flows]
    flows = list(itertools.chain(*zip(norms, convs, flows)))

    # Construct the model
    model = NormalizingFlowModel(prior, flows).to(dev)
    # Optimizer
    optimizer = optim.Adam(model.parameters(), lr=5e-5, weight_decay=1e-5)

    return model, optimizer


class LPFGlitchParameterSampler:
    """Sample glitch parameters in the LISA Pathfinder distribution."""

    def __init__(self, dev, min_beta, max_beta, min_amp, max_amp):
        """Initialize a sampler for LPG glitch parameters.

        Args:
            dev: device to use ('cuda:0' or 'cpu')
            min_beta: minimum Poisson parameter for renomarlization
            max_beta: maximum Poisson parameter for renomarlization
            min_amp: minimum glitch amplitude for renomarlization
            max_amp: maximum glitch amplitude for renomarlization
        """

        self.model_path = None
        self.model = None
        self.optimizer = None
        self.dev = dev

        # Parameters to renormalise back to the proper values.
        self.min_beta = min_beta
        self.max_beta = max_beta
        self.min_amp = min_amp
        self.max_amp = max_amp

    def define_model(self):
        """Define the model for which the weights are loaded."""
        self.model, self.optimizer = initialise_network(self.dev)

    def load_model(self, model_path):
        """Load trained model from the file.

        Args:
            model_path: path to model file
        """
        self.model_path = model_path
        checkpoint = torch.load(self.model_path, map_location=torch.device(self.dev))
        self.model.load_state_dict(checkpoint["model_state_dict"])
        self.optimizer.load_state_dict(checkpoint["optimizer_state_dict"])

    def sample_param(self, number_samples):
        """Sample the parameters from the fitted weights.

        Args:
            number_samples: number of points to sample
        """
        zsample = self.model.sample(number_samples)
        z_point = zsample[-1]
        z_point = z_point.detach().cpu().numpy()
        return z_point

    def generator(self, beta_range_max=None, amp_range_min=None):
        """Generator that outputs the next pair of the glitch parameters.

        Note that `beta_range` and `amp_range` are conditions that can be set
        additionally if we want to impose some restriction on the
        glitch distribution (like `beta_range` < 150, `amp_range` > 1e-12).

        Args:
            beta_range_max: maximum allowed Poisson parameter
            amp_range_min: minimum allowed glitch amplitude
        """
        beta = 0.0
        amp = 0.0

        number_samples = 1
        while True:

            lpf_samples = self.sample_param(number_samples)

            beta_correct_range = np.exp(
                self.min_beta + lpf_samples[:, 0] * (self.max_beta - self.min_beta)
            )
            amp_correct_range = np.exp(
                self.min_amp + lpf_samples[:, 1] * (self.max_amp - self.min_amp)
            )

            if beta_range_max is not None and amp_range_min is not None:
                if (
                    beta_correct_range < beta_range_max
                    and amp_correct_range > amp_range_min
                ):
                    beta = beta_correct_range[0]
                    amp = amp_correct_range[0]
                    yield beta, amp
                else:
                    continue
            else:
                beta = beta_correct_range[0]
                amp = amp_correct_range[0]
                yield beta, amp

    def generate(self, number_samples):
        """Generate many samples at once.

        Args:
            number_samples: number of samples
        """
        lpf_samples = self.sample_param(number_samples)
        beta_correct_range = np.exp(
            self.min_beta + lpf_samples[:, 0] * (self.max_beta - self.min_beta)
        )
        amp_correct_range = np.exp(
            self.min_amp + lpf_samples[:, 1] * (self.max_amp - self.min_amp)
        )

        return beta_correct_range, amp_correct_range


def estimate_poisson_beta(path_intervals):
    """Estimate Poisson's lambda parameter from interarrivals.

    Read a file containing glitch arrival time differences, and estimate the Poisson
    distribution's lambda parameter.

    Args:
        path_intervals: path to interarrival file

    Returns:
        Sample estimate of Poisson's lambda parameter.
    """
    interarrivals = np.loadtxt(
        path_intervals,
        comments="#",
        delimiter=" ",
        skiprows=0,
        usecols=(0),
        unpack=False,
    )
    return 1.0 / np.mean(interarrivals)
