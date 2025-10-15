#  Copyright (c) 2018-2024, Qualcomm Innovation Center, Inc. All rights reserved.
#  Copyright (C) 2025 Embedl AB.
#
#  Redistribution and use in source and binary forms, with or without
#  modification, are permitted provided that the following conditions are met:
#
#  1. Redistributions of source code must retain the above copyright notice,
#     this list of conditions and the following disclaimer.
#
#  2. Redistributions in binary form must reproduce the above copyright notice,
#     this list of conditions and the following disclaimer in the documentation
#     and/or other materials provided with the distribution.
#
#  3. Neither the name of the copyright holder nor the names of its contributors
#     may be used to endorse or promote products derived from this software
#     without specific prior written permission.
#
#  THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
#  AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
#  IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
#  ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE
#  LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
#  CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
#  SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
#  INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
#  CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
#  ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
#  POSSIBILITY OF SUCH DAMAGE.
#
#  SPDX-License-Identifier: BSD-3-Clause

import numpy as np
from aimet_common.utils import AimetLogger


def compute_psnr(
    expected: np.ndarray,
    actual: np.ndarray,
    max_psnr: float = 100.0,
) -> float:
    """
    Computes the Peak Signal-to-Noise Ratio (PSNR) for two values
    PSNR = 20 * log10(data_range / noise) where noise is Root Mean Square error between expected and actual

    Where the data_range is the dynamic range of expected value, computed as maximum of:

    1. expected.max() - expected.min() (standard dynamic range)
    2. np.abs(expected).max() (absolute max value)

    NOTE: Ensure PSNR between (-100, 100) dB to ensure numerical stability in downstream tasks like sorting during per-layer analysis.
          Uses separate thresholds for data_range and noise to ensure smooth behaviour near zero.

    :param expected: The reference values or ground truth (FP32 outputs)
    :param actual: The noisy values to compare against (quantized outputs)
    :param max_psnr: The maximum PSNR value to clip to (default is 100 dB)
    :return: The computed PSNR value in dB
    """
    logger = AimetLogger.get_area_logger(AimetLogger.LogAreas.Utils)

    expected = np.asarray(expected)
    actual = np.asarray(actual)

    if expected.shape != actual.shape:
        raise ValueError("Input arrays must have the same shape.")

    if expected.size == 0 or actual.size == 0:
        raise ValueError("Input arrays must not be empty.")

    # Allow only finite expected values (Exclude NaN, +inf and -inf)
    if not np.all(np.isfinite(expected)):
        raise ValueError("Input arrays must have finite values.")

    # If the actual values contain NaN or +inf or -inf, treat as worst-case quality by returning -max_psnr
    if not np.all(np.isfinite(actual)):
        logger.warning("The actual values contain NaNs or infinite values.")
        return -max_psnr

    # Compute maximum custom data range
    epsilon = 1e-10  # The minimum value for data range to avoid instability
    data_range = max(expected.max() - expected.min(), np.abs(expected).max())
    data_range = max(data_range, epsilon)  # Avoid log10(very small / noise)

    # Compute noise power and RMS error
    noise_epsilon = epsilon * 10 ** (-max_psnr / 20)
    noise_pw = np.mean(np.square(expected - actual))
    noise = max(
        np.sqrt(noise_pw), noise_epsilon
    )  # Avoid log10(data_range / 0)

    # Compute PSNR and clip to ensure numerical stability
    psnr = 20 * np.log10(data_range / noise)
    return float(np.clip(psnr, -max_psnr, max_psnr))
