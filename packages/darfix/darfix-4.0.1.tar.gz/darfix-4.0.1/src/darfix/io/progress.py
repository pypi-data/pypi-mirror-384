from typing import Iterable

import tqdm


def display_progress(iterable: Iterable, desc: str):
    return tqdm.tqdm(iterable, desc=desc)
