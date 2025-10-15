"""Module containing ARTOFLoader class for loading and processing artof data.

The ARTOFLoader class is used to load and process artof data from a specified directory.
"""

from typing import Union

import pandas as pd
import plotly.graph_objects as go
from IPython.display import display

from .base_loader import BaseLoader, TransformFormat
from .data_process import get_axis_values, project_data
from .plotting import plot_1d, plot_2d, plot_counts


class ARTOFLoader:
    """
    Class for loading and processing artof data.
    """

    def __init__(
        self,
        path: str,
        transform_format: TransformFormat,
        x0: Union[float, None] = None,
        y0: Union[float, None] = None,
        t0: Union[float, None] = None,
        sweep_type: str = "Scienta",
    ):
        """
        Initialize ARTOFLoader class.

        Args:
            path: Path to run directory.
            transform_format: Format to load data in:
                - `raw`: Load raw data in ticks (x,y,t).
                - `raw_SI`: Load raw data in SI units (x: m,y: m,t: s).
                - `cylindrical`: Load data in cylindrical coordinates (r: m, phi: rad, t: s).
                - `spherical`: Load data in spherical coordinates and associated energy
                    (E: eV, theta: rad, phi: rad).
            x0: Offset for x ticks, optional (default extracted from acquisition.cfg).
            y0: Offset for y ticks, optional (default extracted from acquisition.cfg).
            t0: Offset for t ticks, optional (default extracted from acquisition.cfg).
            sweep_type: Sweep type ('Scienta' or 'normal'), optional (default 'Scienta').
        """
        self.base_loader = BaseLoader(path, transform_format, x0, y0, t0, sweep_type)
        self.fig = None

    def transform_data(
        self,
        iter_interval: Union[tuple, None] = None,
        wrap_low_energy: bool = False,
        trigger_period: Union[int, None] = None,
        multithreading: bool = True,
    ):
        """
        Load artof data for run in directory and transform into desired format.

        Args:
            iter_interval: Tuple of start (including) and stop (excluding) lens iteration to load
                (default None, load all).
            wrap_low_energy: Wrap low energy values to high energy values (default False). If True,
                the trigger period is read from 'timing.txt' file unless provided as
                `trigger_period`.
            trigger_period: Period between two trigger. When provided time of flight longer than one
                one trigger period can be loaded (default None).
            multithreading: Use multithreading for data loading (default True).
        """
        # reset loader
        self.base_loader.setup_data_vars()

        if iter_interval:
            self.base_loader.set_iter_interval(iter_interval[0], iter_interval[1])
        transformed_data = self.base_loader.load_and_transform(
            multithreading, wrap_low_energy=wrap_low_energy, trigger_period=trigger_period
        )
        self.base_loader.add_transformed_data(transformed_data)

        self.base_loader.print_transform_stats()

    def bin_data(
        self,
        cust_bin_confs=None,
        norm_modes: Union[list, None] = None,
        win_config: Union[tuple[int, int], None] = None,
    ):
        """
        Bin loaded data into 3D histogram.

        Args:
            cust_bin_confs: List of 3 custom binning configurations for the 3 parameters
                [min, max, edges]. F.e.: [[-1500, 1500, 101], [-1500, 1500, 101],
                [12000, 18000, 201]]
            norm_modes: Normalization mode for binned data ('iterations', 'dwell_time', 'sweep').
                Default is None.
                - `iterations`: Normalize data by number of iterations.
                - `dwell_time`: Normalize data by dwell time.
                - `sweep`: Normalize data by changing window size of sweep data.
            win_config: Tuple of (window size, step size) for sweep data (default None, one window)
                If the last window is smaller than the step size, it will be ignored.


        Raises:
            Exception: If data is not loaded before binning.
        """
        # reset binned data from previous binning # pyright: disable=attribute-defined-outside-init
        # TODO pass argument to BaseLoader to reset binned data
        self.base_loader.binned_data = {}

        # set binning configurations
        self.base_loader.set_bin_configs(cust_bin_confs)

        binned_data = self.base_loader.bin(
            self.base_loader.transformed_data, norm_modes, win_config=win_config
        )
        self.base_loader.add_binned_data(binned_data)

        # print windows if win_config is given
        if win_config is not None:
            print(
                f"The following {len(self.base_loader.binned_data)} window(s) were"
                f" created: {list(self.base_loader.binned_data.keys())}"
            )

    def plot(
        self,
        proj_axes: list,
        ranges=None,
        norm_step_size: bool = False,
        photon_energy: float = None,
        width: int = 600,
        height: int = 600,
    ):
        """
        Plot loaded data as projection onto given axes. Projections are possible onto 1 or 2 axes.

        Args:
            proj_axes: List containing all axes onto which the projection is performed, e.g., [0,1].
            ranges: List containing ranges for axes (e.g., [[50, 101], [0,50], None]), if None
                entire range of axes is used (default entire range of each axis).
            norm_step_size: Normalize data with step size before plotting (default False).
            photon_energy: Photon energy to plot in binding energy, optional (default None).
            width: Width of plot (default 600).
            height: Height of plot (default 600).

        Raises:
            ValueError: An incorrect number of projection axes provided.
        """

        if self.base_loader.bin_edges is None:
            raise RuntimeError("Data not binned. Please bin data before plotting.")

        if len(proj_axes) not in [1, 2]:
            raise ValueError(f"A projection along {len(proj_axes)} axes is not possible.")

        if ranges is None:
            ranges = [None, None, None]

        proj_data_wins = {}
        for win_id, data in self.base_loader.binned_data.items():
            proj_data_wins[win_id] = project_data(
                data, self.base_loader.bin_edges, proj_axes, ranges, norm_step_size
            )

        self.fig = go.Figure(layout=go.Layout(width=width, height=height))

        fig_title = (
            f"Projection onto"
            f" {' & '.join([self.base_loader.ax_names[i].split('_')[0] for i in proj_axes])} in"
            f" {self.base_loader.transform_format}-format"
        )
        if len(proj_axes) == 2:  # plot data in 2D as heatmap
            plot_2d(
                self.fig,
                proj_data_wins,
                self.base_loader.bin_edges[proj_axes[0]],
                self.base_loader.bin_edges[proj_axes[1]],
                self.base_loader.ax_names,
                proj_axes,
                photon_energy,
                height,
                title=fig_title,
            )
        elif len(proj_axes) == 1:  # plot data in 1D as line
            x_data = get_axis_values(
                self.base_loader.bin_edges, self.base_loader.ax_names, photon_energy
            )[proj_axes[0]]
            plot_1d(
                self.fig,
                x_data,
                proj_data_wins,
                self.base_loader.ax_names,
                proj_axes,
                photon_energy,
                height,
                title=fig_title,
            )

        self.fig.show()

    def load_counts(
        self, sum_iters: bool = False, start_step: tuple = None, stop_step: tuple = None
    ):
        """
        Load counts of all measured events.

        Args:
            sum_iters: Sum counts of each iteration, instead of returning counts for each step. Only
                relevant for sweeps. (default False)
            start_step: Start step of the lens iteration (iter, step) (including)
                (default None, start from first step)
            stop_step: Stop step of the lens iteration (iter, step) (excluding)
                (default None, stop at last step)

        """
        # if mode 'fix', set sum_iters to True
        if self.base_loader.acquisition_mode == "fix":
            sum_iters = True

        # save sum iters for plotting
        self.base_loader.sum_iters = sum_iters

        # reset counts from previous loading
        self.base_loader.setup_counts_vars()
        self.base_loader.add_event_counts(
            self.base_loader.count_events(
                sum_iters=sum_iters, start_step=start_step, stop_step=stop_step
            )
        )

    def plot_counts(self, iter_range: list = None, width: int = 600, height: int = 600):
        """
        Plot counts of all measured events over iterations in given range.

        Args:
            range: Range of iterations to plot (def+ault None, plot all).
            width: Width of plot (default 600).
            height: Height of plot (default 600).
        """

        iterations, counts = self.base_loader.get_event_counts(iter_range)

        # create plot
        self.fig = go.FigureWidget(layout=go.Layout(width=width, height=height))
        display(self.fig)

        plot_counts(self.fig, iterations, counts, self.base_loader.sum_iters)

    def get_binned_data(
        self,
        proj_axes: list = None,
        ranges=None,
        norm_step_size: bool = False,
    ) -> tuple[list, list]:
        """
        Project loaded data onto given axes. Projections are possible onto 1 or 2 axes.

        Args:
            proj_axes: List containing all axes onto which the projection is performed, e.g., [0,1].
            ranges: List containing ranges for axes (e.g., [[50, 101], [0,50], None]), if
                None entire range of axes is used (default entire range of each axis).
            norm_step_size: Normalize data with step size before plotting (default False).

        Returns:
            Axes values and list containing the projection (1 or 2D).
        """
        return self.base_loader.get_binned_data(proj_axes, ranges, norm_step_size)

    def export(
        self,
        path: str,
        file_format: str,
        proj_axes: Union[list, None] = None,
        ranges=None,
        norm_step_size: bool = False,
        eln_path: Union[str, None] = None,
        delimiter: str = ",",
    ):
        """
        Export loaded data to file in 'csv' or 'nxs' format. If 'csv' is chosen, the data is needs
        to be projected at least along one axis.

        Args:
            path: Path to which the data is saved. Including filename but excluding extension.
            file_format: Format of the file to which the data is saved ('csv' or 'hdf5').
            proj_axes: List containing all axes onto which the projection is performed, e.g., [0,1].
                Default None, the data is not projected and saved as is (only for 'hdf5').
            ranges: List containing ranges for axes (e.g., [[50, 101], [0,50], None]), if
                None entire range of axes is used (default entire range of each axis).
            norm_step_size: Normalize data with step size before export (default False).
            eln_path: NeXus only: path to the ELN file where the metadata is stored. If None,
                standard metadata is used (default None, only relevant for 'hdf5' export).
            delimiter: Delimiter by which the data is separated (default ',').
        """

        self.base_loader.export(
            path, file_format, proj_axes, ranges, norm_step_size, eln_path, delimiter
        )

    def get_event_counts(self, iter_range: list = None) -> tuple[list | list]:
        """
        Get the iterations and the corresponding counts.

        Args:
        iter_range: Range of iterations to be exported (default None, all iterations).

        Returns:
            Tuple containing the iterations and the corresponding counts.
        """
        self.base_loader.get_event_counts(iter_range)

    def export_counts_to_csv(self, path: str, iter_range: list = None, delimiter: str = ","):
        """
        Export event counts to csv file.

        Args:
            path: Path to which the data is saved. Including filename but excluding extension (csv).
            iter_range: Range of iterations to be exported (default None, all iterations).
            delimiter: Delimiter by which the data is separated (default ',').
        """
        self.base_loader.export_counts_to_csv(path, iter_range, delimiter)

    def log_metadata(self, pars: list = None) -> pd.DataFrame:
        """
        Get metadata of loaded data.

        Args:
            pars: List of keys to be extracted from metadata (when 'None' all metadata will
             be returned), optional. Default is `['analyzer.lensMode', 'analyzer.elementSet',
             'analyzer.passEnergy', 'general.lensIterations', 'general.lensDwellTime',
             'general.spectrumBeginEnergy', 'general.spectrumEndEnergy', 'general.centerEnergy',
             'detector.t0', 'detector.t0Tolerance']`

        Returns:
            Dataframe consisting of metadata of loaded data.
        """
        return self.base_loader.log_metadata(pars)

    def save_transformed_data(self, path: str = None):
        """
        Save transformed data to one file per iteration. Since to reload the data, the metadata
        needs to be loaded again. If changing the path, make sure the metadata is also in the new
        directory.

        Args:
            path: Path where transformed data is saved. Deault is None, in this case the
        """
        self.base_loader.save_transformed_data(path)

    def load_transformed_data(self, path: str = None):
        """
        Load transformed data from file. By default it is loaded from the path used for
        initialization of the loader.

        Args:
            path: Path to file where transformed data is stored. If None, the path used for
                initialization is used.
        """
        self.base_loader.load_transformed_data(path)
