from importlib import metadata as _md
from ._core import ExpSketch # type: ignore
from ._core import FastExpSketch # type: ignore
from ._core import FastGMExpSketch # type: ignore
from ._core import BaseQSketch # type: ignore
from ._core import FastQSketch # type: ignore
from ._core import QSketchDyn # type: ignore
from ._core import QSketch # type: ignore
from ._core import BaseLogExpSketch # type: ignore
from ._core import FastLogExpSketch # type: ignore
from ._core import BaseShiftedLogExpSketch # type: ignore
from ._core import FastShiftedLogExpSketch # type: ignore

__all__ = [
    "ExpSketch", 
    "FastExpSketch", 
    "FastGMExpSketch",
    "BaseQSketch", 
    "FastQSketch", 
    "QSketchDyn", 
    "QSketch",
    "BaseLogExpSketch",
    "FastLogExpSketch",
    "BaseShiftedLogExpSketch",
    "FastShiftedLogExpSketch",
    "__version__"
]
__version__ = _md.version(__name__)
# __version__ = "0.0.0-debug" # I USE IT IN DEBUG MODE
