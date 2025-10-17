import copy
import random
import pytest
from tests.test_sketches_functional import QSketch
from weighted_cardinality_estimation import BaseLogExpSketch, BaseQSketch, FastExpSketch, ExpSketch, FastGMExpSketch, BaseLogExpSketch, FastLogExpSketch, FastQSketch, QSketchDyn, BaseShiftedLogExpSketch, FastShiftedLogExpSketch


SKETCH_CONSTRUCTORS_WITH_SEEDS = [
    pytest.param(ExpSketch, id="ExpSketch"),
    pytest.param(FastExpSketch, id="FastExpSketch"),
    pytest.param(lambda m, seeds: FastGMExpSketch(m, seeds), id="FastGMExpSketch"),
    pytest.param(lambda m, seeds: BaseQSketch(m, seeds, 8), id="BaseQSketch"),
    pytest.param(lambda m, seeds: FastQSketch(m, seeds, amount_bits=8), id="FastQSketch"),
    pytest.param(lambda m, seeds: QSketchDyn(m, seeds, amount_bits=8, g_seed=42), id="QSketchDyn"),
    pytest.param(lambda m, seeds: QSketch(m, seeds, amount_bits=8), id="QSketch"),
    pytest.param(lambda m, seeds: BaseLogExpSketch(m, seeds, amount_bits=8, logarithm_base=2), id="BaseLogExpSketch"),
    pytest.param(lambda m, seeds: FastLogExpSketch(m, seeds, amount_bits=8, logarithm_base=2), id="FastLogExpSketch"),
    pytest.param(lambda m, seeds: BaseShiftedLogExpSketch(m, seeds, amount_bits=8, logarithm_base=2), id="BaseShiftedLogExpSketch"),
    pytest.param(lambda m, seeds: FastShiftedLogExpSketch(m, seeds, amount_bits=8, logarithm_base=2), id="FastShiftedLogExpSketch"),
]

SKETCH_CONSTRUCTORS_WITH_NO_SEEDS = [
    pytest.param(lambda m, seeds: ExpSketch(m, []), id="ExpSketch"),
    pytest.param(lambda m, seeds: FastExpSketch(m, []), id="FastExpSketch"),
    pytest.param(lambda m, seeds: FastGMExpSketch(m, []), id="FastGMExpSketch"),
    pytest.param(lambda m, seeds: BaseQSketch(m, [], 8), id="BaseQSketch"),
    pytest.param(lambda m, seeds: FastQSketch(m, [], amount_bits=8), id="FastQSketch"),
    pytest.param(lambda m, seeds: QSketchDyn(m, [], amount_bits=8, g_seed=42), id="QSketchDyn"),
    pytest.param(lambda m, seeds: QSketch(m, [], amount_bits=8), id="QSketch"),
    pytest.param(lambda m, seeds: BaseLogExpSketch(m, [], amount_bits=8, logarithm_base=2), id="BaseLogExpSketch"),
    pytest.param(lambda m, seeds: FastLogExpSketch(m, [], amount_bits=8, logarithm_base=2), id="FastLogExpSketch"),
    pytest.param(lambda m, seeds: BaseShiftedLogExpSketch(m, [], amount_bits=8, logarithm_base=2), id="BaseShiftedLogExpSketch"),
    pytest.param(lambda m, seeds: FastShiftedLogExpSketch(m, [], amount_bits=8, logarithm_base=2), id="FastShiftedLogExpSketch"),
]

SKETCH_CONSTRUCTORS = SKETCH_CONSTRUCTORS_WITH_NO_SEEDS + SKETCH_CONSTRUCTORS_WITH_SEEDS

@pytest.mark.parametrize("sketch_cls", SKETCH_CONSTRUCTORS)
def test_unitary(sketch_cls):
    M=5
    seeds = [random.randint(1,10000000) for _ in range(M)]
    sketch = sketch_cls(M, seeds)
    sketch.add("I am just a simple element.", weight=1)

    estimate = sketch.estimate()
    assert estimate > 0.001

