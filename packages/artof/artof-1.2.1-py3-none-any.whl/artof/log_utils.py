"""
Module containing functions to log metadata of all runs in a directory.
"""

import os

import pandas as pd

# internal
from .data_read import get_aquisition_df, read_acquisition_cfg

DEFAULT_PARS = [
    "analyzer.lensMode",
    "analyzer.elementSet",
    "analyzer.passEnergy",
    "general.acquisitionStarted",
    "general.acquisitionMode",
    "general.xytFormat",
    "general.lensIterations",
    "general.lensDwellTime",
    "general.spectrumBeginEnergy",
    "general.spectrumEndEnergy",
    "general.centerEnergy",
    "detector.t0",
    "detector.t0Tolerance",
]


def get_run_logs(path: str, pars: list = None) -> pd.DataFrame:
    """
    Log metadata of all runs in given directory to a pandas dataframe.

    Args:
        path: Path to directory to be logged.
        pars: List of parameters to be logged. (default: ['analyzer.lensMode',
         'analyzer.elementSet', 'analyzer.passEnergy', 'general.acquisitionStarted',
         'general.acquisitionMode', 'general.xytFormat', 'general.lensIterations',
         'general.lensDwellTime', 'general.spectrumBeginEnergy', 'general.spectrumEndEnergy',
         'general.centerEnergy', 'detector.t0', 'detector.t0Tolerance']

    Returns:
        Pandas dataframe containing the metadata of each run.
    """

    if pars is None:
        pars = DEFAULT_PARS

    # create empty dataframe
    dfs = []

    for f in sorted(os.scandir(path), key=lambda e: e.name):
        if f.is_dir():
            # check if file exists
            if os.path.isfile(f.path + "/acquisition.cfg"):
                # read metadata from acquisition.cfg
                acquisition = read_acquisition_cfg(f.path)
                # add metadata to dataframe
                dfs.append(get_aquisition_df(acquisition, pars, run_name=f.name))

    if len(dfs) == 0:
        print('No runs with "acquisition.cfg" file found in given directory.')
        return None

    return pd.concat(dfs, ignore_index=True)
