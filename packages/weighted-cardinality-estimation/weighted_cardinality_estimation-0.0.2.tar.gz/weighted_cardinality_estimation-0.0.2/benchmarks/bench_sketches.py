# bench_sketches.py
# This file is used for benchmarking sketches for time and compare them.
import itertools as it
import random
from typing import Callable, Literal
import pytest

from weighted_cardinality_estimation import ExpSketch, FastExpSketch, FastQSketch

IMPLS = [
    ("ExpSketch", ExpSketch), 
    ("FastExpSketch", FastExpSketch), 
    ("FastQSketch", lambda m, seeds: FastQSketch(m, seeds, 8))
]
POSSIBLE_STRUCTURE_SIZE = [100, 400]
POSSIBLE_AMOUNT_ELEMENTS = [10_000]

PARAMS = []
for impl in IMPLS:
    for structure_size in POSSIBLE_STRUCTURE_SIZE:
        for amount_elements in POSSIBLE_AMOUNT_ELEMENTS:
            PARAMS.append(
                pytest.param(*impl, structure_size, amount_elements, id=f"{impl[0]}::{structure_size}::{amount_elements}") 
            )

def build_instances(cls, m, k):
    state = random.getstate()
    random.seed(42)
    instances = []
    for _ in range(k):
        seeds = [random.randint(1,1_000_000) for _ in list(range(m))]
        instances.append(cls(m, seeds))
    random.setstate(state)
    return instances

def generate_elems(amount_elements: int) -> list[str]:
    return [f"e{i}" for i in range(amount_elements)] 

def generate_uniform_weights(amount_elements: int) -> list[float]:
    state = random.getstate()
    random.seed(42)
    weights = [random.random() for _ in range(amount_elements)]
    random.setstate(state)
    return weights

@pytest.mark.parametrize("name,cls,structure_size,amount_elements", PARAMS)
def test_add_many_uniform(benchmark, name, cls, structure_size, amount_elements):
    ROUNDS = 10
    elems = generate_elems(amount_elements)
    weights = generate_uniform_weights(amount_elements)
    insts = build_instances(cls=cls, m=structure_size, k=ROUNDS) 
    iters = iter(insts)

    def run_once():
        s = next(iters)   
        s.add_many(elems, weights)

    benchmark.group = f"add_many[uniform]::{structure_size}::{amount_elements}"
    benchmark.pedantic(run_once, iterations=1, rounds=ROUNDS)

@pytest.mark.parametrize("name,cls,structure_size,amount_elements", PARAMS)
def test_estimate_only(benchmark, name, cls, structure_size, amount_elements):
    ROUNDS = 1000
    elems = generate_elems(amount_elements)
    weights = generate_uniform_weights(amount_elements)
    insts = build_instances(cls=cls, m=structure_size, k=ROUNDS) 
    for inst in insts:
        inst.add_many(elems, weights)

    iters = iter(insts)
    def run_once():
        s = next(iters)   
        s.estimate()   

    benchmark.group = f"estimate::{structure_size}"
    benchmark.pedantic(run_once, iterations=1, rounds=ROUNDS)
