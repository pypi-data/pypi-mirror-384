import pickle
from .common import IMPLS, get_seeds


SKETCH_SIZE = 1_000

class MemorySuite:
    param_names = ['sketch type']
    params = [list(IMPLS.keys())]

    def setup(self, impl_name: str):
        self.instance = IMPLS[impl_name](SKETCH_SIZE, get_seeds(SKETCH_SIZE))
        self.instance.add("this is a single element.", 1.0)

    def track_serialization_size(self, impl_name):
        serialized_object = pickle.dumps(self.instance)
        return len(serialized_object)
    track_serialization_size.unit = 'bytes' # type: ignore
    track_serialization_size.benchmark_name = f"memory.track_memory_serialization_sketch_size_{SKETCH_SIZE}" # type: ignore
    track_serialization_size.pretty_name = f"Serialization size of sketch with size {SKETCH_SIZE}"  # type: ignore


    def track_total_memory(self, impl_name):
        return self.instance.memory_usage_total()
    track_total_memory.unit = 'bytes' # type: ignore
    track_total_memory.benchmark_name = f"memory.track_memory_total_sketch_size_{SKETCH_SIZE}" # type: ignore
    track_total_memory.pretty_name = f"Total memory used of sketch of size {SKETCH_SIZE}"  # type: ignore

    
    def track_write_memory(self, impl_name):
        return self.instance.memory_usage_write()
    track_write_memory.unit = 'bytes' # type: ignore
    track_write_memory.benchmark_name = f"memory.track_memory_write_sketch_size_{SKETCH_SIZE}" # type: ignore
    track_write_memory.pretty_name = f"Write-able memory used for sketch of size {SKETCH_SIZE}"  # type: ignore

    def track_estimate_memory(self, impl_name):
        return self.instance.memory_usage_estimate()
    track_estimate_memory.unit = 'bytes' # type: ignore
    track_estimate_memory.benchmark_name = f"memory.track_memory_estimate_sketch_size_{SKETCH_SIZE}" # type: ignore
    track_estimate_memory.pretty_name = f"memory used for estimation in sketch of size {SKETCH_SIZE}"  # type: ignore
