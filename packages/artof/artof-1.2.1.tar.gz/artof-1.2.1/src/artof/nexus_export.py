"""
Module containing function to export data hdf5-file (.nxs) in NeXus format (NXmpes)
"""

import datetime
from dataclasses import is_dataclass
from importlib import resources as impresources
from typing import Union

import h5py
import numpy as np
import pytz
import yaml

from artof.artof_utils import get_datetime_string
from artof.data_read import Metadata

from . import eln_base

ENERGY_SCAN_MODES_DICT = {
    "fix": "fixed_acceptance_window",
    "sweep": "sweep_acceptance_window",
}

AXIS_LONG_NAMES = {
    "E": "Energy",
    "phi": "Phi",
    "theta": "Theta",
    "t": "Time",
    "x": "X",
    "y": "Y",
    "r": "Radius",
    "Delay": "Delay",
}

AXIS_NEXUS_MAP = {
    "E": "energy",
    "phi": "angle0",
    "theta": "angle1",
    "t": "time",
    "x": "spatial0",
    "y": "spatial1",
    "r": "spatial0",
    "Delay": "delay",
}

MPES_ELN_BASE = "mpes.base.yaml"


def export_nx_mpes(
    path: str,
    binned_data: np.ndarray,
    ax_names: list[str],
    axes_values: list,
    acquisition_mode: str,
    metadata: Metadata,
    win_ids: Union[list, None] = None,
    eln_path: Union[str, None] = None,
):
    """
    Export data to NeXus format (.nxs) using the NXmpes structure.

    Args:
        path: Path to which the data is saved. Including filename but excluding extension
        binned_data: The binned data to be saved in the NeXus file.
        ax_names: Names of the axes corresponding to the binned data.
        axes_values: Values for each axis, which should match the names in ax_names.
        acquisition_mode: The mode of acquisition used during data collection.
        win_ids: List of window identifiers. Should be provided, when having additonal evolution
         dimension
        eln_path: Path to the electronic lab notebook (ELN) file. If None, a default template is
         used.
    """

    # add nxs file ending if missing
    if path.split(".")[-1] != "nxs":
        path += ".nxs"

    # load eln file (base template if none provided)
    if eln_path is None:
        eln_file = impresources.files(eln_base) / MPES_ELN_BASE
    else:
        eln_file = eln_path

    # read eln data
    with open(eln_file, "r", encoding="utf-8") as file:
        eln_dict = yaml.safe_load(file)

        # create nexus file
        with h5py.File(path, "w") as f:

            entry = f.create_group("entry")
            entry.attrs["NX_class"] = "NXentry"
            save_eln_field(entry, "title", eln_dict, ["title"])
            definition = entry.create_dataset("definition", data="NXmpes")
            definition.attrs["version"] = "1.0"

            entry.create_dataset(
                "start_time",
                data=pytz.timezone("Europe/Berlin")
                .localize(metadata.timing.start.timestamp)
                .isoformat(),
            )
            entry.create_dataset(
                "end_time",
                data=pytz.timezone("Europe/Berlin")
                .localize(metadata.timing.finish.timestamp)
                .isoformat(),
            )

            save_eln_field(entry, "method", eln_dict, ["method"])

            # user
            user = entry.create_group("user")
            user.attrs["NX_class"] = "NXuser"
            save_eln_field(user, "name", eln_dict, ["user", "name"], required=True)
            save_eln_field(user, "affiliation", eln_dict, ["user", "affiliation"], required=True)
            save_eln_field(user, "address", eln_dict, ["user", "address"])

            # instrument
            instrument = entry.create_group("instrument")
            instrument.attrs["NX_class"] = "NXinstrument"
            save_device_info(instrument, eln_dict, ["instrument", "device_information"])
            ## axis resolutions
            for res_ax in ["energy", "angle0", "angle1"]:
                if eln_field_exists(eln_dict, ["instrument", f"{res_ax}_resolution"])[0]:
                    ax_res = instrument.create_group(f"{res_ax}_resolution")
                    ax_res.attrs["NX_class"] = "Nxresolution"
                    save_eln_field(
                        ax_res,
                        "physical_quantity",
                        eln_dict,
                        ["instrument", f"{res_ax}_resolution", "physical_quantity"],
                        required=True,
                    )
                    save_eln_field(
                        ax_res,
                        "type",
                        eln_dict,
                        ["instrument", f"{res_ax}_resolution", "type"],
                    )
                    save_eln_field(
                        ax_res,
                        "resolution",
                        eln_dict,
                        ["instrument", f"{res_ax}_resolution", "resolution"],
                        required=True,
                        is_unit=True,
                    )
            ## sources and corresponding beams
            for source_name in ["probe", "pump"]:
                ## source
                if eln_field_exists(eln_dict, ["instrument", f"source_{source_name}"])[0]:
                    source = instrument.create_group(f"source_{source_name}")
                    source.attrs["NX_class"] = "NXsource"
                    save_eln_field(
                        source,
                        "type",
                        eln_dict,
                        ["instrument", f"source_{source_name}", "type"],
                        required=True,
                    )
                    save_eln_field(
                        source, "name", eln_dict, ["instrument", f"source_{source_name}", "name"]
                    )
                    save_device_info(
                        source,
                        eln_dict,
                        ["instrument", f"source_{source_name}", "device_information"],
                    )
                    save_eln_field(
                        source,
                        "associated_beam",
                        eln_dict,
                        ["instrument", f"source_{source_name}", "associated_beam"],
                        required=True,
                    )

                if eln_field_exists(eln_dict, ["instrument", f"beam_{source_name}"])[0]:
                    ## beam
                    beam = instrument.create_group(f"beam_{source_name}")
                    beam.attrs["NX_class"] = "NXbeam"
                    save_eln_field(
                        beam,
                        "distance",
                        eln_dict,
                        ["instrument", f"beam_{source_name}", "distance"],
                        is_unit=True,
                    )
                    save_eln_field(
                        beam,
                        "incident_energy",
                        eln_dict,
                        ["instrument", f"beam_{source_name}", "incident_energy"],
                        is_unit=True,
                    )
                    save_eln_field(
                        beam,
                        "incident_energy_spread",
                        eln_dict,
                        ["instrument", f"beam_{source_name}", "incident_energy_spread"],
                        is_unit=True,
                    )
                    save_eln_field(
                        beam,
                        "incident_polarization",
                        eln_dict,
                        ["instrument", f"beam_{source_name}", "incident_polarization"],
                        is_unit=True,
                    )
                    save_eln_field(
                        beam,
                        "extent",
                        eln_dict,
                        ["instrument", f"beam_{source_name}", "extent"],
                        is_unit=True,
                    )
                    save_eln_field(
                        beam,
                        "associated_source",
                        eln_dict,
                        ["instrument", f"beam_{source_name}", "associated_source"],
                    )

            ## beam incident energy (default if not in eln)
            beam_probe = instrument.require_group("beam_probe")
            beam_probe.attrs["NX_class"] = "NXbeam"
            if not eln_field_exists(eln_dict, ["instrument", "beam_probe", "incident_energy"])[0]:
                # get mono energy from metadata extra info if available
                try:
                    incident_en = float(metadata.extra.start["Mono_energy"])
                except (AttributeError, KeyError, TypeError):
                    incident_en = -1
                beam_en = beam_probe.create_dataset("incident_energy", data=incident_en)
                beam_en.attrs["units"] = "eV"

            ## analyzer
            analyzer = instrument.create_group("electronanalyzer")
            analyzer.attrs["NX_class"] = "NXelectronanalyzer"
            save_eln_field(
                analyzer,
                "description",
                eln_dict,
                ["instrument", "electronanalyzer", "description"],
            )
            save_device_info(
                analyzer, eln_dict, ["instrument", "electronanalyzer", "device_information"]
            )

            ### collection column
            collection_col = analyzer.create_group("column")
            collection_col.attrs["NX_class"] = "NXcollectioncolumn"
            collection_col.create_dataset("lens_mode", data=metadata.acquisition.analyzer.lensMode)
            save_eln_field(
                collection_col,
                "scheme",
                eln_dict,
                ["instrument", "electronanalyzer", "collectioncolumn", "scheme"],
                required=True,
            )
            save_eln_field(
                collection_col,
                "projection",
                eln_dict,
                ["instrument", "electronanalyzer", "collectioncolumn", "projection"],
            )
            save_device_info(
                collection_col,
                eln_dict,
                ["instrument", "electronanalyzer", "collectioncolumn", "device_information"],
            )
            #### energy dispersion
            en_disp = analyzer.create_group("dispersion")
            en_disp.attrs["NX_class"] = "NXenergydispersion"
            disp_center_en = en_disp.create_dataset(
                "center_energy", data=metadata.acquisition.general.centerEnergy
            )
            disp_center_en.attrs["units"] = "eV"
            scan_mode = en_disp.create_dataset(
                "energy_scan_mode", data=ENERGY_SCAN_MODES_DICT[acquisition_mode]
            )
            scan_mode.attrs["custom"] = True
            save_eln_field(
                en_disp,
                "scheme",
                eln_dict,
                ["instrument", "electronanalyzer", "energydispersion", "scheme"],
            )
            save_eln_field(
                en_disp,
                "drift_energy",
                eln_dict,
                ["instrument", "electronanalyzer", "energydispersion", "drift_energy"],
                is_unit=True,
            )
            save_device_info(
                en_disp,
                eln_dict,
                ["instrument", "electronanalyzer", "energydispersion", "device_information"],
            )
            #### electron detector
            if eln_field_exists(eln_dict, ["instrument", "electronanalyzer", "electron_detector"])[
                0
            ]:
                el_detector = analyzer.create_group("electron_detector")
                el_detector.attrs["NX_class"] = "NXelectron_detector"
                save_eln_field(
                    el_detector,
                    "amplifier_type",
                    eln_dict,
                    ["instrument", "electronanalyzer", "electron_detector", "amplifier_type"],
                )
                save_eln_field(
                    el_detector,
                    "detector_type",
                    eln_dict,
                    ["instrument", "electronanalyzer", "electron_detector", "detector_type"],
                )
                save_device_info(
                    el_detector,
                    eln_dict,
                    ["instrument", "electronanalyzer", "electron_detector", "device_information"],
                )

            # sample
            sample = entry.create_group("sample")
            sample.attrs["NX_class"] = "NXsample"
            save_eln_field(sample, "name", eln_dict, ["sample", "name"], required=True)
            save_eln_field(sample, "identifier", eln_dict, ["sample", "identifier"])
            save_eln_field(sample, "chemical_formula", eln_dict, ["sample", "chemical_formula"])
            save_eln_field(sample, "physical_form", eln_dict, ["sample", "physical_form"])
            save_eln_field(sample, "situation", eln_dict, ["sample", "situation"])
            ## history
            if eln_field_exists(eln_dict, ["sample", "history"])[0]:
                history = sample.create_group("history")
                history.attrs["NX_class"] = "NXhistory"
                for activity in ["sample_preparation"]:
                    if eln_field_exists(eln_dict, ["sample", "history", activity])[0]:
                        act_group = history.create_group(activity)
                        act_group.attrs["NX_class"] = "NXactivity"
                        save_eln_field(
                            act_group,
                            "start_time",
                            eln_dict,
                            ["sample", "history", activity, "start_time"],
                            required=True,
                        )
                        save_eln_field(
                            act_group,
                            "end_time",
                            eln_dict,
                            ["sample", "history", activity, "end_time"],
                        )
                        save_eln_field(
                            act_group,
                            "method",
                            eln_dict,
                            ["sample", "history", activity, "method"],
                        )
            ## temperature environment
            if eln_field_exists(eln_dict, ["sample", "temperature_env"])[0]:
                temp_env = sample.create_group("temperature_env")
                temp_env.attrs["NX_class"] = "NXenvironment"
                save_eln_field(
                    temp_env,
                    "value",
                    eln_dict,
                    ["sample", "temperature_env", "value"],
                    is_unit=True,
                )
            ## gas pressure environment
            if eln_field_exists(eln_dict, ["sample", "gas_pressure_env"])[0]:
                gas_env = sample.create_group("gas_pressure_env")
                gas_env.attrs["NX_class"] = "NXenvironment"
                save_eln_field(
                    gas_env,
                    "value",
                    eln_dict,
                    ["sample", "gas_pressure_env", "value"],
                    is_unit=True,
                )

            # data
            data = entry.create_group("data")
            data.attrs["NX_class"] = "NXdata"
            data.attrs["signal"] = "data"
            # configure axes
            ax_vars = []
            if win_ids:
                ax_vars.append("window")
                cur_ax_field = data.create_dataset("window", data=np.arange(len(win_ids)))
                cur_ax_field.attrs["ids"] = win_ids
            for name, ax in zip(ax_names, axes_values):
                var, units = name.split("_")
                ax_vars.append(AXIS_NEXUS_MAP[var])
                cur_ax_field = data.create_dataset(AXIS_NEXUS_MAP[var], data=ax)
                cur_ax_field.attrs["units"] = units
                cur_ax_field.attrs["long_name"] = AXIS_LONG_NAMES[var]
                if var == "E":
                    cur_ax_field.attrs["type"] = "kinetic"
            data.attrs["axes"] = ax_vars
            data.create_dataset("data", data=binned_data)

            # custom metadata (copy of metadata file contents exported with measurements)
            cust_meta = entry.create_group("legacy_metadata")
            cust_meta.attrs["NX_class"] = "NXcollection"
            write_object_to_nexus(metadata, cust_meta)


