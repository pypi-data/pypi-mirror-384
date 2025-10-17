import numpy as np
from .common import IMPLS, get_seeds


SKETCH_SIZE = 400
AMOUNT_ELEMENTS_TO_ADD = 1000
STATISTICAL_RUNS = 10_000
TIMEOUT=900

class AccuracySuite:
    elems: list[str]
    weights: list[float]
    true_cardinality: float

    param_names = ['implementation']
    params = [list(IMPLS.keys())]

    def setup_cache(self):
        self.elems = [f"elem_{i}" for i in range(AMOUNT_ELEMENTS_TO_ADD)]
        self.weights = [1.0] * AMOUNT_ELEMENTS_TO_ADD
        self.true_cardinality = sum(self.weights)
        stats = {
            impl_name: self._calculate_all_statistics(impl_name) 
            for impl_name in IMPLS.keys()
        }
        return stats
    
    def _calculate_all_statistics(self, impl_name) -> dict:
        estimates = []
        for _ in range(STATISTICAL_RUNS):
            s = IMPLS[impl_name](SKETCH_SIZE, get_seeds(SKETCH_SIZE))
            s.add_many(self.elems, self.weights)
            estimates.append(s.estimate())
        
        mean_estimate = np.mean(estimates)
        std_dev = np.std(estimates)
        relative_errors = [
            abs(estimate - self.true_cardinality) / self.true_cardinality 
            for estimate in estimates
        ]
        
        return {
            'true_cardinality': self.true_cardinality,
            'mean': mean_estimate,
            'mean_relative_error': np.mean(relative_errors),
            'coeff_of_variation': (std_dev / mean_estimate) if mean_estimate != 0 else 0.0
        }
    
    def track_mean_estimate(self, stats, impl_name):
        return stats[impl_name]['mean']
    track_mean_estimate.unit = 'units' # type: ignore
    track_mean_estimate.benchmark_name = f"accuracy.track_mean_of_{STATISTICAL_RUNS}_estimates_sketch_size_{SKETCH_SIZE}" # type: ignore
    track_mean_estimate.pretty_name = f"Mean of estimates {STATISTICAL_RUNS} sketches with size={SKETCH_SIZE}"  # type: ignore
    track_mean_estimate.timeout=TIMEOUT # type: ignore

    def track_relative_error(self, stats, impl_name):
        return stats[impl_name]['mean_relative_error'] * 100
    track_relative_error.unit = '%' # type: ignore
    track_relative_error.benchmark_name = f"accuracy.track_mean_relative_error_sketch_size_{SKETCH_SIZE}" # type: ignore
    track_relative_error.pretty_name = f"Mean relative error for sketch_size={SKETCH_SIZE}"  # type: ignore
    track_relative_error.timeout=TIMEOUT # type: ignore


    def track_coeff_of_variation(self, stats, impl_name):
        return stats[impl_name]['coeff_of_variation'] * 100
    track_coeff_of_variation.unit = '%' # type: ignore
    track_coeff_of_variation.benchmark_name = f"accuracy.track_CV_of_sketch_size_{SKETCH_SIZE}" # type: ignore
    track_coeff_of_variation.pretty_name = f"Coefficient of variation for sketch_size={SKETCH_SIZE}"  # type: ignore
    track_coeff_of_variation.timeout=TIMEOUT # type: ignore
