"""Data store client for publishing and reading data."""

from __future__ import annotations

import logging
import sys
from collections.abc import Iterable, Sequence
from threading import Lock
from types import TracebackType
from typing import TYPE_CHECKING, Type, TypeVar, overload
from urllib.parse import urlparse

import hightime as ht
from grpc import Channel
from ni.datamonikers.v1.client import MonikerClient
from ni.datamonikers.v1.data_moniker_pb2 import Moniker
from ni.datastore.data._grpc_conversion import (
    get_publish_measurement_timestamp,
    populate_publish_condition_batch_request_values,
    populate_publish_condition_request_value,
    populate_publish_measurement_batch_request_values,
    populate_publish_measurement_request_value,
    unpack_and_convert_from_protobuf_any,
)
from ni.datastore.data._types._published_condition import PublishedCondition
from ni.datastore.data._types._published_measurement import PublishedMeasurement
from ni.datastore.data._types._step import Step
from ni.datastore.data._types._test_result import TestResult
from ni.measurementlink.discovery.v1.client import DiscoveryClient
from ni.measurements.data.v1.client import DataStoreClient as DataStoreServiceClient
from ni.measurements.data.v1.data_store_pb2 import (
    ErrorInformation,
    Outcome,
)
from ni.measurements.data.v1.data_store_service_pb2 import (
    CreateStepRequest,
    CreateTestResultRequest,
    GetStepRequest,
    GetTestResultRequest,
    PublishConditionBatchRequest,
    PublishConditionRequest,
    PublishMeasurementBatchRequest,
    PublishMeasurementRequest,
    QueryConditionsRequest,
    QueryMeasurementsRequest,
    QueryStepsRequest,
)
from ni.protobuf.types.precision_timestamp_conversion import (
    hightime_datetime_to_protobuf,
)
from ni_grpc_extensions.channelpool import GrpcChannelPool

if TYPE_CHECKING:
    if sys.version_info >= (3, 11):
        from typing import Self
    else:
        from typing_extensions import Self

TRead = TypeVar("TRead")

_logger = logging.getLogger(__name__)


