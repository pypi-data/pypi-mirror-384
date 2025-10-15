import importlib.metadata
import logging
import sys
from datetime import datetime

import h5py
import numpy
from silx.io.dictdump import dicttoh5
from silx.io.dictdump import h5todict

_logger = logging.getLogger(__file__)

_VERSION = importlib.metadata.version("darfix")


def assert_string(s, enums):
    s += " has to be "
    for app in enums:
        if app == enums[0]:
            s += "`" + app + "`"
        elif app == enums[-1]:
            s += "or `" + app + "`"
        else:
            s += ", `" + app + "`"
    return s


# Print iterations progress
def advancement_display(
    ncurrent,
    ntotal,
    prefix="",
    suffix="",
    decimals=1,
    length=100,
    fill="\u2588",
    left="-",
):
    """
    Call in a loop to create terminal progress bar
    @params:
        ncurrent   - Required  : current N (Int)
        ntotal     - Required  : total expected N (Int)
        prefix     - Optional  : prefix string (Str)
        suffix     - Optional  : suffix string (Str)
        decimals   - Optional  : positive number of decimals in percent complete (Int)
        length     - Optional  : character length of bar (Int)
        fill       - Optional  : bar fill character (Str)
        left       - Optional  : bar fill character (Str)
    """
    if ntotal:
        ncurrent = min(ncurrent, ntotal)
        progress = ncurrent / float(ntotal)
    else:
        progress = ncurrent + 1
    percent_fmt = "{0:." + str(decimals) + "f}"
    percent = percent_fmt.format(100 * progress)
    filledLength = int(length * min(progress, 1))
    leftLength = length - filledLength
    bar = fill * filledLength + left * leftLength
    sys.stdout.write("\r%s |%s| %s%% %s\r" % (prefix, bar, percent, suffix))
    # Print New Line on Complete
    if ncurrent >= ntotal:
        sys.stdout.write("\n")


def write_maps(
    h5_file,
    list_of_maps,
    default_map,
    entry,
    processing_order,
    data_path="/",
    overwrite=True,
):
    """
    Write a stack of components and its parameters into .h5

    :param str h5_file: path to the hdf5 file
    :param str entry: entry name
    :param dict dimensions: Dictionary with the dimensions names and values
    :param numpy.ndarray W: Matrix with the rocking curves values
    :param numpy.ndarray data: Stack with the components
    :param int processing_order: processing order of treatment
    :param str data_path: path to store the data
    """
    process_name = "process_" + str(processing_order)

    def get_interpretation(my_data):
        """Return hdf5 attribute for this type of data"""
        if isinstance(my_data, numpy.ndarray):
            if my_data.ndim == 1:
                return "spectrum"
            elif my_data.ndim in (2, 3):
                return "image"
        return None

    def save_key(path_name, key_path, value, overwrite=True):
        """Save the given value to the associated path. Manage numpy arrays
        and dictionaries"""
        key_path = key_path.replace(".", "/")
        # save if is dict
        if isinstance(value, dict):
            h5_path = "/".join((path_name, key_path))
            dicttoh5(
                value, h5file=h5_file, h5path=h5_path, overwrite_data=True, mode="a"
            )
        else:
            with h5py.File(h5_file, "a") as h5f:
                nx = h5f.require_group(path_name)
                if overwrite and key_path in nx:
                    del nx[key_path]
                try:
                    nx[key_path] = value
                except TypeError as e:
                    _logger.error("Unable to write", str(key_path), "reason is", str(e))
                else:
                    interpretation = get_interpretation(value)
                    if interpretation:
                        nx[key_path].attrs["interpretation"] = interpretation

    with h5py.File(h5_file, "a") as h5f:
        h5f.attrs["default"] = entry
        nx_entry = h5f.require_group("/".join((data_path, entry)))
        nx_entry.attrs["NX_class"] = "NXentry"
        nx_entry.attrs["default"] = "data"

        nx_process = nx_entry.require_group(process_name)
        nx_process.attrs["NX_class"] = "NXprocess"
        if overwrite:
            for key in ("program", "version", "date", "processing_order"):
                if key in nx_process:
                    del nx_process[key]
        nx_process["program"] = "darfix"
        nx_process["version"] = _VERSION
        nx_process["date"] = datetime.now().replace(microsecond=0).isoformat()
        nx_process["processing_order"] = numpy.int32(processing_order)

        results = nx_process.require_group("results")
        results.attrs["NX_class"] = "NXcollection"
        nx_data = nx_entry.require_group("data")
        nx_data.attrs["NX_class"] = "NXdata"
        default = list_of_maps[default_map]
        source_addr = entry + "/" + process_name + "/results/" + default_map
        results.attrs["target"] = default_map
        save_key(results.name, default_map, default)
        save_key(nx_data.name, default_map, h5f[source_addr])

        for _map in list_of_maps:
            if _map == default_map:
                continue
            if isinstance(list_of_maps[_map], dict):
                maps = results.require_group(_map)
                maps.attrs["NX_class"] = "NXcollection"
                for method in list_of_maps[_map]:
                    save_key(maps.name, method, list_of_maps[_map][method])
            else:
                save_key(results.name, _map, list_of_maps[_map])


