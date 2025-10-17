from .common import IMPLS, get_seeds


SKETCH_SIZE = 1000
AMOUNT_ELEMENTS_TO_ADD = 10_000

class AddManySuite:
    param_names = ['sketch type']
    params = [list(IMPLS.keys())]

    def setup(self, impl_name: str):
        self.instance = IMPLS[impl_name](SKETCH_SIZE, get_seeds(SKETCH_SIZE))
        self.elems = [f"elem_{i}" for i in range(AMOUNT_ELEMENTS_TO_ADD)]
        self.weights = [1.0] * AMOUNT_ELEMENTS_TO_ADD

    def time_add_many(self, impl_name):
        self.instance.add_many(self.elems, self.weights)

    time_add_many.benchmark_name = f"time.time_add_{AMOUNT_ELEMENTS_TO_ADD}_elems_to_sketch_size_{SKETCH_SIZE}" # type: ignore
    time_add_many.pretty_name = f"Time to add {AMOUNT_ELEMENTS_TO_ADD} to sketch size {SKETCH_SIZE}"  # type: ignore
    time_add_many.rounds=3 # type: ignore
    time_add_many.repeat=5 # type: ignore