def save_eln_field(
    group: h5py.Group,
    field: str,
    eln_dict: dict,
    keys: list,
    required: bool = False,
    is_unit: bool = False,
):
    """
    Save a field from the ELN data to the HDF5 group. If eln field is not found, nothing is saved.

    Args:
        group: The HDF5 group where the field should be saved.
        field: The name of the field to be saved.
        eln_dict: The ELN data dictionary.
        keys: List of keys to navigate through the ELN data dictionary to find the desired field.
        required: If True, raises an error if the field is not found (default False).
        unit: If True, field has a unit and is split into value and unit subfields (default False).

    Raises:
        KeyError: If the field is required but not found in the ELN data.
    """

    exists, eln_data = eln_field_exists(eln_dict, keys, is_unit=is_unit)
    if not exists:
        if required:
            raise KeyError(f"Required ELN field '{'.'.join(keys)}' not found.")
        return
    if is_unit:
        group.create_dataset(field, data=eln_data["value"])
        if "unit" in eln_data.keys() and eln_data["unit"] is not None:
            group[field].attrs["units"] = eln_data["unit"]
    else:
        if isinstance(eln_data, datetime.datetime):
            eln_data = get_datetime_string(eln_data)
        group.create_dataset(field, data=eln_data)


def save_device_info(group: h5py.Group, eln_dict, keys: list):
    """
    Save device information from the ELN data to the HDF5 group.

    Args:
        group: The HDF5 group where the device information should be saved.
        eln_dict: The ELN data dictionary.
        keys: List of keys to find the device information.

    """

    if eln_field_exists(eln_dict, keys)[0]:
        device_info = group.create_group("device_information")
        device_info.attrs["NX_class"] = "NXfabrication"
        save_eln_field(device_info, "vendor", eln_dict, keys + ["vendor"])
        save_eln_field(device_info, "model", eln_dict, keys + ["model"])
        save_eln_field(
            device_info,
            "identifier",
            eln_dict,
            keys + ["identifier"],
        )


