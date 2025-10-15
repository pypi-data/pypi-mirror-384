"""
This module contains functions to create bin edges, project data, and calculate axis values.
"""

from typing import Union

import numpy as np


def get_bin_edges(bin_config: list, data_id: str = "unknown") -> np.ndarray:
    """
    Create bin edges (limits) for given bin config.

    Args:
        bin_config: Bin config consisting of three values: [min, max, points].
        data_id: Identifier to raise error message with identifier.

    Returns:
        List of bin edges.

    Raises:
        ValueError: If the number of bins is not given as an int.
    """
    min_point, max_point, total_points = bin_config
    if not isinstance(total_points, int):
        raise ValueError(f"The number of bins for {data_id} needs given as an int")

    bin_size = (max_point - min_point) / (total_points - 1)
    # create bin edges in a way that bin centers are min and max
    return np.linspace(min_point - bin_size / 2, max_point + bin_size / 2, total_points + 1)


def wrap_angle(axis: int, angle: float, transformed_data: dict) -> dict:
    """
    Wrap all values that are within the range of pi - angle to -pi - angle. A copy of data is
    created.

    Args:
        axis: Axis to wrap.
        angle: Angle in radians to wrap the data.
        transformed_data: Dictionary containing transformed data.

    Returns:
        Dictionary with wrapped transformed data.
    """
    transformed_data = transformed_data.copy()
    for cur_data in transformed_data.values():
        cur_data[:, axis] = (cur_data[:, axis] + np.pi + angle) % (2 * np.pi) - np.pi - angle
    return transformed_data


def project_data(
    data: np.ndarray,
    bin_edges: list,
    proj_axes: Union[None, list],
    ranges: list,
    norm_step_size: bool,
) -> np.ndarray:
    """
    Project data onto given axes. Projections are possible in 1 or 2 dimensions.

    Args:
        data: 3D data to be projected.
        bin_edges: List of bin edges for each axis.
        proj_axes: List containing all axes onto which the projection is performed, e.g., [0,1].
        ranges: List of ranges for each axis.
        norm_step_size: Normalize projection with step size.

    Returns:
        Axes values and list containing the projection (1 or 2D).

    Raises:
        RuntimeError: If data is not loaded before projection.
        ValueError: If the number of projection axes is not 1 or 2.
        ValueError: If the projection axes are not valid.
    """

    if data is None:
        raise RuntimeError("Load and bin the data before projecting the data.")
    if proj_axes is not None:
        if len(proj_axes) not in [1, 2]:
            raise ValueError("Projecting data along more than 2 axes is not possible.")
        if len(proj_axes) > 3 or min(proj_axes) < 0 or max(proj_axes) > 2:
            raise ValueError("Invalid axes. Choose between 0, 1, 2.")

    # determine ranges (None is entire range) and reshape data
    start_1, end_1 = (0, data.shape[0]) if ranges[0] is None else (ranges[0][0], ranges[0][1])
    start_2, end_2 = (0, data.shape[1]) if ranges[1] is None else (ranges[1][0], ranges[1][1])
    start_3, end_3 = (0, data.shape[2]) if ranges[2] is None else (ranges[2][0], ranges[2][1])
    proj_data = data[start_1:end_1, start_2:end_2, start_3:end_3]

    # project data onto 1 or 2 axes, if proj_axes is None do not project
    if proj_axes is None:
        pass
    elif len(proj_axes) == 2:  # project data onto 2 axes
        # determine the projection axis
        other_axis = 3 - sum(proj_axes)
        # switch order of array if needed
        if proj_axes[0] < proj_axes[1]:
            proj_data = np.swapaxes(proj_data, proj_axes[0], proj_axes[1])
        proj_data = proj_data[:, :, :].sum(axis=other_axis)
    elif len(proj_axes) == 1:  # project data onto 1 axis
        # get axes to project along
        other_axes = [0, 1, 2]
        other_axes.remove(proj_axes[0])
        # project along axes
        proj_data = proj_data.sum(axis=tuple(other_axes))
        # calculate axes values

    # normalize data with step size if desired
    if norm_step_size:
        step_size_product = calc_step_norm(bin_edges, proj_axes)
        proj_data /= step_size_product

    return proj_data


def calc_step_norm(bin_edges: list, proj_axes: Union[None, list]) -> float:
    """
    Calculate normalization factor based on bin edges and projection axes.

    Args:
        bin_edges: List of bin edges for each axis.
        proj_axes: List of axes to project onto.

    Returns:
        Normalization factor.
    """
    step_size_product = 1
    if proj_axes is None:
        proj_axes = np.arange(len(bin_edges))
    for i in proj_axes:
        step_size_product *= bin_edges[i][1] - bin_edges[i][0]
    return step_size_product


def get_axis_values(bin_edges: list, axes: list, photon_energy: float = None) -> list[np.ndarray]:
    """
    Calculate axis values from bin edges.

    Args:
        bin_edges: List of bin edges for each axis.
        axes: List of axes names.
        photon_energy: Photon energy in eV for binding energy, optional (default is None).
    """

    # calculate axes values
    axes_values = []

    for i in range(len(axes)):
        axes_values.append(
            np.array(
                [(bin_edges[i][j] + bin_edges[i][j + 1]) / 2 for j in range(len(bin_edges[i]) - 1)]
            )
        )

    if photon_energy is not None and "E_eV" in axes:
        axes_values[0] = [photon_energy - energy for energy in axes_values[0]]

    return axes_values
