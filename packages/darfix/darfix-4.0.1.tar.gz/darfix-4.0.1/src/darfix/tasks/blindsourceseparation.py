from __future__ import annotations

import os

import numpy
from ewokscore import Task
from ewokscore.missing_data import MISSING_DATA
from ewokscore.missing_data import MissingData
from ewokscore.model import BaseInputModel
from pydantic import ConfigDict
from pydantic import Field
from silx.utils.enum import Enum as _Enum

from darfix import dtypes
from darfix.io.utils import write_components


class Method(_Enum):
    """
    Different blind source separation approaches that can be applied
    """

    PCA = "PCA"

    NICA = "NICA"

    NMF = "NMF"

    NICA_NMF = "NICA_NMF"

    @classmethod
    def from_value(cls, value):
        # ensure backward compatibility with ewoks <= 1.0
        # the value of the Method use to be the description / tooltip
        for method, desc in Method._descriptions().items():
            if value == desc:
                return method
        return super().from_value(value)

    @staticmethod
    def _descriptions() -> dict:
        return {
            Method.PCA: (
                "The process of computing the principal components \n"
                "and using them to perform a change of basis on the data"
            ),
            Method.NICA: "Find components independent from each other and non-negative",
            Method.NMF: (
                "Non-negative matrix factorization factorizes the data matrix into \n"
                "two matrices, with the property that all three matrices have no negative elements"
            ),
            Method.NICA_NMF: "Apply Non-negative ICA followed by NMF",
        }

    @staticmethod
    def get_description(method) -> str:
        method = Method.from_value(method)
        if method in Method._descriptions():
            return Method._descriptions()[method]
        else:
            raise NotImplementedError


class Inputs(BaseInputModel):
    model_config = ConfigDict(use_attribute_docstrings=True)
    dataset: dtypes.Dataset
    """ Input dataset containing a stack of images """
    method: Method
    "Method to use for blind source separation"
    n_comp: int | MissingData = Field(
        default=MISSING_DATA, description="Number of components to extract"
    )
    save: bool | MissingData = MISSING_DATA
    processing_order: int | MissingData = MISSING_DATA


class BlindSourceSeparation(
    Task,
    input_model=Inputs,
    output_names=["dataset", "comp", "W"],
):
    """Perform blind source separation on a Darfix dataset.
    Blind source separation (BSS) comprises all techniques that try to decouple a set of source signals from a set of mixed signals with unknown (or very little) information.

    Supported methods are PCA, NICA, NMF and NICA_NMF.

    Related article  : https://pmc.ncbi.nlm.nih.gov/articles/PMC10161887/#sec3.3.3

    """

    def run(self):
        if not isinstance(self.inputs.dataset, dtypes.Dataset):
            raise TypeError(
                f"'dataset' input should be an instance of Dataset. Got {type(self.inputs.dataset)}."
            )
        dataset = self.inputs.dataset.dataset
        indices = self.inputs.dataset.indices
        bg_indices = self.inputs.dataset.bg_indices
        bg_dataset = self.inputs.dataset.bg_dataset

        n_comp = self.get_input_value("n_comp", None)
        method = Method.from_value(self.inputs.method)
        if method == Method.PCA:
            comp, W = dataset.pca(n_comp, indices=indices)
        elif method == Method.NICA:
            comp, W = dataset.nica(n_comp, indices=indices)
        elif method == Method.NMF:
            comp, W = dataset.nmf(n_comp, indices=indices)
        elif method == Method.NICA_NMF:
            comp, W = dataset.nica_nmf(n_comp, indices=indices)
        else:
            raise ValueError("BSS method not managed")
        n_comp = comp.shape[0]
        shape = dataset.frame_shape
        comp = comp.reshape(n_comp, shape[0], shape[1])
        if bg_indices is not None:
            # If filter data is activated, the matrix W has reduced dimensionality, so reshaping is not possible
            # Create empty array with shape the total number of frames
            W = numpy.zeros((dataset.nframes, n_comp))
            # Set actual values of W where threshold of filter is True
            W[indices] = W
            W = W

        if self.get_input_value("save", False):
            write_components(
                h5file=os.path.join(dataset.dir, "components.h5"),
                entry="entry",
                dimensions=dataset.dims.to_dict(),
                W=W,
                data=comp,
                values=dataset.get_dimensions_values(),
                processing_order=self.get_input_value("processing_order", 0),
            )
        self.outputs.dataset = dtypes.Dataset(
            dataset=dataset,
            indices=indices,
            bg_indices=bg_indices,
            bg_dataset=bg_dataset,
        )

        self.outputs.W = W
        self.outputs.comp = comp
