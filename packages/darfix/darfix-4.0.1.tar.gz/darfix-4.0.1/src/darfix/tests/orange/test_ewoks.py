import os

import h5py
import numpy
import pytest
from ewoks import load_graph
from ewoks import save_graph
from ewokscore import execute_graph
from ewoksorange.bindings import ows_to_ewoks

from darfix.core.grainplot import MomentType
from darfix.tasks.blindsourceseparation import BlindSourceSeparation
from darfix.tasks.blindsourceseparation import Method
from darfix.tasks.dimensiondefinition import DimensionDefinition
from darfix.tasks.grainplot import GrainPlot
from darfix.tasks.hdf5_data_selection import HDF5DataSelection
from darfix.tasks.noiseremoval import NoiseRemoval
from darfix.tasks.roi import RoiSelection
from darfix.tasks.shiftcorrection import ShiftCorrection

try:
    from importlib.resources import files as resource_files
except ImportError:
    from importlib_resources import files as resource_files

from ..utils import generate_ewoks_task_inputs


def test_darfix_example2_hdf5(tmpdir):
    from orangecontrib.darfix import tutorials

    filename = resource_files(tutorials).joinpath("darfix_example_hdf.ows")

    hdf5_dataset_file = resource_files(tutorials).joinpath(
        "hdf5_dataset", "strain.hdf5"
    )
    assert os.path.exists(str(hdf5_dataset_file))
    inputs = [
        *generate_ewoks_task_inputs(
            HDF5DataSelection,
            raw_detector_data_path="/1.1/instrument/my_detector/data",
            raw_input_file=str(hdf5_dataset_file),
            raw_metadata_path="/1.1/instrument/positioners",
            treated_data_dir=str(tmpdir),
        ),
        *generate_ewoks_task_inputs(ShiftCorrection, shift=[0.1, 2]),
    ]
    graph = load_graph(str(filename), inputs=inputs)

    results = graph.execute(output_tasks=True)
    for node_id, task in results.items():
        assert task.succeeded, node_id


def get_inputs(input_filename: str):
    ds_inputs = generate_ewoks_task_inputs(
        HDF5DataSelection,
        raw_input_file=input_filename,
        raw_detector_data_path="/2.1/instrument/my_detector/data",
        raw_metadata_path="/2.1/instrument/positioners",
    )
    dim_inputs = generate_ewoks_task_inputs(
        DimensionDefinition,
        dims={
            0: {"name": "diffry", "kind": 2, "size": 8, "tolerance": 1e-09},
            1: {"name": "diffrx", "kind": 2, "size": 9, "tolerance": 1e-09},
        },
    )
    roi_inputs = generate_ewoks_task_inputs(
        RoiSelection, roi_origin=[198, 114], roi_size=[59, 133]
    )
    noise_inputs = generate_ewoks_task_inputs(
        NoiseRemoval,
        method="median",
        background_type="Data",
        bottom_threshold=0,
        kernel_size=3,
    )
    shiftcorr_inputs = generate_ewoks_task_inputs(ShiftCorrection, shift=[0.0, 0])

    return [*ds_inputs, *dim_inputs, *roi_inputs, *noise_inputs, *shiftcorr_inputs]


# TODO: Fix RockingCurves: it hangs at dataset.apply_fit
@pytest.mark.skip(reason="RockingCurves takes way too long")
def test_example_workflow1(tmpdir, silx_resources):
    """Execute workflow after converting it to an ewoks workflow"""
    ref_filename = silx_resources.getfile("reference_maps.h5")

    from orangecontrib.darfix import tutorials

    filename = resource_files(tutorials).joinpath("darfix_example1.ows")

    graph = ows_to_ewoks(filename)
    input_filename = silx_resources.getfile("input.h5")
    output_filename = str(tmpdir / "maps.h5")
    inputs = [
        *get_inputs(input_filename),
        *generate_ewoks_task_inputs(GrainPlot, filename=output_filename),
        *generate_ewoks_task_inputs(BlindSourceSeparation, method=Method.NICA),
    ]
    positioners = ("diffrx", "diffry")

    execute_graph(graph, inputs=inputs, outputs=[{"all": True}], merge_outputs=False)

    with h5py.File(ref_filename, "r") as ref_file:
        with h5py.File(output_filename, "r") as output_file:
            ref_entry = ref_file["entry"]
            output_entry = output_file["entry"]
            assert list(output_entry.keys()) == [
                "Mosaicity",
                "Orientation distribution",
                *positioners,
            ]

            for pos in positioners:
                for moment in MomentType.values():
                    numpy.testing.assert_allclose(
                        ref_entry[pos][moment][moment],
                        output_entry[pos][moment][moment],
                    )

            numpy.testing.assert_allclose(
                ref_entry["Mosaicity/Mosaicity"], output_entry["Mosaicity/Mosaicity"]
            )
            numpy.testing.assert_allclose(
                ref_entry["Orientation distribution/key/image"],
                output_entry["Orientation distribution/key/image"],
            )


@pytest.mark.parametrize("load_from_json", (True, False))
def test_example_workflow2(tmpdir, load_from_json, silx_resources):
    """Execute workflow after converting it to an ewoks workflow"""
    ref_filename = silx_resources.getfile("reference_maps.h5")

    from orangecontrib.darfix import tutorials

    input_filename = silx_resources.getfile("input.h5")
    output_filename = str(tmpdir / "maps.h5")
    inputs = [
        *get_inputs(input_filename),
        *generate_ewoks_task_inputs(GrainPlot, filename=output_filename),
    ]
    graph = ows_to_ewoks(
        resource_files(tutorials).joinpath("darfix_example_hdf.ows"), inputs=inputs
    )

    if load_from_json:
        json_filename = save_graph(
            graph, tmpdir / "darfix_example_hdf.json", representation="json"
        )
        graph = load_graph(str(json_filename))

    execute_graph(graph, outputs=[{"all": True}], merge_outputs=False)

    positioners = ("diffrx", "diffry")
    with h5py.File(ref_filename, "r") as ref_file:
        with h5py.File(output_filename, "r") as output_file:
            ref_entry = ref_file["entry"]
            output_entry = output_file["entry"]
            assert list(output_entry.keys()) == [
                "Mosaicity",
                "Orientation distribution",
                *positioners,
            ]

            for pos in positioners:
                for moment in MomentType.values():
                    numpy.testing.assert_allclose(
                        ref_entry[pos][moment][moment],
                        output_entry[pos][moment][moment],
                    )

            numpy.testing.assert_allclose(
                ref_entry["Mosaicity/Mosaicity"], output_entry["Mosaicity/Mosaicity"]
            )
            numpy.testing.assert_allclose(
                ref_entry["Orientation distribution/key/image"],
                output_entry["Orientation distribution/key/image"],
            )
