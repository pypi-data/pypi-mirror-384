"""Init module for ml diagnostics."""

# Import the upfront API for users
from . import api
from . import core


__path__ = __import__('pkgutil').extend_path(__path__, __name__)


machinelearning_run = api.machinelearning_run
metrics = api.metrics
xprof = core.xprof.Xprof
