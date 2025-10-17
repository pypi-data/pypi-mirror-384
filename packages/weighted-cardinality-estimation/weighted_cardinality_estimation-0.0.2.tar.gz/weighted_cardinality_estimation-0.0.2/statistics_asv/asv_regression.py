from .common import IMPLS

SKETCH_SIZE = 1000

class RegressionSuite:
    param_names = ['sketch type']
    params = [list(IMPLS.keys())]

    def setup(self, impl_name: str):
        seeds = list(range(1,SKETCH_SIZE+1))
        self.instance = IMPLS[impl_name](SKETCH_SIZE, seeds)
        self.instance.add("this is a single element.", 1.0)

    def track_estimate(self, impl_name):
        # This is done to see if estimate changed, 
        # I want to see if my changes did any change to the estimation at all.
        return self.instance.estimate()
    track_estimate.benchmark_name = f"regression.track_estimate" # type: ignore
    track_estimate.pretty_name = f"Sketch value after adding constant element."  # type: ignore
    track_estimate.unit = "units" # type: ignore
