import logging
import pytest
import test_constants as test_const
from test_commons import retry_operation
from acceldata_sdk.torch_client import TorchClient
from acceldata_sdk.models.profile import StartProfilingRequest
from acceldata_sdk.models.common_types import (
    ExecutionType, BoundsIdMarkerConfig, BoundsDateTimeMarkerConfig,
    BoundsFileEventMarkerConfig, TimestampBasedMarkerConfig
)
from acceldata_sdk.errors import APIError, TorchSdkException

# Logging configuration
LOGGER = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)

# Initialize Torch client
torch_client = TorchClient(**test_const.torch_credentials)
LOGGER.info("Torch client connected")


@pytest.fixture(scope="module")
def asset():
    return torch_client.get_asset(identifier=test_const.table_asset_uid)


@pytest.mark.order(1)
def test_execute_full_profiling_backward_compatible(asset):
    LOGGER.info(f"Asset ID: {asset.id}")
    LOGGER.info("\n" + "=" * 20 + " Executing FULL profile using backward compatible call " + "=" * 20 + "\n")

    def operation():
        return asset.start_profile(profiling_type=ExecutionType.FULL)

    profiling_execution_result = retry_operation(
        operation,
        test_const.MAX_RETRIES,
        test_const.RETRY_INTERVAL
    )
    LOGGER.info(profiling_execution_result)
    assert profiling_execution_result is not None


@pytest.mark.order(2)
def test_execute_incremental_profiling_backward_compatible(asset):
    LOGGER.info(f"Asset ID: {asset.id}")
    LOGGER.info("\n" + "=" * 20 + " Executing INCREMENTAL profile using backward compatible call " + "=" * 20 + "\n")

    def operation():
        return asset.start_profile(profiling_type=ExecutionType.INCREMENTAL)

    profiling_execution_result = retry_operation(
        operation,
        test_const.MAX_RETRIES,
        test_const.RETRY_INTERVAL
    )
    LOGGER.info(profiling_execution_result)
    assert profiling_execution_result is not None


@pytest.mark.order(3)
def test_execute_full_profiling_using_start_profiling_request(asset):
    LOGGER.info(f"Asset ID: {asset.id}")
    profiling_execution_request = StartProfilingRequest(
        profilingType=ExecutionType.FULL
    )
    LOGGER.info(f" Executing FULL profile using Profiling Execution Request: {profiling_execution_request}")

    def operation():
        return asset.start_profile(start_profiling_request=profiling_execution_request)

    profiling_execution_result = retry_operation(
        operation,
        test_const.MAX_RETRIES,
        test_const.RETRY_INTERVAL
    )
    LOGGER.info(f"Profiling Execution Result: {profiling_execution_result}")
    assert profiling_execution_result is not None


@pytest.mark.order(4)
def test_execute_incremental_profiling_using_start_profiling_request(asset):
    LOGGER.info(f"Asset ID: {asset.id}")
    profiling_execution_request = StartProfilingRequest(profilingType=ExecutionType.INCREMENTAL)
    LOGGER.info(f" Executing INCREMENTAL profile using Profiling Execution Request: {profiling_execution_request}")

    def operation():
        return asset.start_profile(start_profiling_request=profiling_execution_request)

    profiling_execution_result = retry_operation(
        operation,
        test_const.MAX_RETRIES,
        test_const.RETRY_INTERVAL
    )
    LOGGER.info(f"Profiling Execution Result: {profiling_execution_result}")
    assert profiling_execution_result is not None


@pytest.mark.order(5)
def test_execute_selective_profiling_without_marker_configs(asset):
    LOGGER.info(f"Asset ID: {asset.id}")
    profiling_execution_request = StartProfilingRequest(profilingType=ExecutionType.SELECTIVE)
    LOGGER.info(f"Executing SELECTIVE profile without MARKER CONFIG: {profiling_execution_request}")
    try:
        profiling_execution_result = asset.start_profile(start_profiling_request=profiling_execution_request)
    except TorchSdkException as e:
        error_message = str(e)
        assert "markerConfig is a mandatory parameter for execution type" in error_message, \
            f"Unexpected error message: {error_message}"
        LOGGER.warning(f"Expected error occurred: {error_message}")


