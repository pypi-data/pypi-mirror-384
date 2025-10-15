"""Module for loading and processing pump-probe data.

This module provides functionality to load and process pump-probe data from specified directories.
"""

from enum import Enum
from typing import Union

import numpy as np
from plotly import graph_objects as go

from artof.artof_utils import print_progress
from artof.base_loader import BaseLoader, TransformFormat
from artof.data_process import calc_step_norm, get_axis_values
from artof.nexus_export import export_nx_mpes
from artof.plotting import plot_2d


class DelayAxis(Enum):
    """
    Enum for delay axis types.
    - REVOLUTION: Delay axis of the synchrotron revolutions.
    - STAGE: Delay axis of the sample stage (f.e. delay stage, laser settings).

    """

    REVOLUTION = "revolution"
    STAGE = "stage"


class PumpProbeLoader:
    """
    Class for loading and processing pump-probe data.
    """

    def __init__(
        self,
        directory: str,
        run_prefix: str,
        start_run: int,
        stop_run: int,
        transform_format: TransformFormat,
        t0: float,
        trigger_period: float,
        x0: Union[int, None] = None,
        y0: Union[int, None] = None,
    ):
        """
        Initialize PumpProbeLoader class.

        Args:
            - directory: Path to the root directory containing all pumb-probe runs.
            - run_prefix: Prefix for the run directories (e.g., "Run_").
            - start_run: The starting run number (inclusive).
            - stop_run: The stopping run number (exclusive).
            - transform_format: Format to load the data in
                - `raw`: Load raw data in ticks (x,y,t).
                - `raw_SI`: Load raw data in SI units (x: m, y: m, t: s).
                - `cylindrical`: Load data in cylindrical coordinates (r: m, phi: rad, t: s).
                - `spherical`: Load data in spherical coordinates and associated energy
                    (E: eV, theta: rad, phi: rad).
            - x0: Offset for x ticks, optional (default extracted from acquisition.cfg).
            - y0: Offset for y ticks, optional (default extracted from acquisition.cfg).
            - t0: t0 corresponding to the excitation iteration in ticks.
            - trigger_period: Period of the trigger in ticks.
        """

        self.dir = directory
        self.run_prefix = run_prefix
        self.start_run = start_run
        self.stop_run = stop_run
        self.t0 = t0
        self.trigger_period = trigger_period
        self.stage_delay_map = None
        self.iter_delay_map = None
        self.fig = None
        self.transform_format = transform_format

        self.progress_info = None
        self.rev_proj_axes = None
        self.stage_proj_axes = None
        self.rev_ax_values = None
        self.stage_ax_values = None
        self.rev_bin_edges = None
        self.stage_bin_edges = None
        self.rev_delay_edges = None
        self.stage_delay_edges = None
        self.bin_info_logged = False
        self.revolution_delay_map = None
        self.stage_delay_map = None

        self.loaders = []

        for run_num in range(start_run, stop_run):
            run_path = f"{self.dir}/{self.run_prefix}{str(run_num).zfill(3)}"
            loader = BaseLoader(run_path, transform_format, t0=t0, x0=x0, y0=y0)
            self.loaders.append(loader)

        self.x0 = self.loaders[0].x0
        self.y0 = self.loaders[0].y0

    def process_revolution_delay(
        self,
        proj_ax: int,
        run_num: int,
        rev_interval: Union[tuple, None] = None,
        iter_interval: Union[tuple, None] = None,
        cust_bin_confs=None,
        norm_modes: Union[list, None] = None,
        wrap_low_energy: bool = False,
        trigger_period: Union[int, None] = None,
        multithreading: bool = True,
    ):
        """
        Load, transform and bin pump-probe data along the synchrotron revolution delay axis.

        Args:
            proj_ax: Axis to project the data onto for each delay.
            run_num: The run number to load data from.
            rev_interval: Tuple specifying the range of revolutions to load (start inc., stop exc.).
            iter_interval: Tuple specifying the range of iterations to load (start inc., stop exc.).
                If None, all iterations are loaded.
            cust_bin_confs: List of 3 custom binning configurations for the 3 parameters
                [min, max, edges]. F.e.: [[-1500, 1500, 101], [-1500, 1500, 101],
                [12000, 18000, 201]]
            norm_modes: Normalization mode for binned data ('iterations', 'dwell_time', 'sweep').
                Default is None.
                - `iterations`: Normalize data by number of iterations.
                - `dwell_time`: Normalize data by dwell time.
                - `sweep`: Normalize data by changing window size of sweep data.
            wrap_low_energy: Wrap low energy values to high energy values (default False). If True,
                the trigger period is read from 'timing.txt' file unless provided as
                `trigger_period`.
            trigger_period: Period between two trigger. When provided time of flight longer than one
                one trigger period can be loaded (default None).
            multithreading: Use multithreading for data loading (default True).
        """

        if run_num < self.start_run or run_num >= self.stop_run:
            raise ValueError(
                f"Run number {run_num} is out of range ({self.start_run}, {self.stop_run})"
            )

        loader_idx = run_num - self.start_run
        cur_loader = self.loaders[loader_idx]

        if iter_interval is not None:
            cur_loader.set_iter_interval(iter_interval[0], iter_interval[1])

        start_rev, stop_rev = rev_interval if rev_interval else (-1, 206)

        # setup progress info
        self.progress_info = {
            "name": "Runs",
            "current": 0,
            "total": (stop_rev - start_rev),
        }
        print_progress(self.progress_info)

        self.bin_info_logged = False
        delay_list = []
        bin_edges = None
        for i in range(start_rev, stop_rev):
            # Last revolution appears at -2 because trigger resets before
            i = -2 if i == 205 else i

            new_t0 = self.t0 + i * self.trigger_period
            bin_edges, counts = self.__process_delay_step(
                proj_ax,
                cur_loader,
                new_t0,
                cust_bin_confs,
                norm_modes,
                wrap_low_energy,
                trigger_period,
                multithreading,
            )
            delay_list.append(counts)

        # overwriting of loading message
        print()

        self.rev_proj_axes = proj_ax
        self.rev_bin_edges = bin_edges
        self.revolution_delay_map = np.array(delay_list)

        # calculate delay values and edges (in s)
        ticks_to_s = 1 / self.loaders[0].metadata.acquisition.detector.tdcResolution
        self.rev_ax_values = [
            ticks_to_s * (self.t0 + i * self.trigger_period) for i in range(start_rev, stop_rev)
        ]
        self.rev_delay_edges = [
            ticks_to_s * (self.t0 + (i - 0.5) * self.trigger_period)
            for i in range(start_rev, stop_rev + 1)
        ]

    def process_stage_delay(
        self,
        proj_ax: int,
        revolution: int,
        delay_range: tuple,
        run_interval: Union[tuple, None] = None,
        iter_interval: Union[tuple, None] = None,
        cust_bin_confs=None,
        norm_modes: Union[list, None] = None,
        wrap_low_energy: bool = False,
        trigger_period: Union[int, None] = None,
        multithreading: bool = True,
    ):
        """
        Load, transform and bin pump-probe data along the synchrotron revolution delay axis.

        Args:
            proj_ax: Axis to project the data onto for each delay.
            revolution: The revolution number to load data from.
            delay_range: Tuple specifying the range of delay steps in seconds to load
                (start inc., stop inc.).
            run_interval: Tuple specifying the range of runs to load (start inc., stop exc.).
            iter_interval: Tuple specifying the range of iterations to load for each run
                (start inc., stop exc.). If None, all iterations are loaded.
            cust_bin_confs: List of 3 custom binning configurations for the 3 parameters
                [min, max, edges]. F.e.: [[-1500, 1500, 101], [-1500, 1500, 101],
                [12000, 18000, 201]]
            norm_modes: Normalization mode for binned data ('iterations', 'dwell_time', 'sweep').
                Default is None.
                - `iterations`: Normalize data by number of iterations.
                - `dwell_time`: Normalize data by dwell time.
                - `sweep`: Normalize data by changing window size of sweep data.
            wrap_low_energy: Wrap low energy values to high energy values (default False). If True,
                the trigger period is read from 'timing.txt' file unless provided as
                `trigger_period`.
            trigger_period: Period between two trigger. When provided time of flight longer than one
                one trigger period can be loaded (default None).
            multithreading: Use multithreading for data loading (default True).
        """

        if revolution < -1 or revolution > 206:
            raise ValueError(f"Revolution number {revolution} is out of range (-1, 206)")
        # Last revolution appears at -2 because trigger resets before
        revolution = -2 if revolution == 205 else revolution
        new_t0 = self.t0 + revolution * self.trigger_period

        if run_interval is None:
            run_interval = (self.start_run, self.stop_run)

        # setup progress info
        self.progress_info = {
            "name": "Runs",
            "current": 0,
            "total": (run_interval[1] - run_interval[0]),
        }
        print_progress(self.progress_info)

        self.bin_info_logged = False
        delay_list = []
        bin_edges = None
        for run_num in range(*run_interval):
            loader_idx = run_num - self.start_run
            cur_loader = self.loaders[loader_idx]

            if iter_interval is not None:
                cur_loader.set_iter_interval(iter_interval[0], iter_interval[1])

            bin_edges, counts = self.__process_delay_step(
                proj_ax,
                cur_loader,
                new_t0,
                cust_bin_confs,
                norm_modes,
                wrap_low_energy,
                trigger_period,
                multithreading,
            )
            delay_list.append(counts)

        # overwriting of loading message
        print()

        self.stage_proj_axes = proj_ax
        self.stage_bin_edges = bin_edges
        self.stage_delay_map = np.array(delay_list)

        # calculate delay values and edges (in s)
        full_stage_ax_values = np.linspace(
            delay_range[0], delay_range[1], self.stop_run - self.start_run
        )
        delta_delay = full_stage_ax_values[1] - full_stage_ax_values[0]
        full_stage_ax_edges = np.linspace(
            delay_range[0] - 0.5 * delta_delay,
            delay_range[1] - delta_delay * 0.5,
            self.stop_run - self.start_run + 1,
        )
        ## limit values to the current run interval
        self.stage_ax_values = full_stage_ax_values[
            run_interval[0] - self.start_run : run_interval[1] - self.start_run
        ]
        self.stage_delay_edges = full_stage_ax_edges[
            run_interval[0] - self.start_run : run_interval[1] - self.start_run + 1
        ]

    def plot_revolution_delay(
        self, norm_step_size: bool = False, width: int = 600, height: int = 600
    ):
        """
        Plot the revolution delay map.

        Args:
            norm_step_size: Whether to normalize the step size (default False).
            width: Width of the plot in pixels (default 600).
            height: Height of the plot in pixels (default 600).

        """
        if self.revolution_delay_map is None or self.rev_bin_edges is None:
            raise ValueError(
                "Revolution delay map is not processed yet. Call process_revolution_data first."
            )

        data = self.revolution_delay_map.copy()
        bin_edges = self.rev_bin_edges[self.rev_proj_axes : self.rev_proj_axes + 1]
        if norm_step_size:
            self._norm_step_size(data, bin_edges)

        self.fig = go.Figure(layout=go.Layout(width=width, height=height))

        plot_2d(
            self.fig,
            {"0": data},
            bin_edges[0],
            self.rev_delay_edges,
            self.loaders[0].ax_names + ["Delay_s"],
            [self.rev_proj_axes, -1],
            height,
            title="Revolution Delay Map",
        )
        self.fig.show()

    def plot_stage_delay(self, norm_step_size: bool = False, width: int = 600, height: int = 600):
        """
        Plot the stage delay map.

        Args:
            norm_step_size: Whether to normalize the step size (default False).
            width: Width of the plot in pixels (default 600).
            height: Height of the plot in pixels (default 600).

        """
        if self.stage_delay_map is None or self.stage_bin_edges is None:
            raise ValueError("Stage delay map is not processed yet. Call process_stage_data first.")

        data = self.stage_delay_map.copy()
        bin_edges = self.stage_bin_edges[self.stage_proj_axes : self.stage_proj_axes + 1]
        if norm_step_size:
            self._norm_step_size(data, bin_edges)

        self.fig = go.Figure(layout=go.Layout(width=width, height=height))

        plot_2d(
            self.fig,
            {"0": data},
            bin_edges[0],
            self.stage_delay_edges,
            self.loaders[0].ax_names + ["Delay_s"],
            [self.stage_proj_axes, -1],
            height,
            title="Stage Delay Map",
        )
        self.fig.show()

    def __process_delay_step(
        self,
        proj_ax: int,
        loader: BaseLoader,
        t0: float,
        custom_bin_confs: Union[list, None],
        norm_modes: Union[list, None],
        wrap_low_energy: bool,
        trigger_period: Union[int, None],
        multithreading: bool,
    ) -> tuple[list, list]:
        """
        Process a single delay step for the given loader.

        Args:
            proj_ax: Axis to project the data onto for each delay.
            loader: The BaseLoader instance to process data from.
            t0: offset for the delay step in ticks.
            custom_bin_confs: List of 3 custom binning configurations for the 3 parameters
                [min, max, edges]. F.e.: [[-1500, 1500, 101], [-1500, 1500, 101],
                [12000, 18000, 201]]
            norm_modes: Normalization mode for binned data ('iterations', 'dwell_time', 'sweep').
                Default is None.
            multithreading: Use multithreading for data loading (default True).

        Returns:
            Binned data counts for the specified projection axis.

        """
        loader.setup_data_vars(t0=t0)
        # transform data
        transformed_data = loader.load_and_transform(
            multithreading,
            wrap_low_energy=wrap_low_energy,
            trigger_period=trigger_period,
            logging=False,
        )
        loader.add_transformed_data(transformed_data)
        # bin data
        loader.set_bin_configs(custom_bin_confs, logging=not self.bin_info_logged)
        self.bin_info_logged = True
        binned_data = loader.bin(loader.transformed_data, norm_modes)
        loader.add_binned_data(binned_data)
        # project data
        _, counts = loader.get_binned_data([proj_ax])
        # update progress
        self.progress_info["current"] += 1
        print_progress(self.progress_info)

        return loader.bin_edges, counts

    def get_stage_delay(self, norm_step_size: bool = False) -> np.ndarray:
        """
        Get the stage delay data.

        Args:
            norm_step_size: Whether to normalize the data with step size (default False).

        Returns:
            Numpy array of the stage delay map.
        """
        data = self.stage_delay_map.copy()
        if norm_step_size:
            bin_edges = self.stage_bin_edges[self.stage_proj_axes : self.stage_proj_axes + 1]
            self._norm_step_size(data, bin_edges)
        return data

    def get_revolution_delay(self, norm_step_size: bool = False) -> np.ndarray:
        """
        Get the stage delay data.

        Args:
            norm_step_size: Whether to normalize the data with step size (default False).

        Returns:
            Numpy array of the stage delay map.
        """
        data = self.revolution_delay_map.copy()
        if norm_step_size:
            bin_edges = self.rev_bin_edges[self.rev_proj_axes : self.rev_proj_axes + 1]
            self._norm_step_size(data, bin_edges)
        return data

    def export_stage_delay(
        self,
        path: str,
        file_format: str,
        norm_step_size: bool = False,
        delimiter: str = ",",
    ):
        """
        Export stage delay data to file in 'csv' or 'hdf5' format. If 'csv' is chosen, the data is
        needs to be projected at least along one axis.

        Args:
            path: Path to which the data is saved. Including filename but excluding extension.
            file_format: Format of the file to which the data is saved ('csv' or 'nxs').
            proj_axes: List containing all axes onto which the projection is performed, e.g., [0,1].
                Default None, the data is not projected and saved as is (only for 'hdf5').
            ranges: List containing ranges for axes (e.g., [[50, 101], [0,50], None]), if
                None entire range of axes is used (default entire range of each axis).
            norm_step_size: Normalize data with step size before exporting (default False).
            delimiter: Delimiter by which the data is separated for format 'csv' (default ',').
        """

        axes_names = ["Delay_s", self.loaders[0].ax_names[self.stage_proj_axes]]
        bin_edges = [self.stage_delay_edges, self.stage_bin_edges[self.stage_proj_axes]]
        axes_values = get_axis_values(bin_edges, axes_names)
        data = self.stage_delay_map.copy()

        self._export_delay_map(
            data, path, file_format, bin_edges, axes_names, axes_values, norm_step_size, delimiter
        )

    def export_revolution_delay(
        self,
        path: str,
        file_format: str,
        norm_step_size: bool = False,
        delimiter: str = ",",
    ):
        """
        Export revolution delay data to file in 'csv' or 'hdf5' format. If 'csv' is chosen, the data
        is needs to be projected at least along one axis.

        Args:
            path: Path to which the data is saved. Including filename but excluding extension.
            file_format: Format of the file to which the data is saved ('csv' or 'nxs').
            proj_axes: List containing all axes onto which the projection is performed, e.g., [0,1].
                Default None, the data is not projected and saved as is (only for 'hdf5').
            ranges: List containing ranges for axes (e.g., [[50, 101], [0,50], None]), if
                None entire range of axes is used (default entire range of each axis).
            norm_step_size: Normalize data with step size before exporting (default False).
            delimiter: Delimiter by which the data is separated for format 'csv' (default ',').
        """

        if file_format not in ["csv", "nxs"]:
            raise ValueError("File format must be 'csv' or 'nxs'.")

        axes_names = ["Delay_s", self.loaders[0].ax_names[self.rev_proj_axes]]
        bin_edges = [self.rev_delay_edges, self.rev_bin_edges[self.rev_proj_axes]]
        axes_values = get_axis_values(bin_edges, axes_names)
        data = self.revolution_delay_map.copy()

        self._export_delay_map(
            data, path, file_format, bin_edges, axes_names, axes_values, norm_step_size, delimiter
        )

    def _export_delay_map(
        self,
        data: np.ndarray,
        path: str,
        file_format: str,
        bin_edges: list,
        axes_names: list,
        axes_values: list,
        norm_step_size: bool = False,
        delimiter: str = ",",
    ) -> None:
        """
        Export delay map data to file.

        Args:
            data: Delay map data to export.
            path: Path to which the data is saved. Including filename but excluding extension.
            file_format: Format of the file to which the data is saved ('csv' or 'nxs').
            bin_edges: List of bin edges for delay and projection axes.
            axes_names: List of axis names.
            axes_values: List of axis values for delay and projection axes.
            norm_step_size: Normalize data with step size before exporting (default False).
            delimiter: Delimiter by which the data is separated for format 'csv' (default ',').
        """

        if file_format not in ["csv", "nxs"]:
            raise ValueError("File format must be 'csv' or 'nxs'.")

        if norm_step_size:
            self._norm_step_size(data, bin_edges[1:])

        if file_format == "csv":
            header = f"# x0: {self.x0}, y0: {self.y0}, t0: {self.t0}"
            for ax_values, ax_name in zip(axes_values, axes_names):
                values_str = ", ".join([str(v) for v in ax_values])
                header += f"\n# {ax_name}: {values_str}"

            np.savetxt(
                f"{path}.csv",
                data,
                delimiter=delimiter,
                header=header,
                comments="",
            )
        elif file_format == "nxs":
            loader = self.loaders[0]
            export_nx_mpes(
                path,
                data,
                axes_names,
                axes_values,
                loader.acquisition_mode,
                loader.metadata,
            )

    def _norm_step_size(self, data, bin_edges):
        """
        Normalize the data with respect to the step size defined by the bin edges.

        Args:
            data: The data to normalize.
            bin_edges: All bin edges defining the step size (no delay bin edges).
        """

        norm_factor = calc_step_norm(bin_edges, None)
        data /= norm_factor