def read_components(h5_file):
    """
    Read a stack of components and its parameters from a Nexus file.

    :param str h5_file: path to the hdf5 file
    """
    with h5py.File(h5_file, "r") as nx:
        # find the default NXentry group
        nx_entry = nx[nx.attrs["default"]]
        # find the default NXdata group
        nx_process = nx_entry["process_1"]
        input_data = nx_process["dimensions"]
        dimensions = h5todict(
            h5_file, nx.attrs["default"] + "/process_1/dimensions", asarray=False
        )
        input_data = nx_process["values"]
        values = {}
        for key in input_data.keys():
            values[key] = numpy.array(list(input_data[key]))
        results = nx_process["results"]
        components = numpy.array(list(results["components"]))
        W = numpy.array(list(results["W"]))

    return dimensions, components, W, values


def write_components(
    h5_file,
    entry,
    dimensions,
    W,
    data,
    values,
    processing_order,
    data_path="/",
    overwrite=True,
):
    """
    Write a stack of components and its parameters into .h5

    :param str h5_file: path to the hdf5 file
    :param str entry: entry name
    :param dict dimensions: Dictionary with the dimensions names and values
    :param numpy.ndarray W: Matrix with the rocking curves values
    :param numpy.ndarray data: Stack with the components
    :param int processing_order: processing order of treatment
    :param str data_path: path to store the data
    """
    process_name = "process_" + str(processing_order)

    def get_interpretation(my_data):
        """Return hdf5 attribute for this type of data"""
        if isinstance(my_data, numpy.ndarray):
            if my_data.ndim == 1:
                return "spectrum"
            elif my_data.ndim in (2, 3):
                return "image"
        return None

    def save_key(path_name, key_path, value, overwrite=True):
        """Save the given value to the associated path. Manage numpy arrays
        and dictionaries"""
        key_path = key_path.replace(".", "/")
        # save if is dict
        if isinstance(value, dict):
            h5_path = "/".join((path_name, key_path))
            dicttoh5(
                value, h5file=h5_file, h5path=h5_path, overwrite_data=True, mode="a"
            )
        else:
            with h5py.File(h5_file, "a") as h5f:
                nx = h5f.require_group(path_name)
                if overwrite and key_path in nx:
                    del nx[key_path]
                try:
                    nx[key_path] = value
                except TypeError as e:
                    _logger.error("Unable to write", str(key_path), "reason is", str(e))
                else:
                    interpretation = get_interpretation(value)
                    if interpretation:
                        nx[key_path].attrs["interpretation"] = interpretation

    with h5py.File(h5_file, "a") as h5f:
        h5f.attrs["default"] = entry
        nx_entry = h5f.require_group("/".join((data_path, entry)))
        nx_entry.attrs["NX_class"] = "NXentry"
        nx_entry.attrs["default"] = "data"

        nx_process = nx_entry.require_group(process_name)
        nx_process.attrs["NX_class"] = "NXprocess"
        if overwrite:
            for key in ("program", "version", "date", "processing_order"):
                if key in nx_process:
                    del nx_process[key]
        nx_process["program"] = "darfix"
        nx_process["version"] = _VERSION
        nx_process["date"] = datetime.now().replace(microsecond=0).isoformat()
        nx_process["processing_order"] = numpy.int32(processing_order)

        nx_parameters = nx_process.require_group("dimensions")
        nx_parameters.attrs["NX_class"] = "NXparameters"
        dicttoh5(dimensions, h5f, entry + "/" + process_name + "/dimensions")

        nx_values = nx_process.require_group("values")
        nx_values.attrs["NX_class"] = "NXparameters"
        for key, value in values.items():
            save_key(nx_values.name, key_path=key, value=value)

        results = nx_process.require_group("results")
        results.attrs["NX_class"] = "NXcollection"

        nx_data = nx_entry.require_group("data")
        nx_data.attrs["NX_class"] = "NXdata"
        nx_data.attrs["signal"] = "components"
        source_addr = entry + "/" + process_name + "/results/components"
        results.attrs["target"] = "components"

        save_key(results.name, "W", W)
        save_key(results.name, "components", data)
        save_key(nx_data.name, "components", h5f[source_addr])


def create_nxdata_dict(
    signal: numpy.ndarray,
    signal_name: str,
    axes=None,
    axes_names=None,
    axes_long_names=None,
    rgba=False,
):
    nxdata = {signal_name: signal, "@signal": signal_name, "@NX_class": "NXdata"}

    if axes is not None:
        nxdata.update(
            {"@axes": axes_names, axes_names[0]: axes[0], axes_names[1]: axes[1]}
        )

        if axes_long_names is not None:
            nxdata.update(
                {
                    axes_names[0] + "@long_name": axes_long_names[0],
                    axes_names[1] + "@long_name": axes_long_names[1],
                }
            )

    if rgba:
        nxdata[signal_name + "@interpretation"] = "rgba-image"
        nxdata[signal_name + "@CLASS"] = "IMAGE"

    return nxdata