@pytest.mark.order(6)
def test_execute_selective_profiling_id_based(asset):
    LOGGER.info(f"Asset ID: {asset.id}")
    markerConfig = BoundsIdMarkerConfig(idColumnName="ID", fromId=0, toId=1000)
    profiling_execution_request = StartProfilingRequest(profilingType=ExecutionType.SELECTIVE,
                                                        markerConfig=markerConfig)
    LOGGER.info(
        f" Executing SELECTIVE ID based profiling  using Profiling Execution Request: {profiling_execution_request}")

    def operation():
        return asset.start_profile(start_profiling_request=profiling_execution_request)

    profiling_execution_result = retry_operation(
        operation,
        test_const.MAX_RETRIES,
        test_const.RETRY_INTERVAL
    )
    LOGGER.info(f"Profiling Execution Result: {profiling_execution_result}")
    LOGGER.info(profiling_execution_result)
    assert profiling_execution_result is not None


@pytest.mark.order(7)
def test_execute_selective_profiling_date_time_based(asset):
    LOGGER.info(f"Asset ID: {asset.id}")
    markerConfig = BoundsDateTimeMarkerConfig(dateColumnName="TO_DATE", format="yyyy-MM-dd",
                                              fromDate="2023-07-01 00:00:00.000", toDate="2024-07-14 23:59:59.999",
                                              timeZoneId="Asia/Calcutta")
    profiling_execution_request = StartProfilingRequest(profilingType=ExecutionType.SELECTIVE,
                                                        markerConfig=markerConfig)
    LOGGER.info(
        f" Executing SELECTIVE DATE TIME based profiling  using Profiling Execution Request: {profiling_execution_request}")

    def operation():
        return asset.start_profile(start_profiling_request=profiling_execution_request)

    profiling_execution_result = retry_operation(
        operation,
        test_const.MAX_RETRIES,
        test_const.RETRY_INTERVAL
    )
    LOGGER.info(f"Profiling Execution Result: {profiling_execution_result}")
    LOGGER.info(profiling_execution_result)
    assert profiling_execution_result is not None


@pytest.mark.order(8)
def test_execute_selective_profiling_file_event_based():
    asset = torch_client.get_asset(identifier=test_const.file_based_asset_uid)
    LOGGER.info(f"Asset ID: {asset.id}")
    markerConfig = BoundsFileEventMarkerConfig(
        fromDate="2019-04-01 00:00:00.000", toDate="2024-07-16 23:59:59.999",
        timeZoneId="Asia/Calcutta")
    profiling_execution_request = StartProfilingRequest(profilingType=ExecutionType.SELECTIVE,
                                                        markerConfig=markerConfig)
    LOGGER.info(
        f" Executing SELECTIVE FILE EVENT based profiling using Profiling Execution Request: {profiling_execution_request}")

    def operation():
        return asset.start_profile(start_profiling_request=profiling_execution_request)

    profiling_execution_result = retry_operation(
        operation,
        test_const.MAX_RETRIES,
        test_const.RETRY_INTERVAL
    )
    LOGGER.info(f"Profiling Execution Result: {profiling_execution_result}")
    LOGGER.info(profiling_execution_result)
    assert profiling_execution_result is not None
    LOGGER.info(profiling_execution_result)


# TODO Blocked on AOC-16709
@pytest.mark.order(9)
def test_execute_selective_profiling_kafka_timestamp():
    asset = torch_client.get_asset(identifier=test_const.kafka_asset_uid)
    LOGGER.info(f"Asset ID: {asset.id}")
    markerConfig = TimestampBasedMarkerConfig(
        format="yyyy-mm-dd",
        initialOffset="2023-06-01",
        timeZoneId="Asia/Calcutta")
    profiling_execution_request = StartProfilingRequest(profilingType=ExecutionType.SELECTIVE,
                                                        markerConfig=markerConfig)

    LOGGER.info(
        f" Executing SELECTIVE KAFKA TIMESTAMP based profiling using Profiling Execution Request: {profiling_execution_request}")

    def operation():
        return asset.start_profile(start_profiling_request=profiling_execution_request)

    profiling_execution_result = retry_operation(
        operation,
        test_const.MAX_RETRIES,
        test_const.RETRY_INTERVAL
    )
    LOGGER.info(f"Profiling Execution Result: {profiling_execution_result}")
    LOGGER.info(profiling_execution_result)
    assert profiling_execution_result is not None
