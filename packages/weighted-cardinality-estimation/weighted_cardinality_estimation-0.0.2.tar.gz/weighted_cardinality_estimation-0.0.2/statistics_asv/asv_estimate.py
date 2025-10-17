from .common import IMPLS, get_seeds


SKETCH_SIZE = 1000

class EstimateSuite:
    param_names = ['sketch type']
    params = [list(IMPLS.keys())]

    def setup(self, impl_name: str):
        self.instance = IMPLS[impl_name](SKETCH_SIZE, get_seeds(SKETCH_SIZE))
        self.instance.add("this is a single element.", 1.0)

    def time_estimate(self, impl_name):
        self.instance.estimate()

    time_estimate.benchmark_name = f"time.time_estimate_sketch_size_{SKETCH_SIZE}" # type: ignore
    time_estimate.pretty_name = f"Time to estimate sketch size {SKETCH_SIZE}"  # type: ignore
    time_estimate.rounds=5 # type: ignore
    time_estimate.repeat=10 # type: ignore
