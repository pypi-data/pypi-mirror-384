import random
from typing import Callable, Union

from weighted_cardinality_estimation import BaseShiftedLogExpSketch, ExpSketch, FastExpSketch, BaseQSketch, FastGMExpSketch, FastQSketch, FastShiftedLogExpSketch, QSketch, QSketchDyn, BaseLogExpSketch, FastLogExpSketch

SketchType = Union[ExpSketch, FastExpSketch, FastGMExpSketch, BaseQSketch, FastQSketch, QSketchDyn, QSketch, BaseLogExpSketch, FastLogExpSketch, BaseShiftedLogExpSketch, FastShiftedLogExpSketch]
IMPLS: dict[str, Callable[..., SketchType]] = {
    "ExpSketch": lambda m, seeds: ExpSketch(m, seeds),
    "FastExpSketch": lambda m, seeds: FastExpSketch(m, seeds),
    "FastGMExpSketch": lambda m, seeds: FastGMExpSketch(m, seeds),
    "BaseQSketch(b=8)": lambda m, seeds: BaseQSketch(m, seeds, amount_bits=8),
    "FastQSketch(b=8)": lambda m, seeds: FastQSketch(m, seeds, amount_bits=8),
    "QSketchDyn(b=8)": lambda m, seeds: QSketchDyn(m, seeds, amount_bits=8, g_seed=42),
    "QSketch(b=8)": lambda m, seeds: QSketch(m, seeds, amount_bits=8),
    "BaseLogExpSketch(b=8, k=2)": lambda m, seeds: BaseLogExpSketch(m, seeds, amount_bits=8, logarithm_base=2),
    "FastLogExpSketch(b=8, k=2)": lambda m, seeds: FastLogExpSketch(m, seeds, amount_bits=8, logarithm_base=2),
    "BaseShiftedLogExpSketch(b=8, k=2)": lambda m, seeds: BaseShiftedLogExpSketch(m, seeds, amount_bits=8, logarithm_base=2),
    "FastShiftedLogExpSketch(b=8, k=2)": lambda m, seeds: FastShiftedLogExpSketch(m, seeds, amount_bits=8, logarithm_base=2),
}

def get_seeds(m: int):
    return [random.randint(1, 1_000_000) for _ in range(m)]