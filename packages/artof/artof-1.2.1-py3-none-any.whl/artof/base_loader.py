"""
Module for BaseLoader class for providing basic framework for loading and processing artof data.
"""

import time
from enum import StrEnum
from typing import Union

import numpy as np
import pandas as pd

from .artof_utils import get_next_step, is_last_step, next_file_exists, print_progress
from .data_process import get_axis_values, get_bin_edges, project_data, wrap_angle
from .data_read import get_aquisition_df, load_counts, load_file, read_metadata
from .log_utils import DEFAULT_PARS
from .nexus_export import export_nx_mpes
from .normalize import get_norm_scaling_factor, norm_sweep
from .sweep import get_scienta_sweep_config
from .threading_utils import PropagatingThread
from .transform import ARTOFTransformer


class TransformFormat(StrEnum):
    """
    Enum for data transformation formats.
    - `raw`: Load raw data in ticks (x,y,t).
    - `raw_SI`: Load raw data in SI units (x: m,y: m,t: s).
    - `cylindrical`: Load data in cylindrical coordinates (r: m, phi: rad, t: s).
    - `spherical`: Load data in spherical coordinates and associated energy (E: eV, theta: rad,
    phi: rad).
    """

    RAW = "raw"
    RAW_SI = "raw_SI"
    CYLINDRICAL = "cylindrical"
    SPHERICAL = "spherical"


