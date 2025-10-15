"""
Module for extracting default binning configurations for artof data.
"""

import numpy as np

from artof.data_read import Acquisition

XYR_POINTS = 101


def get_default_xyr_config(
    spatial_diameter: int, scaling_factor: float = 1, radius: bool = False
) -> list:
    """
    Extract the default x, y or r binning configuration.

    Args:
        spatial_diameter: Spacial diameter of the detector.
        scaling_factor: The scaling factor of the x, y r binning (default is 1). Important for x
            and y in SI units.
        radius: Weather the binning should be in radius or not.

    Returns:
        The default configuration for x, y or r binning configs.
    """
    xyr_min = 0 if radius else (-spatial_diameter / 2) * scaling_factor
    xyr_max = (spatial_diameter / 2) * scaling_factor
    return [xyr_min, xyr_max, XYR_POINTS]


T_UPSCALE_FACTOR = 10
T_MAX_POINTS = 201


def get_default_t_config(aquisition: Acquisition, t0: int, si: bool = False) -> list:
    """
    Extract the default t binning configuration.

    Args:
        metadata: Metadata extracted from acquisition.cfg file
        t0: The t offset.
        si: Weather bin conf should be given in SI units (s).

    Returns:
        The default configuration for t binning configs.
    """
    # extract all neccessary information from metadata
    tof_vector = aquisition.lensmode.tofVector
    energy_matrix = aquisition.lensmode.energyMatrix
    e_ref = aquisition.lensmode.eKinRef
    tdc_res = aquisition.detector.tdcResolution
    e_begin = aquisition.general.spectrumBeginEnergy
    e_end = aquisition.general.spectrumEndEnergy
    t0_tol = aquisition.detector.t0Tolerance

    ## calculate t0 for reference energy from energy matrix at theta=0
    # interpolate for higher precision
    t = np.linspace(tof_vector[0], tof_vector[-1], T_UPSCALE_FACTOR * len(tof_vector))
    e = np.interp(t, tof_vector, energy_matrix[0])
    # find crossing of reference energy and calculate t_0 in ticks
    crossing_idx = next(i for i, x in enumerate(e) if x < e_ref)
    t_0_ref = t[crossing_idx] * tdc_res
    # determine t_0 at spectrum start and end energy
    t_0_end = int(t_0_ref * np.sqrt(e_ref / e_begin))
    t_0_begin = int(t_0_ref * np.sqrt(e_ref / e_end))
    # calculate t_min und t_max based on t_0_tol
    t_min = t_0_begin - t0_tol + t0
    t_max = t_0_end + t0_tol + t0
    # calculate number of points
    t_points = min(T_MAX_POINTS, t_max - t_min)

    # if desired transform into seconds (si)
    if si:
        t_min /= tdc_res
        t_max /= tdc_res

    return [t_min, t_max, t_points]


PHI_MIN = -np.pi
PHI_MAX = np.pi
PHI_POINTS = 201


def get_default_phi_config() -> list:
    """
    Extract the default phi binning configuration.

    Returns:
        The default configuration for phi binning configs.
    """
    return [PHI_MIN, PHI_MAX, PHI_POINTS]


E_POINTS = 101


def get_default_e_config(e_min: float, e_max: float, e_step_size: float = None) -> list:
    """
    Extract the default E binning configuration.

    Args:
        e_min: The minimum value of the E binning from acquisition.cfg.
        e_max: The maximum value of the E binning from acquisition.cfg.
        e_step_size: The step size of the E binning e from acquisition.cfg for sweep mode.
            Default is None and therefore E_POINTS will be used.

    Returns:
        The default configuration for E binning configs.
    """
    e_points = E_POINTS if e_step_size is None else int((e_max - e_min) / e_step_size) + 1

    return [e_min, e_max, e_points]


THETA_MIN = 0
THETA_POINTS = 201


def get_default_theta_config(theta_max: float) -> list:
    """
    Extract the default theta binning configuration.

    Args:
        theta_max: The maximum theta value from acquisition.cfg.

    Returns:
        The default configuration for theta binning configs.
    """
    return [THETA_MIN, theta_max, THETA_POINTS]
