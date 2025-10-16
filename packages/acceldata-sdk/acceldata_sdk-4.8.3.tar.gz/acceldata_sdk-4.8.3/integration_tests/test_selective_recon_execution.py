from acceldata_sdk.torch_client import TorchClient
import logging
import pytest

from acceldata_sdk.models.common_types import PolicyExecutionRequest, ExecutionType, MarkerConfig, \
    AssetMarkerConfig, BoundsIdMarkerConfig, YunikornConfig, SparkResourceConfig, \
    RuleSparkSQLDynamicFilterVariableMapping, Mapping, BoundsDateTimeMarkerConfig, BoundsFileEventMarkerConfig, \
    TimestampBasedMarkerConfig
import test_constants as test_const
from test_commons import retry_operation
from acceldata_sdk.errors import APIError, TorchSdkException

# Setup logging configuration
logging.basicConfig(
    level=logging.INFO,  # Set the logging level to INFO
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()  # Log to the console
    ]
)

LOGGER = logging.getLogger(__name__)

# Authenticate to Acceldata
torch_client = TorchClient(**test_const.torch_credentials)
LOGGER.info("Torch client connected")


@pytest.mark.order(1)
def test_execute_full_recon_request_backward_compatible():
    recon_policy = torch_client.get_policy(identifier=test_const.selective_recon_policy_backward_compatible_name)
    LOGGER.info(f"Reconciliation Policy ID: {recon_policy.id}")
    LOGGER.info(
        f" Executing FULL Reconciliation using backward compatible approach:")

    def operation():
        return torch_client.execute_reconciliation_rule(
            rule_id=recon_policy.id, incremental=True
        )

    result = retry_operation(
        operation,
        test_const.MAX_RETRIES,
        test_const.RETRY_INTERVAL
    )
    assert result is not None
    LOGGER.info(f"Reconciliation Policy Execution Result: {result}")


@pytest.mark.order(2)
def test_execute_incremental_recon_request_backward_compatible():
    policy_id = test_const.incremental_recon_policy_name
    recon_policy = torch_client.get_policy(identifier=policy_id)
    LOGGER.info(
        f" Executing INCREMENTAL Reconciliation using backward compatible approach:")

    def operation():
        return torch_client.execute_reconciliation_rule(
            rule_id=recon_policy.id, incremental=True
        )

    policy_execution_result = retry_operation(
        operation,
        test_const.MAX_RETRIES,
        test_const.RETRY_INTERVAL
    )
    assert policy_execution_result is not None
    LOGGER.info(f"Reconciliation Policy Execution Result: {policy_execution_result}")


@pytest.mark.order(3)
def test_execute_full_recon_using_policy_execution_request(request):
    policy_id = test_const.selective_recon_policy_backward_compatible_name
    policy = torch_client.get_policy(identifier=policy_id)
    request = PolicyExecutionRequest(executionType=ExecutionType.FULL)
    LOGGER.info(f"Executing FULL Reconciliation using Policy execution request: {request}")

    def operation():
        return torch_client.execute_reconciliation_rule(rule_id=policy.id, policy_execution_request=request)

    policy_execution_result = retry_operation(
        operation,
        test_const.MAX_RETRIES,
        test_const.RETRY_INTERVAL
    )
    assert policy_execution_result is not None
    LOGGER.info(f"Reconciliation Policy Execution Result: {policy_execution_result}")


@pytest.mark.order(4)
def test_execute_incremental_recon_using_policy_execution_request(request):
    policy_id = test_const.incremental_recon_policy_name
    policy = torch_client.get_policy(identifier=policy_id)
    request = PolicyExecutionRequest(executionType=ExecutionType.INCREMENTAL)
    LOGGER.info(f"Executing INCREMENTAL Reconciliation using Policy execution request: {request}")

    def operation():
        return torch_client.execute_reconciliation_rule(rule_id=policy.id, policy_execution_request=request)

    policy_execution_result = retry_operation(
        operation,
        test_const.MAX_RETRIES,
        test_const.RETRY_INTERVAL
    )
    assert policy_execution_result is not None
    LOGGER.info(f"Reconciliation Policy Execution Result: {policy_execution_result}")


@pytest.mark.order(5)
def test_execute_selective_recon_without_marker_config():
    recon_policy = torch_client.get_policy(identifier=test_const.spark_sql_policy_name)
    policy_execution_request = PolicyExecutionRequest(
        executionType=ExecutionType.SELECTIVE, )
    LOGGER.info(
        f"Executing SELECTIVE Reconciliation without Marker config: {policy_execution_request}")

    try:
        policy_execution_request = torch_client.execute_reconciliation_rule(rule_id=recon_policy.id,
                                                                            policy_execution_request=policy_execution_request)
    except TorchSdkException as e:
        error_message = str(e)
        assert "markerConfig is a mandatory parameter for execution type" in error_message, \
            f"Unexpected error message: {error_message}"
        LOGGER.warning(f"Expected error occurred: {error_message}")


