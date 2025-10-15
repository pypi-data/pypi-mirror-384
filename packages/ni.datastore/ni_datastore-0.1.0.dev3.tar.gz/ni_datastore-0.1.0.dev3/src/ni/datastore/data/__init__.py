"""Public API for accessing the NI Data Store."""

from ni.datamonikers.v1.data_moniker_pb2 import Moniker
from ni.datastore.data._data_store_client import DataStoreClient
from ni.datastore.data._types._published_condition import PublishedCondition
from ni.datastore.data._types._published_measurement import PublishedMeasurement
from ni.datastore.data._types._step import Step
from ni.datastore.data._types._test_result import TestResult
from ni.measurements.data.v1.data_store_pb2 import ErrorInformation, Outcome

__all__ = [
    "DataStoreClient",
    "ErrorInformation",
    "Moniker",
    "Outcome",
    "PublishedCondition",
    "PublishedMeasurement",
    "Step",
    "TestResult",
]

# Hide that it was not defined in this top-level package
DataStoreClient.__module__ = __name__
ErrorInformation.__module__ = __name__
Moniker.__module__ = __name__
Outcome.__module__ = __name__
PublishedCondition.__module__ = __name__
PublishedMeasurement.__module__ = __name__
Step.__module__ = __name__
TestResult.__module__ = __name__