class BaseLoader:
    """
    BaseLoader class as a framework for loading and processing artof data. Loader for specific
    usecases can inherit from this class and implement their own methods.
    """

    def __init__(
        self,
        path: str,
        transform_format: TransformFormat,
        x0: Union[int, None] = None,
        y0: Union[int, None] = None,
        t0: Union[float, None] = None,
        sweep_type: str = "Scienta",
    ):
        """
        Initialize loader for given run. This function reads the metadata and sets up the
        transformer.

        Args:
            path: Path to run directory.
            transform_format: Load parameters in given format ('raw', 'raw_SI', 'cylindrical',
                'spherical').
                - `raw`: Load raw data in ticks (x,y,t).
                - `raw_SI`: Load raw data in SI units (x: m,y: m,t: s).
                - `cylindrical`: Load data in cylindrical coordinates (r: m, phi: rad, t: s).
                - `spherical`: Load data in spherical coordinates and associated energy
                    (E: eV, theta: rad, phi: rad).
            x0: Offset for x ticks
            y0: Offset for y ticks
            t0: Offset for t ticks
            sweep_type: Type of sweep analysis ('Scienta' or 'normal')

        Raises:
            NotImplementedError: When trying to load the 'normal' sweep type not implemented yet.
        """
        # setup instance variables
        self.threads = None
        self.sum_iters = None

        # save path and format
        self.path = path
        self.transform_format = transform_format
        # acquire metadata and timing info
        self.metadata = read_metadata(path)

        # setup everything need for sweep analysis
        self.acquisition_mode = self.metadata.acquisition.general.acquisitionMode
        if self.acquisition_mode == "sweep":
            if sweep_type == "Scienta":
                general = self.metadata.acquisition.general
                self.lens_steps, self.sweep_config = get_scienta_sweep_config(
                    general.spectrumBeginEnergy,
                    general.spectrumEndEnergy,
                    general.lensLowEdgeEnergyStep,
                    self.metadata.acquisition.lensmode.lensK,
                )
            else:
                raise NotImplementedError("Normal sweep analysis not implemented yet.")
        else:
            self.lens_steps = self.metadata.acquisition.general.lensSteps
        # create transformer based on metadata and transformation parameters
        self.x0 = self.metadata.acquisition.detector.x0 if x0 is None else x0
        self.y0 = self.metadata.acquisition.detector.y0 if y0 is None else y0
        self.t0 = self.metadata.acquisition.detector.t0 if t0 is None else t0
        self.transformer = ARTOFTransformer(self.metadata.acquisition, self.x0, self.y0, self.t0)
        # save axes and set returned bin configurations as default
        self.ax_names, self.default_bin_confs = self.transformer.get_axis_and_bins(
            transform_format, self.metadata.acquisition
        )
        # check if lens iterations and steps are available
        if (
            self.metadata.acquisition.general.lensIterations == 0
            or self.metadata.acquisition.general.lensSteps == 0
        ):
            raise ValueError("No lens iterations or steps found in metadata.")

        # set default iteration interval
        self.start_iter = 0
        self.stop_iter = self.metadata.acquisition.general.lensIterations
        self.iterations = self.metadata.acquisition.general.lensIterations

        # setup variables for data and count loading and processing
        self.setup_data_vars()
        self.setup_counts_vars()

    def setup_data_vars(self, t0: Union[float, None] = None):
        """
        Setup variables for data loading and processing.

        Args:
            t0: Offset for t ticks (optional).
        """
        self.t0 = t0 if t0 is not None else self.t0
        self.transformer.t0 = self.t0

        # setup progress info
        self.progress_info = {
            "name": "Steps",
            "current": 0,
            "total": self.iterations * self.lens_steps,
        }

        # create transformed data dictionary with empty list for each lens iteration
        self.transformed_data = {
            i: np.empty((0, 3), dtype=np.float64)
            for i in range(self.metadata.acquisition.general.lensIterations)
        }
        # create empty binned data dictionary
        self.binned_data = {}

    def setup_counts_vars(self):
        """
        Setup variables for event counts loading and processing.
        """
        # create empty event counts dictionary
        self.event_counts = {}

    def log_metadata(self, pars: Union[list, None] = None) -> pd.DataFrame:
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

        if pars is None:
            pars = DEFAULT_PARS
        return get_aquisition_df(self.metadata.acquisition, pars)

    def set_iter_interval(self, start_iter: int, stop_iter: int):
        """
        Set the interval of iterations to be loaded.

        Args:
            start_iter: Start iteration (including).
            stop_iter: Stop iteration (excluding).
        """
        if start_iter < 0 or stop_iter > self.metadata.acquisition.general.lensIterations:
            raise ValueError(
                f"Given range of iterations is not within range of available iterations "
                f"(0 to {self.metadata.acquisition.general.lensIterations - 1})."
            )

        # save start and stop iteration
        self.start_iter = start_iter
        self.stop_iter = stop_iter
        self.iterations = stop_iter - start_iter
        self.progress_info["total"] = self.iterations * self.lens_steps

    def count_events(
        self,
        sum_iters: bool,
        start_step: Union[tuple, None] = None,
        stop_step: Union[tuple, None] = None,
    ) -> dict:
        """
        Count events in given range of iteration.

        Args:
            sum_iters: Sum counts of each iteration, instead of returning counts for each step.
            start_step: Start step of the lens iteration (iter, step) (including).
            stop_step: Stop step of the lens iteration (iter, step) (excluding).

        Returns:
            Dict containing the number of events for each lens iteration.
        """

        start_step, stop_step = self.__get_step_interval(start_step, stop_step)

        event_counts = {}

        cur_step = start_step
        while True:
            try:
                cur_counts = load_counts(self.path, cur_step[0], cur_step[1])
            except FileNotFoundError as exc:
                if next_file_exists(
                    self.path, cur_step[0], cur_step[1], self.lens_steps
                ) or is_last_step(cur_step[0], cur_step[1], self.stop_iter, self.lens_steps):
                    print(
                        f"Skipping file {self.path}/{cur_step[0]}_{cur_step[1]} "
                        "as it is missing."
                    )
                    cur_counts = 0
                else:
                    raise FileNotFoundError(
                        f"File {self.path}/{cur_step[0]}_{cur_step[1]} not \
                                            found (more than 2 files missing)."
                    ) from exc
            except PermissionError:  # relevant for live plotting
                print(
                    f"File {self.path}/{cur_step[0]}_{cur_step[1]} does not allow reading yet."
                    f" Trying again in 0.5 seconds."
                )
                # if file does not allow reading yet, try again after 0.5 seconds
                time.sleep(0.5)
                cur_counts = load_counts(self.path, cur_step[0], cur_step[1])

            if sum_iters:
                # check if key exists
                if cur_step[0] not in event_counts:
                    event_counts[cur_step[0]] = cur_counts
                else:
                    event_counts[cur_step[0]] += cur_counts
            else:
                event_counts[f"{cur_step[0]}_{cur_step[1]}"] = cur_counts

            # break loop if last loaded step was the last step
            if is_last_step(cur_step[0], cur_step[1], self.stop_iter, self.lens_steps):
                break
            cur_step = get_next_step(cur_step[0], cur_step[1], self.lens_steps)
            # check if current step is within range of steps to be loaded
            if cur_step == stop_step:
                break

        return event_counts

    def add_event_counts(self, event_counts_to_add: dict) -> None:
        """
        Add new event counts to existing event counts.

        Args:
            event_counts_to_add: Dictionary containing event counts to be added.
        """
        for key, event_counts in event_counts_to_add.items():
            if key in self.event_counts:
                self.event_counts[key] += event_counts
            else:
                self.event_counts[key] = event_counts

    def load_and_transform(
        self,
        multithreading: bool,
        start_step: Union[tuple, None] = None,
        stop_step: Union[tuple, None] = None,
        wrap_low_energy: bool = False,
        trigger_period: Union[int, None] = None,
        logging: bool = True,
    ) -> dict:
        """
        Load raw data from file and transform to desired format.

        Args:
            multithreading: Use multithreading to load and transform data (True/False).
            start_step: Start step of the lens iteration (iter, step) (including).
            stop_step: Stop step of the lens iteration (iter, step) (excluding).
            wrap_low_energy: Wrap low energy values to high energy values (default False). If True,
                the trigger period is read from 'timing.txt' file unless provided as
                `trigger_period`.
            trigger_period: Period between two trigger. When provided time of flight longer than one
                one trigger period can be loaded (default None).
            logging: If True, log progress information (default True).

        Raises:
            RuntimeError: If the run was not initialized before loading data.

        Returns:
            Transformed data in given format as dictionary with iteration as key and
             transformed data as value.
        """
        # make sure init_run was called before and transformer is available
        if self.transformer is None:
            raise RuntimeError("Initialize run before loading data.")

        start_step, stop_step = self.__get_step_interval(start_step, stop_step)

        # print initial progress info
        if logging and self.progress_info["current"] == 0:
            print_progress(self.progress_info)

        data_pieces = {i: [] for i in range(start_step[0], stop_step[0] + 1)}
        self.threads = []

        if wrap_low_energy:
            if trigger_period is None:
                # take average between start and end trigger period
                trigger_period = int(
                    (
                        self.metadata.timing.start.TriggerPeriod
                        + self.metadata.timing.finish.TriggerPeriod
                    )
                    // 2
                )
        else:
            trigger_period = None

        cur_step = start_step
        while True:
            if multithreading:
                thread = PropagatingThread(
                    target=self.__process_data,
                    args=(cur_step[0], cur_step[1], data_pieces),
                    kwargs={"trigger_period": trigger_period, "logging": logging},
                )
                self.threads.append(thread)
                thread.start()
            else:
                self.__process_data(
                    cur_step[0],
                    cur_step[1],
                    data_pieces,
                    trigger_period=trigger_period,
                    logging=logging,
                )
            # break loop if last loaded step was the last step
            if is_last_step(cur_step[0], cur_step[1], self.stop_iter, self.lens_steps):
                break
            cur_step = get_next_step(cur_step[0], cur_step[1], self.lens_steps)
            # check if current step is within range of steps to be loaded
            if cur_step == stop_step:
                break

        if multithreading:  # wait for all threads to finish
            for thread in self.threads:
                thread.join()

        # combine all data pieces and previously transformed data into one array per iteration
        transformed_data = {}
        for it in data_pieces.keys():
            if len(data_pieces[it]) > 0:
                transformed_data[it] = np.concatenate(data_pieces[it], axis=0)

        return transformed_data

    def __get_step_interval(
        self, start_step: Union[tuple, None], stop_step: Union[tuple, None]
    ) -> tuple[tuple, tuple]:
        """
        Get step interval for loading data. If no start and/or stop step are given, use the minimum
         and/or max.

        Args:
            start_step: Start step of the lens iteration (iter, step) (including).
            stop_step: Stop step of the lens iteration (iter, step) (excluding).

        Returns:
            Tuple of start and stop step.
        """
        start_step = (self.start_iter, 0) if start_step is None else start_step
        stop_step = (self.stop_iter, 0) if stop_step is None else stop_step
        return start_step, stop_step

    def add_transformed_data(self, trans_data_to_add: dict) -> None:
        """
        Add transformed data to existing transformed data.

        Args:
            trans_data_to_add: Dictionary containing transformed data to be added.
        """
        for it in trans_data_to_add.keys():
            if len(trans_data_to_add[it]) > 0:
                self.transformed_data[it] = np.concatenate(
                    [self.transformed_data[it], trans_data_to_add[it]], axis=0
                )

    def print_transform_stats(self) -> None:
        """
        Print statistics of loaded and transformed data.
        """
        points = 0
        for data in self.transformed_data.values():
            points += data.shape[0]
        # overwriting of loading message
        print()
        print(f"Loaded and transformed {points} data points to formats {self.ax_names}.")

    def __process_data(
        self,
        it: int,
        step: int,
        data_pieces: dict,
        trigger_period: Union[int, None] = None,
        logging: bool = True,
    ) -> None:
        """
        Load and transform single data file in given format (needed for multithreading).

        Args:
            it: Index of the lens iteration to be loaded.
            step: Index of the lens step to be loaded.
            data_pieces: Dictionary to store the transformed data.
            trigger_period: Period between two trigger. When provided time of flight longer than one
                one trigger period can be loaded (default None).
        logging: If True, log progress information (default True).

        Raises:
            FileNotFoundError: If file (and next file) is not found.
        """

        try:
            raw_data = load_file(self.path, it, step)
        except FileNotFoundError as exc:
            if next_file_exists(self.path, it, step, self.lens_steps) or is_last_step(
                it, step, self.stop_iter, self.lens_steps
            ):
                print(f"Skipping file {self.path}/{it}_{step} as it is missing.")
                self.progress_info["current"] += 1
                if logging:
                    print_progress(self.progress_info)
                return
            raise FileNotFoundError(
                f"File {self.path}/{it}_{step} not found (more than 2 files missing)."
            ) from exc
        except PermissionError:  # relevant for live plotting
            print(
                f"File {self.path}/{it}_{step} does not allow reading yet."
                f" Trying again in 0.5 seconds."
            )
            # if file does not allow reading yet, try again after 0.5 seconds
            time.sleep(0.5)
            raw_data = load_file(self.path, it, step)
        data_pieces[it].append(self.__transform_data(raw_data, step, trigger_period=trigger_period))
        self.progress_info["current"] += 1
        if logging:
            print_progress(self.progress_info)

    def __transform_data(
        self, raw_data: np.ndarray, step: int, trigger_period: Union[int, None] = None
    ) -> np.ndarray:
        """
        Load and transform single data file in given format (needed for multithreading).

        Args:
            raw_data: Raw data to be transformed.
            step: Index of the lens step to be loaded.
            trigger_period: Period between two trigger. When provided time of flight longer than one
                trigger period can be loaded (default None).
        """

        if self.acquisition_mode == "sweep":
            center_energy = (
                self.sweep_config.sweep_start_energy
                + step * self.sweep_config.adjusted_channel_width
            )
            return self.transformer.transform(
                raw_data,
                self.transform_format,
                center_energy=center_energy,
                trigger_period=trigger_period,
            )

        center_energy = self.metadata.acquisition.general.centerEnergy
        return self.transformer.transform(
            raw_data,
            self.transform_format,
            center_energy=center_energy,
            trigger_period=trigger_period,
        )

    def set_bin_configs(self, cust_bin_confs: Union[list, None], logging: bool = True):
        """
        Set custom binning configurations for the 3 parameters.

        Args:
            cust_bin_confs: List of 3 custom binning configurations for the 3 parameters
             [min, max, edges], optional. F.e.: [[-1500, 1500, 101],
             [-1500, 1500, 101],[12000, 18000, 201]]
            logging: Toggle progress information (default True).
        """
        if cust_bin_confs is None:
            cust_bin_confs = [None, None, None]
        # use either passed or default bin configurations
        bin_confs = self.__get_bin_confs(cust_bin_confs, logging)
        self.bin_edges = self.__get_bin_edges(bin_confs)

    def __get_bin_confs(self, cust_bin_confs: list, logging: bool) -> list:
        """
        Set bin configurations for 3 parameters.

        Args:
            cust_bin_confs: List of 3 custom binning configurations for the 3 parameters
             [min, max, edges], optional. F.e.: [[-1500, 1500, 101],
             [-1500, 1500, 101],[12000, 18000, 201]]

        Returns:
            List of 3 binning configurations for the 3 parameters [min, max, edges].
        """

        bin_conf_pos_names = ["min", "max", "edge_count"]

        bin_confs = []
        for i, bin_conf in enumerate(cust_bin_confs):
            if bin_conf is None:
                # use default binning configuration
                bin_confs.append(self.default_bin_confs[i])
            else:
                for j, val in enumerate(bin_conf):
                    if val is None:
                        # use default binning configuration for this position
                        bin_conf[j] = self.default_bin_confs[i][j]
                bin_confs.append(bin_conf)

            step_size = (bin_confs[i][1] - bin_confs[i][0]) / bin_confs[i][2]
            if logging:
                ax_var, unit = self.ax_names[i].split("_")
                print(
                    f"Binning axis '{ax_var}' between {bin_confs[i][0]:.3E} {unit} and "
                    f"{bin_confs[i][1]:.3E} {unit} with {bin_confs[i][2]} edges "
                    f"(step size {step_size:.3E} {unit})."
                )
        return bin_confs

    def __get_bin_edges(self, bin_confs: list) -> list:
        """
        Create bin edges based on the passed bin configurations.

        Args:
            bin_confs: List of 3 binning configurations for the 3 parameters [min, max, edges],
            optional. F.e.: [[-1500, 1500, 101], [-1500, 1500, 101],[12000, 18000, 201]]

        Returns:
            List of bin edges for each axis.
        """
        bin_edges = []
        for i in range(3):
            bin_edges.append(get_bin_edges(bin_confs[i], data_id=self.ax_names[i]))
        return bin_edges

    def bin(
        self,
        transformed_data: dict[int, list],
        norm_modes: Union[list, None] = None,
        win_config: Union[tuple[int], None] = None,
        cust_start_iter: Union[int, None] = None,
        cust_stop_iter: Union[int, None] = None,
    ) -> dict[str, np.ndarray]:
        """
        Bin loaded data into 3D histogram.

        Args:
            transformed_data: Transformed data to be binned.
            norm_modes: Normalization mode for binned data ('iterations', 'dwell_time', 'sweep').
                Default is None.
                - `iterations`: Normalize data by number of iterations.
                - `dwell_time`: Normalize data by dwell time.
                - `sweep`: Normalize data by changing window size of sweep data.
            win_config: Window size and delta for spectral evolution analysis. If None, no window
                size is set.
            cust_start_iter: Start iteration (including). Default is None, first run iteration.
            cust_stop_iter: Stop iteration (excluding). Default is None, last run iteration.

        Returns:
            Dictionary containing binned data for each window

        Raises:
            RuntimeError: If data is not loaded before binning or no binning config was set
             (see set_bin_configs).
            ValueError: If win_size and win_delta are not set correctly.
        """
        if self.transformer is None:
            raise RuntimeError("Initialize run before binning data.")

        if self.bin_edges is None:
            raise RuntimeError("Set bin configurations before binning data.")

        if win_config is not None:
            if len(win_config) != 2:
                raise ValueError(
                    "Window size and delta must be set as tuple (win_size, win_delta)."
                )
            win_size, win_delta = win_config
            if win_size <= 0 or win_delta <= 0:
                raise ValueError("Window size and delta must be greater than 0.")
            if win_delta > win_size:
                raise ValueError("Window delta must be smaller than window size.")
            if win_size > self.stop_iter - self.start_iter:
                raise ValueError(
                    "Window size must be smaller than the number of iterations to be binned."
                )
        else:
            win_size = self.stop_iter - self.start_iter
            win_delta = 1

        if norm_modes is not None:
            # print all non-recognized norm modes
            for mode in norm_modes:
                if mode not in ["iterations", "dwell_time", "sweep"]:
                    print(f'Normalization mode "{mode}" not recognized.')

        # wrap counts from last bin to first bin for phi axis (see Igor)
        if "phi_rad" in self.ax_names:
            phi_idx = self.ax_names.index("phi_rad")
            phi_delta = self.bin_edges[phi_idx][1] - self.bin_edges[phi_idx][0]
            transformed_data = wrap_angle(phi_idx, phi_delta / 2, transformed_data)

        # create empty binned data dictionary
        binned_data = {}

        # go through all iterations with given window size and delta

        win_start = self.start_iter
        if cust_start_iter is not None:
            # get the first window start that includes the custom start iteration
            while win_start + win_size < cust_start_iter + 1:
                win_start += win_delta

        while (win_start + win_size) <= self.stop_iter:
            # abort if window start is greater than stop iteration
            if cust_stop_iter is not None:
                if win_start >= cust_stop_iter:
                    break

            win_end = win_start + win_size
            if cust_stop_iter is not None:
                win_end = min(win_end, cust_stop_iter)
            win_data = [
                transformed_data[it] for it in range(win_start, win_end) if it in transformed_data
            ]
            if len(win_data) == 0:  # skip empty windows in case of missing files
                win_start += win_delta
                continue
            win_data = np.concatenate(win_data)
            win_id = f"{win_start}-{win_end - 1}"
            # bin data for current window
            binned_data[win_id], _ = np.histogramdd(win_data, bins=self.bin_edges)
            # go to next window
            win_start += win_delta

            # normalize data if desired
            if norm_modes is not None:
                binned_data[win_id] = self.__norm_data(binned_data[win_id], norm_modes=norm_modes)

        if win_config is not None:
            print(
                f"Binned data for {len(binned_data)} windows "
                f"with size {win_size} and delta {win_delta}."
            )

        return binned_data

    def __norm_data(self, data: np.ndarray, norm_modes: list) -> np.ndarray:
        """
        Normalize data based on passed norm_modes.

        Args:
            data: Data to be normalized.
            norm_modes: Normalization mode for binned data ('iterations', 'dwell_time', 'sweep').
                - `iterations`: Normalize data by number of iterations.
                - `dwell_time`: Normalize data by dwell time.
                - `sweep`: Normalize data by changing window size of sweep data.
        """
        scaling_factor = get_norm_scaling_factor(
            norm_modes, self.iterations, self.metadata.acquisition.general.lensDwellTime
        )
        data *= scaling_factor
        # normalize data by sweep acceptance if desired and in sweep mode
        if "sweep" in norm_modes:
            if self.acquisition_mode != "sweep" or self.transform_format != "spherical":
                raise ValueError(
                    "Sweep normalization only possible for sweep data in spherical format."
                )
            data = norm_sweep(
                data,
                self.bin_edges[0],
                self.sweep_config,
                self.lens_steps,
                self.metadata.acquisition.lensmode.lensK,
            )
        return data

    def add_binned_data(self, binned_data_to_add: dict) -> None:
        """
        Add binned data to existing binned data.

        Args:
            binned_data_to_add: Binned data to be added.
        """
        for it, data in binned_data_to_add.items():
            if it not in self.binned_data:
                self.binned_data[it] = data
            else:
                self.binned_data[it] += data
        # check if key is in binned data
        # if self.binned_data is None:
        #     self.binned_data = binned_data_to_add
        # else:
        #     self.binned_data += binned_data_to_add

    def save_transformed_data(self, path: Union[str, None] = None):
        """
        Save transformed data to one file per iteration. Since to reload the data, the metadata
        needs to be loaded again. If changing the path, make sure the metadata is also in the new
        directory.

        Args:
            path: Path where transformed data is saved. Deault is None, in this case the
        """

        if path is None:
            path = self.path

        for it, data in self.transformed_data.items():
            data.tofile(f"{path}/{self.transform_format}_{it}.bin")

        print(f"Saved transformed data as binary file to {path}/{self.transform_format}_[it].bin ")

    def load_transformed_data(self, path: Union[str, None] = None):
        """
        Load transformed data from file. By default it is loaded from the path used for
        initialization of the loader.

        Args:
            path: Path to file where transformed data is stored. If None, the path used for
                initialization is used.
        """
        if path is None:
            path = self.path

        if self.transform_format == "raw":
            data_format = np.int32
        else:
            data_format = np.float64

        for it in self.transformed_data.keys():
            self.transformed_data[it] = (
                np.fromfile(f"{path}/{self.transform_format}_{it}.bin", dtype=data_format)
                .reshape(-1, 3)
                .astype(np.float64)
            )

    def get_binned_data(
        self,
        proj_axes: Union[list, None] = None,
        ranges=None,
        norm_step_size: bool = False,
    ) -> tuple[list, Union[list, dict]]:
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

        if ranges is None:
            ranges = [None, None, None]

        axes_values = get_axis_values(self.bin_edges, self.ax_names)
        if proj_axes is not None:
            # if projection onto one axis, return axis values without list
            if len(proj_axes) == 1:
                axes_values = axes_values[proj_axes[0]]
            else:
                axes_values = [
                    ax_values for i, ax_values in enumerate(axes_values) if i in proj_axes
                ]

        data = {}
        for win_id, cur_data in self.binned_data.items():
            if proj_axes is None:
                data[win_id] = cur_data.copy()
            else:
                data[win_id] = project_data(
                    cur_data, self.bin_edges, proj_axes, ranges, norm_step_size
                )

        # if only one entry in proj_data (meaning only one window), return without dict
        if len(data) == 1:
            data = list(data.values())[0]

        return (axes_values, data)

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

        if file_format not in ["csv", "nxs"]:
            raise ValueError("File format must be 'csv' or 'nxs'.")

        if ranges is None:
            ranges = [None, None, None]

        axes_names = self.ax_names
        axes_values = get_axis_values(self.bin_edges, self.ax_names)
        if proj_axes is not None:
            axes_names = [ax_name for i, ax_name in enumerate(axes_names) if i in proj_axes]
            axes_values = [ax_values for i, ax_values in enumerate(axes_values) if i in proj_axes]

        if file_format == "csv":
            if proj_axes is None:
                raise ValueError(
                    "Projection axes must be given for csv export. Use 'hdf5' format for raw data."
                )

            for win_id, data in self.binned_data.items():
                proj_data = project_data(data, self.bin_edges, proj_axes, ranges, norm_step_size)

                # save t0, x0 ad y0 to header
                header = f"# x0: {self.x0}, y0: {self.y0}, t0: {self.t0}"
                # add axis to header
                for i, ax_idx in enumerate(proj_axes):
                    values_str = ", ".join(map(str, axes_values[i]))
                    header += f"\n# {self.ax_names[ax_idx]}: {values_str}"

                # save file with win_id, if window does not span the entire range of iterations
                win_start, win_end = win_id.split("-")
                win_start, win_end = int(win_start), int(win_end)
                if win_start == self.start_iter and win_end == self.stop_iter - 1:
                    identifier = ""
                else:
                    identifier = f"_{win_id}"

                # save data to csv file
                np.savetxt(
                    f"{path}{identifier}.csv",
                    proj_data,
                    delimiter=delimiter,
                    header=header,
                    comments="",
                )
        elif file_format == "nxs":
            # save data to nxs file

            wins = None
            proj_data = []
            if len(self.binned_data.keys()) > 1:
                if proj_axes is None:
                    proj_data = np.array(list(self.binned_data.values()))
                else:
                    proj_data = []
                    for data in self.binned_data.values():
                        proj_data.append(
                            project_data(data, self.bin_edges, proj_axes, ranges, norm_step_size)
                        )
                    proj_data = np.array(proj_data)
                wins = list(self.binned_data.keys())
            else:
                binned_data = np.array(list(self.binned_data.values())[0])
                if proj_axes is None:
                    proj_data = binned_data
                else:
                    proj_data = project_data(
                        binned_data, self.bin_edges, proj_axes, ranges, norm_step_size
                    )

            # order axes values and axes names correctly
            if proj_axes is not None and len(proj_axes) == 2 and proj_axes[0] < proj_axes[1]:
                axes_names = [axes_names[1], axes_names[0]]
                axes_values = [axes_values[1], axes_values[0]]

            export_nx_mpes(
                path,
                proj_data,
                self.ax_names,
                axes_values,
                self.acquisition_mode,
                self.metadata,
                win_ids=wins,
                eln_path=eln_path,
            )

    def export_counts_to_csv(
        self, path: str, iter_range: Union[list, None] = None, delimiter: str = ","
    ):
        """
        Export event counts to csv file.

        Args:
            path: Path to which the data is saved. Including filename but excluding extension (csv).
            iter_range: Range of iterations to be exported (default None, all iterations).
            delimiter: Delimiter by which the data is separated (default ',').
        """

        iterations, counts = self.get_event_counts(iter_range=iter_range)

        df = pd.DataFrame({"Step": iterations, "Counts": counts})
        df.to_csv(f"{path}.csv", index=False, sep=delimiter)

    def get_event_counts(self, iter_range: Union[list, None] = None) -> tuple[list, list]:
        """
        Get the iterations and the corresponding counts.

        Args:
            iter_range: Range of iterations to be exported (default None, all iterations).

        Returns:
            Tuple containing the iterations and the corresponding counts.
        """

        counts = list(self.event_counts.values())
        iterations = list(self.event_counts.keys())
        if iter_range is not None:
            counts = counts[iter_range[0] : iter_range[1]]
            iterations = iterations[iter_range[0] : iter_range[1]]

        return iterations, counts