@pytest.mark.order(6)
def test_execute_selective_recon_datetime_based():
    recon_policy = torch_client.get_policy(identifier=test_const.recon_policy_name)
    LOGGER.info("\n" + "=" * 20 + "execute_selective_dq: Reconciliation Policy Details " + "=" * 20 + "\n")

    markerConfig = BoundsDateTimeMarkerConfig(dateColumnName="TO_DATE", format="yyyy-MM-dd",
                                              fromDate="2023-07-01 00:00:00.000", toDate="2024-07-14 23:59:59.999",
                                              timeZoneId="Asia/Calcutta")
    assetMarkerConfig = AssetMarkerConfig(assetId=9667404, markerConfig=markerConfig)
    markerConfigs = [assetMarkerConfig]
    policy_execution_request = PolicyExecutionRequest(
        markerConfigs=markerConfigs,
        executionType=ExecutionType.SELECTIVE)
    LOGGER.info(
        f"Executing SELECTIVE Reconciliation DATETIME based using Policy execution request: {policy_execution_request}")

    def operation():
        return torch_client.execute_reconciliation_rule(rule_id=recon_policy.id,
                                                        policy_execution_request=policy_execution_request)

    policy_execution_result = retry_operation(
        operation,
        test_const.MAX_RETRIES,
        test_const.RETRY_INTERVAL)
    assert policy_execution_result is not None
    LOGGER.info(policy_execution_result)


@pytest.mark.order(7)
def test_execute_selective_recon_file_event_based():
    recon_policy = torch_client.get_policy(identifier=test_const.file_event_based_recon)
    LOGGER.info("\n" + "=" * 20 + "execute_selective_dq: Reconciliation Policy Details " + "=" * 20 + "\n")
    markerConfig = BoundsFileEventMarkerConfig(
        fromDate="2020-07-01 00:00:00.000", toDate="2024-07-01 23:59:59.999",
        timeZoneId="Asia/Calcutta")
    assetMarkerConfig = AssetMarkerConfig(assetId=2220202, markerConfig=markerConfig)
    markerConfigs = [assetMarkerConfig]
    policy_execution_request = PolicyExecutionRequest(
        markerConfigs=markerConfigs,
        executionType=ExecutionType.SELECTIVE)
    LOGGER.info(
        f"Executing SELECTIVE Reconciliation FILE EVENT based using Policy execution request: {policy_execution_request}")

    def operation():
        return torch_client.execute_reconciliation_rule(rule_id=recon_policy.id,
                                                        policy_execution_request=policy_execution_request)

    policy_execution_result = retry_operation(
        operation,
        test_const.MAX_RETRIES,
        test_const.RETRY_INTERVAL)
    assert policy_execution_result is not None
    LOGGER.info(
        "\n" + "=" * 20 + "execute_selective_dq: Reconciliation Policy Execution Result Details " + "=" * 20 + "\n")
    LOGGER.info(policy_execution_result)


@pytest.mark.order(8)
def test_execute_selective_recon_kafka_timestamp_based():
    recon_policy = torch_client.get_policy(identifier=test_const.kafka_recon_policy_name)
    LOGGER.info("\n" + "=" * 20 + "execute_selective_dq: Reconciliation Policy Details " + "=" * 20 + "\n")
    LOGGER.info(f"execute_selective_dq: Reconciliation Policy ID: {recon_policy.id}")

    markerConfig = TimestampBasedMarkerConfig(
        format="yyyy-mm-dd",
        initialOffset="2023-06-01",
        timeZoneId="Asia/Calcutta")
    assetMarkerConfig = AssetMarkerConfig(assetId=5241961, markerConfig=markerConfig)
    markerConfigs = [assetMarkerConfig]
    policy_execution_request = PolicyExecutionRequest(
        markerConfigs=markerConfigs,
        executionType=ExecutionType.SELECTIVE)
    LOGGER.info(
        f"Executing SELECTIVE Reconciliation KAFKA TIMESTAMP based using Policy execution request: {policy_execution_request}")

    def operation():
        return torch_client.execute_reconciliation_rule(rule_id=recon_policy.id,
                                                              policy_execution_request=policy_execution_request)

    policy_execution_result = retry_operation(
        operation,
        test_const.MAX_RETRIES,
        test_const.RETRY_INTERVAL)
    assert policy_execution_result is not None
    LOGGER.info(
        "\n" + "=" * 20 + "execute_selective_dq: Reconciliation Policy Execution Result Details " + "=" * 20 + "\n")
    LOGGER.info(policy_execution_result)
