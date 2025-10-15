import logging
import sys, os

os.environ.setdefault("XPCSCORR_LOG_TO_CLI", "1")
os.environ.setdefault("XPCSCORR_LOG_TO_FILE", "0")

logger = logging.getLogger("xpcscorr")
logger.propagate = False           # <--- Set propagate to False immediately after getting the logger
logger.setLevel(logging.INFO)

if logger.hasHandlers():
    logger.handlers.clear()

if os.environ["XPCSCORR_LOG_TO_FILE"].lower() in ("1", "true", "yes", "on"):
    file_handler = logging.FileHandler("xpcscorr.log")
    file_formatter = logging.Formatter('%(asctime)s %(levelname)s: %(message)s')
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)

if os.environ["XPCSCORR_LOG_TO_CLI"].lower() in ("1", "true", "yes", "on"):
    stream_handler = logging.StreamHandler(sys.stdout)
    stream_formatter = logging.Formatter('%(asctime)s %(levelname)s: %(message)s')
    stream_handler.setFormatter(stream_formatter)
    logger.addHandler(stream_handler)

# Easy access to main correlator functions
from .correlators.dense.base import _create_correlator_function
from .correlators.dense.reference import CorrelatorDenseReference
from .correlators.dense.chunked import CorrelatorDenseChunked

correlator_dense_reference = _create_correlator_function(CorrelatorDenseReference)
correlator_dense_chunked = _create_correlator_function(CorrelatorDenseChunked)

# Make these two functions part of the public API so autodoc will include them
__all__ = [
    "correlator_dense_reference",
    "correlator_dense_chunked",
]