def eln_field_exists(
    eln_dict: dict, keys: list, is_unit: bool = False
) -> tuple[bool, Union[None, any]]:
    """
    Check if a field exists in the ELN data dictionary and return its value. Values of None also
    produce a False return.

    Args:
        eln_dict: The ELN data dictionary.
        keys: List of keys to navigate through the ELN data dictionary to find the desired field.
        is_unit: If True, field has a unit and is split into value and unit subfields
          (default False).

    Returns:
        True if the field exists, False otherwise. If True, also returns the field value.
    """

    cur_eln_field = eln_dict
    for key in keys:
        if key not in cur_eln_field.keys():
            return False, None

        cur_eln_field = cur_eln_field[key]
    # check if field is not None (also for unit fields)
    if cur_eln_field is None or (is_unit and (cur_eln_field["value"] is None)):
        return False, None
    return True, cur_eln_field


def write_object_to_nexus(obj, group: h5py.Group):
    """
    Write a dataclass or dictionary to a NeXus group.
    Args:
        object: The dataclass or dictionary to be written.
        group: The HDF5 group where the object should be written.

    """
    obj_dict = obj if isinstance(obj, dict) else obj.__dict__

    for key, val in obj_dict.items():
        if is_dataclass(val) or isinstance(val, dict):
            subgroup = group.create_group(key)
            subgroup.attrs["NX_class"] = "NXcollection"
            write_object_to_nexus(val, subgroup)
        else:
            if isinstance(val, datetime.datetime):
                val = get_datetime_string(val)
            group.create_dataset(key, data=val)