class DataStoreClient:
    """Data store client for publishing and reading data."""

    __slots__ = (
        "_closed",
        "_discovery_client",
        "_grpc_channel",
        "_grpc_channel_pool",
        "_data_store_client",
        "_data_store_client_lock",
        "_moniker_clients_by_service_location",
        "_moniker_clients_lock",
    )

    _DATA_STORE_CLIENT_CLOSED_ERROR = "This DataStoreClient has been closed. Create a new DataStoreClient for further interaction with the data store."

    _closed: bool
    _discovery_client: DiscoveryClient | None
    _grpc_channel: Channel | None
    _grpc_channel_pool: GrpcChannelPool | None
    _data_store_client: DataStoreServiceClient | None
    _moniker_clients_by_service_location: dict[str, MonikerClient]
    _data_store_client_lock: Lock
    _moniker_clients_lock: Lock

    def __init__(
        self,
        discovery_client: DiscoveryClient | None = None,
        grpc_channel: Channel | None = None,
        grpc_channel_pool: GrpcChannelPool | None = None,
    ) -> None:
        """Initialize the DataStoreClient.

        Args:
            discovery_client: An optional discovery client (recommended).

            grpc_channel: An optional data store gRPC channel. Providing this channel will bypass
                discovery service resolution of the data store. (Note: Reading data from a moniker
                will still always use a channel corresponding to the service location specified by
                that moniker.)

            grpc_channel_pool: An optional gRPC channel pool (recommended).
        """
        self._discovery_client = discovery_client
        self._grpc_channel = grpc_channel
        self._grpc_channel_pool = grpc_channel_pool

        self._data_store_client = None
        self._moniker_clients_by_service_location = {}

        self._data_store_client_lock = Lock()
        self._moniker_clients_lock = Lock()

        self._closed = False

    def __enter__(self) -> Self:
        """Enter the runtime context of the data store client."""
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        """Exit the runtime context of the data store client."""
        self.close()

    def close(self) -> None:
        """Close the data store client and clean up resources that it owns."""
        self._closed = True

        with self._data_store_client_lock:
            if self._data_store_client is not None:
                self._data_store_client.close()
                self._data_store_client = None

        with self._moniker_clients_lock:
            for _, moniker_client in self._moniker_clients_by_service_location.items():
                moniker_client.close()
            self._moniker_clients_by_service_location.clear()

    def publish_condition(
        self,
        condition_name: str,
        type: str,
        value: object,
        step_id: str,
    ) -> PublishedCondition:
        """Publish a condition value to the data store."""
        publish_request = PublishConditionRequest(
            condition_name=condition_name,
            type=type,
            step_id=step_id,
        )
        populate_publish_condition_request_value(publish_request, value)
        publish_response = self._get_data_store_client().publish_condition(publish_request)
        return PublishedCondition.from_protobuf(publish_response.published_condition)

    def publish_condition_batch(
        self, condition_name: str, type: str, values: object, step_id: str
    ) -> PublishedCondition:
        """Publish a batch of N values for a condition to the data store."""
        publish_request = PublishConditionBatchRequest(
            condition_name=condition_name,
            type=type,
            step_id=step_id,
        )
        populate_publish_condition_batch_request_values(publish_request, values)
        publish_response = self._get_data_store_client().publish_condition_batch(publish_request)
        return PublishedCondition.from_protobuf(publish_response.published_condition)

    def publish_measurement(
        self,
        measurement_name: str,
        value: object,  # More strongly typed Union[bool, AnalogWaveform] can be used if needed
        step_id: str,
        timestamp: ht.datetime | None = None,
        outcome: Outcome.ValueType = Outcome.OUTCOME_UNSPECIFIED,
        error_information: ErrorInformation | None = None,
        hardware_item_ids: Iterable[str] = tuple(),
        test_adapter_ids: Iterable[str] = tuple(),
        software_item_ids: Iterable[str] = tuple(),
        notes: str = "",
    ) -> PublishedMeasurement:
        """Publish a measurement value to the data store."""
        publish_request = PublishMeasurementRequest(
            measurement_name=measurement_name,
            step_id=step_id,
            outcome=outcome,
            error_information=error_information,
            hardware_item_ids=hardware_item_ids,
            test_adapter_ids=test_adapter_ids,
            software_item_ids=software_item_ids,
            notes=notes,
        )
        populate_publish_measurement_request_value(publish_request, value)
        publish_request.timestamp.CopyFrom(
            get_publish_measurement_timestamp(publish_request, timestamp)
        )
        publish_response = self._get_data_store_client().publish_measurement(publish_request)
        return PublishedMeasurement.from_protobuf(publish_response.published_measurement)

    def publish_measurement_batch(
        self,
        measurement_name: str,
        values: object,
        step_id: str,
        timestamps: Iterable[ht.datetime] = tuple(),
        outcomes: Iterable[Outcome.ValueType] = tuple(),
        error_information: Iterable[ErrorInformation] = tuple(),
        hardware_item_ids: Iterable[str] = tuple(),
        test_adapter_ids: Iterable[str] = tuple(),
        software_item_ids: Iterable[str] = tuple(),
    ) -> Sequence[PublishedMeasurement]:
        """Publish a batch of N values of a measurement to the data store."""
        publish_request = PublishMeasurementBatchRequest(
            measurement_name=measurement_name,
            step_id=step_id,
            timestamp=[hightime_datetime_to_protobuf(ts) for ts in timestamps],
            outcome=outcomes,
            error_information=error_information,
            hardware_item_ids=hardware_item_ids,
            test_adapter_ids=test_adapter_ids,
            software_item_ids=software_item_ids,
        )
        populate_publish_measurement_batch_request_values(publish_request, values)
        publish_response = self._get_data_store_client().publish_measurement_batch(publish_request)
        return [
            PublishedMeasurement.from_protobuf(pm) for pm in publish_response.published_measurements
        ]

    @overload
    def read_data(
        self,
        moniker_source: Moniker | PublishedMeasurement | PublishedCondition,
        expected_type: Type[TRead],
    ) -> TRead: ...

    @overload
    def read_data(
        self,
        moniker_source: Moniker | PublishedMeasurement | PublishedCondition,
    ) -> object: ...

    def read_data(
        self,
        moniker_source: Moniker | PublishedMeasurement | PublishedCondition,
        expected_type: Type[TRead] | None = None,
    ) -> TRead | object:
        """Read data published to the data store."""
        if isinstance(moniker_source, Moniker):
            moniker = moniker_source
        elif isinstance(moniker_source, PublishedMeasurement):
            if moniker_source.moniker is None:
                raise ValueError("PublishedMeasurement must have a Moniker to read data")
            moniker = moniker_source.moniker
        elif isinstance(moniker_source, PublishedCondition):
            if moniker_source.moniker is None:
                raise ValueError("PublishedCondition must have a Moniker to read data")
            moniker = moniker_source.moniker

        moniker_client = self._get_moniker_client(moniker.service_location)
        read_result = moniker_client.read_from_moniker(moniker)
        converted_data = unpack_and_convert_from_protobuf_any(read_result.value)
        if expected_type is not None and not isinstance(converted_data, expected_type):
            raise TypeError(f"Expected type {expected_type}, got {type(converted_data)}")
        return converted_data

    def create_step(self, step: Step) -> str:
        """Create a step in the data store."""
        create_request = CreateStepRequest(step=step.to_protobuf())
        create_response = self._get_data_store_client().create_step(create_request)
        return create_response.step_id

    def get_step(self, step_id: str) -> Step:
        """Get a step from the data store."""
        get_request = GetStepRequest(step_id=step_id)
        get_response = self._get_data_store_client().get_step(get_request)
        return Step.from_protobuf(get_response.step)

    def create_test_result(self, test_result: TestResult) -> str:
        """Create a test result in the data store."""
        create_request = CreateTestResultRequest(test_result=test_result.to_protobuf())
        create_response = self._get_data_store_client().create_test_result(create_request)
        return create_response.test_result_id

    def get_test_result(self, test_result_id: str) -> TestResult:
        """Get a test result from the data store."""
        get_request = GetTestResultRequest(test_result_id=test_result_id)
        get_response = self._get_data_store_client().get_test_result(get_request)
        return TestResult.from_protobuf(get_response.test_result)

    def query_conditions(self, odata_query: str = "") -> Sequence[PublishedCondition]:
        """Query conditions from the data store."""
        query_request = QueryConditionsRequest(odata_query=odata_query)
        query_response = self._get_data_store_client().query_conditions(query_request)
        return [
            PublishedCondition.from_protobuf(published_condition)
            for published_condition in query_response.published_conditions
        ]

    def query_measurements(self, odata_query: str = "") -> Sequence[PublishedMeasurement]:
        """Query measurements from the data store."""
        query_request = QueryMeasurementsRequest(odata_query=odata_query)
        query_response = self._get_data_store_client().query_measurements(query_request)
        return [
            PublishedMeasurement.from_protobuf(published_measurement)
            for published_measurement in query_response.published_measurements
        ]

    def query_steps(self, odata_query: str = "") -> Sequence[Step]:
        """Query steps from the data store."""
        query_request = QueryStepsRequest(odata_query=odata_query)
        query_response = self._get_data_store_client().query_steps(query_request)
        return [Step.from_protobuf(step) for step in query_response.steps]

    def _get_data_store_client(self) -> DataStoreServiceClient:
        if self._closed:
            raise RuntimeError(self._DATA_STORE_CLIENT_CLOSED_ERROR)

        if self._data_store_client is None:
            with self._data_store_client_lock:
                if self._data_store_client is None:
                    self._data_store_client = self._instantiate_data_store_client()
        return self._data_store_client

    def _instantiate_data_store_client(self) -> DataStoreServiceClient:
        return DataStoreServiceClient(
            discovery_client=self._discovery_client,
            grpc_channel=self._grpc_channel,
            grpc_channel_pool=self._grpc_channel_pool,
        )

    def _get_moniker_client(self, service_location: str) -> MonikerClient:
        if self._closed:
            raise RuntimeError(self._DATA_STORE_CLIENT_CLOSED_ERROR)

        parsed_service_location = urlparse(service_location).netloc
        if parsed_service_location not in self._moniker_clients_by_service_location:
            with self._moniker_clients_lock:
                if parsed_service_location not in self._moniker_clients_by_service_location:
                    self._moniker_clients_by_service_location[parsed_service_location] = (
                        self._instantiate_moniker_client(parsed_service_location)
                    )
        return self._moniker_clients_by_service_location[parsed_service_location]

    def _instantiate_moniker_client(self, parsed_service_location: str) -> MonikerClient:
        return MonikerClient(
            service_location=parsed_service_location,
            grpc_channel_pool=self._grpc_channel_pool,
        )
