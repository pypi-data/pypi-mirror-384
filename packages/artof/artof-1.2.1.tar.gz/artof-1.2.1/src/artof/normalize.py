"""
Module containing different normalization modes for artof fixed and sweep measurements.
"""

import numpy as np

from artof.sweep import SweepConfig


def get_norm_scaling_factor(
    norm_modes: list, iterations: int, dwell_time: float
) -> float:
    """
    Get scaling factor for normalization based on normalization modes.

    Args:
        norm_modes: List of normalization modes ('iterations', 'dwell time').
        iterations: Number of iterations.
        dwell_time: Dwell time.

    Returns:
        Scaling factor for normalization.
    """
    scaling_factor = 1
    if "iterations" in norm_modes:
        scaling_factor /= iterations
    if "dwell_time" in norm_modes:
        scaling_factor /= dwell_time / 1000  # norm to seconds
    return scaling_factor


def norm_sweep(
    binned_data: np.ndarray,
    bin_edges: list,
    sweep_config: SweepConfig,
    sweep_steps: int,
    lens_k: float,
) -> np.ndarray:
    """
    Normalize sweep data to lens k value.

    Args:
        binned_data: Binned data to normalize.
        bin_edges: Bin edges.
        sweep_config: SweepConfig object containing sweep start and end energy, adjusted channel
         width.
        sweep_steps: Number of steps in sweep.
        lens_k: Lens k value.

    Returns:
        Normalized sweep data.
    """
    # calculate bin centers
    bin_centers = np.array(
        [(bin_edges[i] + bin_edges[i + 1]) / 2 for i in range(len(bin_edges) - 1)]
    )
    center_hits = np.zeros(len(bin_centers))
    # count how often each bin center is hit during
    for i in range(sweep_steps):
        e = sweep_config.sweep_start_energy + i * sweep_config.adjusted_channel_width
        step_min = e * (1 - lens_k / 2)
        step_max = e * (1 + lens_k / 2)
        hits = np.where(
            np.logical_and(bin_centers >= step_min, bin_centers <= step_max)
        )
        for j in hits[0]:
            center_hits[j] += 1
    # fit to linear function
    fit_pars = np.polyfit(bin_centers, center_hits, 1)
    norm_values = np.polyval(fit_pars, bin_centers)
    # normalize data
    return binned_data / norm_values[:, np.newaxis, np.newaxis]
