from __future__ import annotations

import logging
from typing import Tuple

import h5py

_logger = logging.getLogger(__file__)


def find_scan_names(file: str) -> Tuple[str, ...]:
    with h5py.File(file) as h5file:
        return tuple(
            entry.name.lstrip("/")
            for entry in h5file.values()
            if isinstance(entry, h5py.Group)
        )


def find_detector_name(scan: h5py.Group) -> str | None:
    instrument_group = scan.get("instrument", None)
    if not isinstance(instrument_group, h5py.Group):
        _logger.warning(
            f"Could not find group 'instrument' in {scan.file}::{scan.name}"
        )
        return None

    for instrument_name, instrument in instrument_group.items():
        if not isinstance(instrument, h5py.Group):
            continue

        if instrument.attrs.get("NX_class") != "NXdetector":
            continue

        instrument_type = instrument.get("type")
        if not isinstance(instrument_type, h5py.Dataset):
            continue
        if instrument_type[()].decode() == "lima" and "image" in instrument:
            # Found the LIMA detector
            return instrument_name

    _logger.warning(
        f"Could not find valid detector in {scan.file}::{instrument_group.name} among {tuple(instrument_group.keys())}"
    )
    return None
