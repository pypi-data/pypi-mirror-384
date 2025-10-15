from __future__ import annotations

import logging
import os
from typing import Literal

from ewokscore import Task
from ewokscore.missing_data import MISSING_DATA
from ewokscore.missing_data import MissingData
from ewokscore.model import BaseInputModel
from pydantic import ConfigDict
from silx.io.dictdump import dicttonx

from darfix import dtypes

from ..core.dataset import ImageDataset
from ..core.grainplot import OrientationDistData
from ..core.grainplot import OrientationDistImage
from ..core.grainplot import compute_mosaicity
from ..core.grainplot import generate_grain_maps_nxdict

_logger = logging.getLogger(__file__)


class Inputs(BaseInputModel):
    model_config = ConfigDict(use_attribute_docstrings=True)
    dataset: dtypes.Dataset
    """ Input dataset containing a stack of images """
    dimensions: tuple[int, int] = (0, 1)
    """Dimension indices to use for the maps. Default is (0, 1), which means the two first dimensions."""
    save_maps: bool = True
    """Whether to save the maps to file. Default is True."""
    filename: str | MissingData = MISSING_DATA
    """Only used if save_maps is True. Filename to save the maps to. Default is 'maps.h5' in the dataset directory."""
    orientation_img_origin: Literal["dims", "center"] = "dims"
    "Origin for the orientation distribution image. Can be 'dims', 'center' or None. Default is 'dims'."


class GrainPlot(
    Task,
    input_model=Inputs,
    output_names=["dataset"],
):
    """Generates and saves maps of Center of Mass, FWHM, Skewness, Kurtosis, Orientation distribution and Mosaicity."""

    def run(self):

        inputs = Inputs(**self.get_input_values())

        default_filename = os.path.join(inputs.dataset.dataset._dir, "maps.h5")
        filename: str = self.get_input_value("filename", default_filename)

        dataset: ImageDataset = inputs.dataset.dataset
        moments = dataset.apply_moments()

        # mosaicity and orientation can only be computed for 2D+ datasets
        if dataset.dims.ndim > 1:
            dimension1, dimension2 = inputs.dimensions

            mosaicity = compute_mosaicity(
                moments,
                x_dimension=dimension1,
                y_dimension=dimension2,
            )

            orientation_dist_data = OrientationDistData(
                dataset,
                x_dimension=dimension1,
                y_dimension=dimension2,
            )
            assert orientation_dist_data is not None

            orientation_dist_image = OrientationDistImage(
                xlabel=orientation_dist_data.x_label,
                ylabel=orientation_dist_data.y_label,
                scale=orientation_dist_data.rgb_key_plot_scale(),
                origin=orientation_dist_data.origin(inputs.orientation_img_origin),
                data=orientation_dist_data.data,
                as_rgb=orientation_dist_data.rgb_key,
                contours=dict(),
            )
        else:
            mosaicity = None
            orientation_dist_image = None

        # Save data if asked
        if inputs.save_maps:
            nxdict = generate_grain_maps_nxdict(
                dataset, mosaicity, orientation_dist_image
            )
            dicttonx(nxdict, filename)

        self.outputs.dataset = dtypes.Dataset(
            dataset=dataset,
            indices=inputs.dataset.indices,
            bg_indices=inputs.dataset.bg_indices,
            bg_dataset=inputs.dataset.bg_dataset,
        )