@pytest.mark.parametrize("sketch_cls", SKETCH_CONSTRUCTORS_WITH_SEEDS)
def test_estimate_adding_duplicate_does_not_change_estimation(sketch_cls):
    M=5
    seeds = [random.randint(1,10000000) for _ in range(M)]
    sketch = sketch_cls(M, seeds)
    sketch.add("I am just a simple element.", weight=1)

    estimate = sketch.estimate()
    sketch.add("I am just a simple element.", weight=1)

    assert estimate == sketch.estimate()

@pytest.mark.parametrize("sketch_cls", SKETCH_CONSTRUCTORS_WITH_SEEDS)
def test_no_seeds_is_the_same_as_range_seeds(sketch_cls):
    M=3
    seeds = [1,2,3]
    sketch1 = sketch_cls(M, seeds)
    sketch1.add("I am just a simple element.", weight=1)

    sketch2 = sketch_cls(M, [])
    sketch2.add("I am just a simple element.", weight=1)

    assert sketch1.estimate() == sketch2.estimate()
    assert sketch1.__getstate__() == sketch2.__getstate__()


@pytest.mark.parametrize("sketch_cls", SKETCH_CONSTRUCTORS)
def test_copy_produces_same_estimate(sketch_cls):
    # here i just want to make some basic contract that it holds to ANY standard lol
    m = 5
    seeds = [1, 2, 3, 4, 5]
    original_sketch = sketch_cls(m, seeds)
    original_sketch.add("A single test element", weight=1.0)
    original_estimate = original_sketch.estimate()
    
    copied_sketch = copy.copy(original_sketch)
    copied_estimate = copied_sketch.estimate()

    assert original_estimate == copied_estimate
    assert original_sketch is not copied_sketch

@pytest.mark.parametrize("sketch_cls", SKETCH_CONSTRUCTORS)
def test_copy_has_identical_internal_state(sketch_cls):
    m = 5
    seeds = [1, 2, 3, 4, 5]
    original_sketch = sketch_cls(m, seeds)
    original_sketch.add("some element", weight=2.5)

    copied_sketch = copy.copy(original_sketch)

    # this test is essentialy, from testing point of view, pointless, but is good for dev.
    original_state = original_sketch.__getstate__()
    copied_state = copied_sketch.__getstate__()

    assert original_state == copied_state

@pytest.mark.parametrize("sketch_cls", SKETCH_CONSTRUCTORS)
def test_copy_different_memory_objects(sketch_cls):
    m = 5
    seeds = [1, 2, 3, 4, 5]
    original_sketch = sketch_cls(m, seeds)
    original_sketch.add("some element", weight=2.5)

    copied_sketch = copy.copy(original_sketch)
    # here i want to check if internal stuff is different so it is important to save it
    original_estimate = original_sketch.estimate() 
    copied_sketch.add("new element", weight=1)
    assert original_estimate == original_sketch.estimate()

@pytest.mark.parametrize("sketch_cls", SKETCH_CONSTRUCTORS)
def test_copy_independently_the_same_structures(sketch_cls):
    m = 5
    seeds = [1, 2, 3, 4, 5]
    original_sketch = sketch_cls(m, seeds)
    original_sketch.add("some element", weight=2.5)

    copied_sketch = copy.copy(original_sketch)
    # here I want to see if all internal stuff is the same so adding new element will cause same effect.
    copied_sketch.add("new element", weight=1)
    original_sketch.add("new element", weight=1)

    assert original_sketch.estimate() == copied_sketch.estimate()

@pytest.mark.parametrize("sketch_cls", SKETCH_CONSTRUCTORS)
def test_memory_usage_sanity_check(sketch_cls):
    m = 5
    seeds = [1, 2, 3, 4, 5]
    original_sketch = sketch_cls(m, seeds)
    original_sketch.add("some element", weight=2.5)

    total_memory = original_sketch.memory_usage_total()
    write_memory = original_sketch.memory_usage_write()
    estimate_memory = original_sketch.memory_usage_estimate()
    assert total_memory > write_memory
    assert write_memory > 0
    assert estimate_memory > 0
