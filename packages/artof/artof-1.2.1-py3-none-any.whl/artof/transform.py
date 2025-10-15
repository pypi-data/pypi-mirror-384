"""
Module providing a class to transform raw artof data into different formats.
"""

from typing import Union

import numpy as np
from scipy.interpolate import RectBivariateSpline

from .data_read import Acquisition
from .default_bin_config import (
    get_default_e_config,
    get_default_phi_config,
    get_default_t_config,
    get_default_theta_config,
    get_default_xyr_config,
)


def create_matrix_transform(
    p1_0: int, p2_0: int, p1_vec: np.ndarray, p2_vec: np.ndarray, trans_mat: np.ndarray
) -> RectBivariateSpline:
    """
    Transform 2D data point using a given matrix using interpolation through a bivariate spline.

    Args:
        p1_0: Offset of p1.
        p2_0: Offset of p2.
        p1_vec: Vector corresponding to p1 and the columns of the matrix.
        p2_vec: Vector corresponding to p2 and the rows of the matrix.
        trans_mat: 2D list representing the transformation matrix.

    Returns:
        RectBivariateSpline interpolation for given matrix.
    """
    interp = RectBivariateSpline(p2_vec + p2_0, p1_vec + p1_0, trans_mat)
    return interp


class ARTOFTransformer:
    """Class to transform raw artof data"""

    def __init__(self, acquisition: Acquisition, x0: int, y0: int, t0: float):
        """
        Initializer ARTOFTransform class

        Args:
            metadata: Metadata class containing all metadata for current measurement.
            x0: x offset in ticks.
            y0: y offset in ticks.
            t0: t offset in ticks.
        """
        self.tdc_res = acquisition.detector.tdcResolution
        self.e_kin_ref = acquisition.lensmode.eKinRef
        self.lens_k = acquisition.lensmode.lensK
        # save t0 in ticks
        self.t0 = acquisition.detector.t0 if t0 is None else t0
        # create transformations
        self.x_transform, self.y_transform, self.t_transform = self.__ticks_to_si_transform(
            acquisition, x0, y0
        )
        self.e_transform, self.theta_transform = self.__tr_to_e_theta_transform(acquisition)
        # save t_min, and t_max in SI (at reference energy)
        self.t_min, self.t_max = (
            acquisition.lensmode.tofVector[0],
            acquisition.lensmode.tofVector[-1],
        )

    def transform(
        self,
        raw_data: np.ndarray,
        load_as: str,
        center_energy: Union[float, None] = None,
        trigger_period: Union[int, None] = None,
    ) -> np.ndarray:
        """
        Transform raw data to desired representation.

        Args:
            raw_data: 2D list of raw data points (x, y, t ticks).
            load_as: Desired representation to transform to
             (options: 'raw', 'raw_SI', 'cylindrical', 'spherical').
            center_energy: Center energy in eV (required for spherical transformation).
            trigger_period: Period between two trigger. When provided time of flight longer than one
             one trigger period can be loaded.

        Returns:
            Three 2D list of transformed data, list of variable names, and list of default bin edges
             for given transformation.
        """

        match load_as:
            case "raw":
                data = raw_data
            case "raw_SI":
                x, y, t = self.__raw_to_si(raw_data)
                data = np.stack([x, y, t], -1)
            case "cylindrical":
                r, phi, t = self.__raw_to_cylindrical(raw_data)
                data = np.stack([r, phi, t], -1)
            case "spherical":
                if center_energy is None:
                    raise ValueError("Center energy is required for spherical transformation.")
                e, phi, theta = self.__raw_to_spherical(raw_data, center_energy, trigger_period)
                data = np.stack([e, phi, theta], -1)
            case _:
                print(f"Did not recognize transformation of type {load_as}. Using raw data")
                data = raw_data
        return data

    def __raw_to_spherical(
        self, raw_data: np.ndarray, center_energy: float, trigger_period: int = None
    ) -> tuple[any, any, any]:
        """
        Transform raw data to spherical coordinates.

        Args:
            raw_data: 2D list of raw data points (x, y, t ticks).
            center_energy: Center energy in eV.
            trigger_period: Period between two trigger. When provided time of flight longer than one
             one trigger period can be loaded.

        Returns:
            3 lists containing E, phi, and theta values
        """
        energy_scaler = center_energy / self.e_kin_ref

        raw_data = self.__clip_t(raw_data, energy_scaler, trigger_period=trigger_period)
        r, phi, t = self.__raw_to_cylindrical(raw_data)
        t *= np.sqrt(energy_scaler)
        e = self.e_transform.ev(r, t) * energy_scaler
        theta = self.theta_transform.ev(r, t)
        e, phi, theta = self.__clip_e(e, phi, theta, center_energy)
        return e, phi, theta

    def __clip_t(
        self, raw_data: np.ndarray, energy_scaler: float, trigger_period: int = None
    ) -> np.ndarray:
        """
        Clip raw data to t_min and t_max in SI units.

        Args:
            raw_data: 2D list of raw data points (x, y, t ticks).
            energy_scaler: Energy scaler to scale energy and time.
            trigger_period: Period between two trigger. When provided time of flight longer than one
             one trigger period are returned (default None).

        Returns:
            Clipped raw data.
        """
        t_min_raw = self.t_min * self.tdc_res / np.sqrt(energy_scaler) + self.t0
        t_max_raw = self.t_max * self.tdc_res / np.sqrt(energy_scaler) + self.t0
        # # when trigger_period is given, add a second set of data points with t shifted
        # # by trigger_period
        if trigger_period is not None:
            if t_max_raw > trigger_period - self.t0:
                secondary_raw_data = raw_data.copy()
                secondary_raw_data[:, 2] += trigger_period
                raw_data = np.concatenate((raw_data, secondary_raw_data), axis=0)
        return raw_data[(raw_data[:, 2] >= t_min_raw) & (raw_data[:, 2] <= t_max_raw)]

    def __clip_e(self, e: np.ndarray, phi: np.ndarray, theta: np.ndarray, center_energy: float):
        """
        Clip (E, phi, theta) point values to be within lensK window.

        Args:
            e: Energy in eV.
            phi: Phi in radians.
            theta: Theta in radians.

        Returns:
            Clipped E, phi, and theta.
        """
        e_min = center_energy * (1 - self.lens_k / 2)
        e_max = center_energy * (1 + self.lens_k / 2)
        return (
            e[(e >= e_min) & (e <= e_max)],
            phi[(e >= e_min) & (e <= e_max)],
            theta[(e >= e_min) & (e <= e_max)],
        )

    def __raw_to_cylindrical(self, raw_data: np.ndarray) -> tuple[any, any, any]:
        """
        Transform raw data to cylindrical coordinates.

        Args:
            raw_data: 2D list of raw data points (x, y, t ticks).

        Returns:
            Three lists containing r, phi, and t values.
        """
        x, y, t = self.__raw_to_si(raw_data)
        r, phi = self.__xy_to_polar(x, y)
        return r, phi, t

    def __raw_to_si(self, raw_data: np.ndarray) -> tuple[list, list, list]:
        """
        Transform raw data to SI units.

        Args:
            raw_data: 2D list of raw data points (x, y, t ticks).

        Returns:
            Three lists containing x, y, and t values in SI units.
        """
        x = self.x_transform.ev(raw_data[:, 1], raw_data[:, 0])
        y = self.y_transform.ev(raw_data[:, 1], raw_data[:, 0])
        t = self.t_transform(raw_data[:, 2])
        return x, y, t

    def get_axis_and_bins(self, load_as: str, acquisition: Acquisition) -> tuple[list, list]:
        """
        Get axis names and default bin edges for given transformation.

        Args:
            load_as: Desired representation to transform to
             (options: 'raw', 'raw_SI', 'cylindrical', 'spherical').
            metadata: Metadata class containing all metadata for current measurement.
        """
        match load_as:
            case "raw":
                x_bin_conf = get_default_xyr_config(acquisition.detector.spatialDiameter)
                y_bin_conf = get_default_xyr_config(acquisition.detector.spatialDiameter)
                t_bin_conf = get_default_t_config(acquisition, self.t0)

                return ["x_ticks", "y_ticks", "t_ticks"], [
                    x_bin_conf,
                    y_bin_conf,
                    t_bin_conf,
                ]
            case "raw_SI":
                spatial_diameter = acquisition.detector.spatialDiameter
                # implemented based on Igor ARTOFLoader, TODO check if correct
                x_vec_max = acquisition.detector.transformXVector[-1]
                x_matrix_max = max(max(row) for row in acquisition.detector.transformXMatrix)
                x_scaling = x_matrix_max / x_vec_max
                y_vec_max = acquisition.detector.transformYVector[-1]
                y_matrix_max = max(max(row) for row in acquisition.detector.transformYMatrix)
                y_scaling = y_matrix_max / y_vec_max
                x_bin_conf = get_default_xyr_config(spatial_diameter, scaling_factor=x_scaling)
                y_bin_conf = get_default_xyr_config(spatial_diameter, scaling_factor=y_scaling)
                t_bin_conf = get_default_t_config(acquisition, self.t0, si=True)
                return ["x_m", "y_m", "t_s"], [x_bin_conf, y_bin_conf, t_bin_conf]
            case "cylindrical":
                spatial_diameter = acquisition.detector.spatialDiameter
                # implemented based on Igor ARTOFLoader, TODO check if correct
                x_vec_max = acquisition.detector.transformXVector[-1]
                x_matrix_max = max(max(row) for row in acquisition.detector.transformXMatrix)
                x_scaling = x_matrix_max / x_vec_max
                y_vec_max = acquisition.detector.transformYVector[-1]
                y_matrix_max = max(max(row) for row in acquisition.detector.transformYMatrix)
                y_scaling = y_matrix_max / y_vec_max
                r_bin_conf = get_default_xyr_config(
                    spatial_diameter,
                    scaling_factor=max(x_scaling, y_scaling),
                    radius=True,
                )
                phi_bin_conf = get_default_phi_config()
                t_bin_conf = get_default_t_config(acquisition, self.t0, si=True)
                return ["r_m", "phi_rad", "t_s"], [r_bin_conf, phi_bin_conf, t_bin_conf]
            case "spherical":
                e_min = acquisition.general.spectrumBeginEnergy
                e_max = acquisition.general.spectrumEndEnergy
                e_step_size = (
                    acquisition.general.lensLowEdgeEnergyStep
                    if acquisition.general.acquisitionMode == "sweep"
                    else None
                )
                e_bin_conf = get_default_e_config(e_min, e_max, e_step_size=e_step_size)
                phi_bin_conf = get_default_phi_config()
                theta_bin_conf = get_default_theta_config(acquisition.lensmode.maxTheta)
                return ["E_eV", "phi_rad", "theta_rad"], [
                    e_bin_conf,
                    phi_bin_conf,
                    theta_bin_conf,
                ]
            case _:
                raise ValueError(f"Did not recognize transformation of type {load_as}.")

    def __ticks_to_si_transform(
        self, metadata: Acquisition, x0: int = None, y0: int = None
    ) -> tuple:
        """
        Transform x, y, and t from ticks to SI units using transformation matrices and tdcResolution
        from acquisition.cfg file.

        Args:
            metadata: Metadata class containing all metadata for current measurement.
            x0: x offset in ticks (default: from the acquisition.cfg file).
            y0: y offset in ticks (default: from the acquisition.cfg file).

        Returns:
            Three lists containing x, y, and t values in SI units.
        """
        # convert x and y ticks to radius in m and phi in radians
        detector = metadata.detector
        x0 = detector.x0 if x0 is None else x0
        y0 = detector.y0 if y0 is None else y0
        x_transform = create_matrix_transform(
            x0,
            y0,
            detector.transformXVector,
            detector.transformYVector,
            detector.transformXMatrix,
        )
        y_transform = create_matrix_transform(
            x0,
            y0,
            detector.transformXVector,
            detector.transformYVector,
            detector.transformYMatrix,
        )

        # transform time ticks to time in seconds
        def t_transform(t: int):
            return self.__transform_time(t, self.t0, detector.tdcResolution)

        return x_transform, y_transform, t_transform

    def __xy_to_polar(self, x: float, y: float) -> tuple[list, list]:
        """
        Transform x and y in SI units to polar coordinates. The function arctan2(y, x) is used.

        Args:
            x: x value in meters (SI).
            y: y value in meters (SI).

        Returns:
            r in meters and phi in radians.
        """
        r = np.sqrt(x**2 + y**2)
        phi = np.arctan2(y, x)
        return r, phi

    def __tr_to_e_theta_transform(self, metadata: Acquisition) -> tuple[any, any]:
        """
        Transform t and r in SI units to E and theta. The transformation matrices from the
        acquisition.cfg file are used. Warning: Scaling has to be done when evaluting using factor
        centerEnergy/eKinRef.

        Args:
            metadata: Metadata class containing all metadata for current measurement.

        Returns:
            E in eV and theta in radians.
        """
        lensmode = metadata.lensmode
        t_vector = lensmode.tofVector
        r_vector = lensmode.radiusVector
        energy_matrix = lensmode.energyMatrix
        theta_matrix = lensmode.thetaMatrix

        e = create_matrix_transform(0, 0, t_vector, r_vector, energy_matrix)
        theta = create_matrix_transform(0, 0, t_vector, r_vector, theta_matrix)
        return e, theta

    def __transform_time(self, t_raw: int, t0: int, tdc_resolution: float) -> float:
        """
        Transform time from ticks to seconds.

        Args:
            t_raw: Time in ticks.
            t0: Time offset in ticks.
            tdc_resolution: Resolutions of time to digital converter (tdc); number of events per
             second.

        Returns:
            Time in seconds.
        """
        return (t_raw - t0) * 1 / tdc_resolution
