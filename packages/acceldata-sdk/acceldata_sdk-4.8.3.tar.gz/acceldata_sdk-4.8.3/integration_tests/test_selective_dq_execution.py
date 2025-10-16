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
def test_execute_full_dq_request_backward_compatible():
    dq_policy = torch_client.get_policy(identifier=test_const.dq_policy_backward_compatible_name)
    LOGGER.info(f"DQ Policy ID: {dq_policy.id}")
    LOGGER.info(
        f" Executing FULL DQ using backward compatible approach:")

    def operation():
        return torch_client.execute_dq_rule(
            rule_id=dq_policy.id, incremental=True
        )

    result = retry_operation(
        operation,
        test_const.MAX_RETRIES,
        test_const.RETRY_INTERVAL
    )
    assert result is not None
    LOGGER.info(f"DQ Policy Execution Result: {result}")


@pytest.mark.order(2)
def test_execute_incremental_dq_request_backward_compatible():
    policy_id = test_const.incremental_dq_policy_name
    dq_policy = torch_client.get_policy(identifier=policy_id)
    LOGGER.info(
        f" Executing INCREMENTAL DQ using backward compatible approach:")

    def operation():
        return torch_client.execute_dq_rule(
            rule_id=dq_policy.id, incremental=True
        )

    policy_execution_result = retry_operation(
        operation,
        test_const.MAX_RETRIES,
        test_const.RETRY_INTERVAL
    )
    assert policy_execution_result is not None
    LOGGER.info(f"DQ Policy Execution Result: {policy_execution_result}")


@pytest.mark.order(3)
def test_execute_full_dq_using_policy_execution_request(request):
    policy_id = test_const.dq_policy_name
    policy = torch_client.get_policy(identifier=policy_id)
    request = PolicyExecutionRequest(executionType=ExecutionType.FULL)
    LOGGER.info(f"Executing FULL DQ using Policy execution request: {request}")

    def operation():
        return torch_client.execute_dq_rule(rule_id=policy.id, policy_execution_request=request)

    policy_execution_result = retry_operation(
        operation,
        test_const.MAX_RETRIES,
        test_const.RETRY_INTERVAL
    )
    assert policy_execution_result is not None
    LOGGER.info(f"DQ Policy Execution Result: {policy_execution_result}")


@pytest.mark.order(4)
def test_execute_incremental_dq_using_policy_execution_request(request):
    policy_id = test_const.dq_policy_name
    policy = torch_client.get_policy(identifier=policy_id)
    request = PolicyExecutionRequest(executionType=ExecutionType.INCREMENTAL)
    LOGGER.info(f"Executing INCREMENTAL DQ using Policy execution request: {request}")

    def operation():
        return torch_client.execute_dq_rule(rule_id=policy.id, policy_execution_request=request)

    policy_execution_result = retry_operation(
        operation,
        test_const.MAX_RETRIES,
        test_const.RETRY_INTERVAL
    )
    assert policy_execution_result is not None
    LOGGER.info(f"DQ Policy Execution Result: {policy_execution_result}")


@pytest.mark.order(5)
def test_execute_selective_dq_spark_sql_dynamic_filter_variable_mapping():
    dq_policy = torch_client.get_policy(identifier=test_const.spark_sql_policy_name)
    LOGGER.info("\n" + "=" * 20 + "execute_selective_dq: DQ Policy Details " + "=" * 20 + "\n")
    LOGGER.info(f"execute_selective_dq: DQ Policy : {dq_policy}")

    markerConfig = BoundsIdMarkerConfig(idColumnName="ID", fromId=0, toId=1000)
    assetMarkerConfig = AssetMarkerConfig(assetId=9667404, markerConfig=markerConfig)
    markerConfigs = [assetMarkerConfig]
    yunikornConfig = YunikornConfig(minExecutors=1, maxExecutors=2, executorCores=2, executorMemory="2g", driverCores=2,
                                    driverMemory="2g")
    # additionalConfiguration = {"spark.executor.memoryOverhead": "384"}
    sparkResourceConfig = SparkResourceConfig(yunikorn=yunikornConfig,
                                              additionalConfiguration={})
    ruleItemSelections = []
    mapping = Mapping(key="column_name", isColumnVariable=True, value="100")
    sparkSQLDynamicFilterVariableMapping = [RuleSparkSQLDynamicFilterVariableMapping(
        ruleName="SelectiveDQPolicysparkSQLDynamicFilterVariable",
        mapping=[mapping])]
    policy_execution_request = PolicyExecutionRequest(
        markerConfigs=markerConfigs,
        executionType=ExecutionType.SELECTIVE,
        sparkResourceConfig=sparkResourceConfig,
        sparkSQLDynamicFilterVariableMapping=sparkSQLDynamicFilterVariableMapping,
        ruleItemSelections=ruleItemSelections)
    LOGGER.info(
        f"Executing SELECTIVE DQ ID based with SPARK SQL DYNAMIC FILTER using Policy execution request: {policy_execution_request}")

    def operation():
        return torch_client.execute_dq_rule(rule_id=dq_policy.id,
                                            policy_execution_request=policy_execution_request)

    policy_execution_result = retry_operation(
        operation,
        test_const.MAX_RETRIES,
        test_const.RETRY_INTERVAL
    )

    assert policy_execution_result is not None
    LOGGER.info(f"DQ Policy Execution Result: {policy_execution_result}")


@pytest.mark.order(6)
def test_execute_selective_dq_without_marker_config():
    dq_policy = torch_client.get_policy(identifier=test_const.spark_sql_policy_name)
    policy_execution_request = PolicyExecutionRequest(
        executionType=ExecutionType.SELECTIVE)
    LOGGER.info(
        f"Executing SELECTIVE DQ policy without marker config using Policy execution request: {policy_execution_request}")

    try:
        policy_execution_request = torch_client.execute_dq_rule(rule_id=dq_policy.id,
                                                                policy_execution_request=policy_execution_request)
    except TorchSdkException as e:
        error_message = str(e)
        assert "markerConfig is a mandatory parameter for execution type" in error_message, \
            f"Unexpected error message: {error_message}"
        LOGGER.warning(f"Expected error occurred: {error_message}")


@pytest.mark.order(7)
def test_execute_selective_dq_datetime_based():
    dq_policy = torch_client.get_policy(identifier=test_const.dq_policy_name)
    LOGGER.info("\n" + "=" * 20 + "execute_selective_dq: DQ Policy Details " + "=" * 20 + "\n")

    markerConfig = BoundsDateTimeMarkerConfig(dateColumnName="TO_DATE", format="yyyy-MM-dd",
                                              fromDate="2023-07-01 00:00:00.000", toDate="2024-07-14 23:59:59.999",
                                              timeZoneId="Asia/Calcutta")
    assetMarkerConfig = AssetMarkerConfig(assetId=9667404, markerConfig=markerConfig)
    markerConfigs = [assetMarkerConfig]
    policy_execution_request = PolicyExecutionRequest(
        markerConfigs=markerConfigs,
        executionType=ExecutionType.SELECTIVE)
    LOGGER.info(
        f"Executing SELECTIVE DQ DATETIME based using Policy execution request: {policy_execution_request}")

    def operation():
        return torch_client.execute_dq_rule(rule_id=dq_policy.id,
                                            policy_execution_request=policy_execution_request)

    policy_execution_result = retry_operation(
        operation,
        test_const.MAX_RETRIES,
        test_const.RETRY_INTERVAL)
    assert policy_execution_result is not None
    LOGGER.info(policy_execution_result)


@pytest.mark.order(8)
def test_execute_selective_dq_file_event_based():
    dq_policy = torch_client.get_policy(identifier=test_const.file_event_based_dq)
    LOGGER.info("\n" + "=" * 20 + "execute_selective_dq: DQ Policy Details " + "=" * 20 + "\n")
    LOGGER.info(f"execute_selective_dq: DQ Policy ID: {dq_policy.id}")

    markerConfig = BoundsFileEventMarkerConfig(
        fromDate="2024-07-01 00:00:00.000", toDate="2024-07-01 23:59:59.999",
        timeZoneId="Asia/Calcutta")
    assetMarkerConfig = AssetMarkerConfig(assetId=1202688, markerConfig=markerConfig)
    markerConfigs = [assetMarkerConfig]
    policy_execution_request = PolicyExecutionRequest(
        markerConfigs=markerConfigs,
        executionType=ExecutionType.SELECTIVE)
    LOGGER.info(
        f"Executing SELECTIVE DQ FILE EVENT based using Policy execution request: {policy_execution_request}")

    def operation():
        return torch_client.execute_dq_rule(rule_id=dq_policy.id,
                                            policy_execution_request=policy_execution_request)

    policy_execution_result = retry_operation(
        operation,
        test_const.MAX_RETRIES,
        test_const.RETRY_INTERVAL)
    assert policy_execution_result is not None
    LOGGER.info("\n" + "=" * 20 + "execute_selective_dq: DQ Policy Execution Result Details " + "=" * 20 + "\n")
    LOGGER.info(policy_execution_result)


@pytest.mark.order(9)
def test_execute_selective_dq_kafka_timestamp_based():
    dq_policy = torch_client.get_policy(identifier=test_const.kafka_dq_policy_name)

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
        f"Executing SELECTIVE DQ KAFKA TIMESTAMP based using Policy execution request: {policy_execution_request}")

    def operation():
        return torch_client.execute_dq_rule(rule_id=dq_policy.id,
                                                  policy_execution_request=policy_execution_request)

    policy_execution_result = retry_operation(
        operation,
        test_const.MAX_RETRIES,
        test_const.RETRY_INTERVAL)
    assert policy_execution_result is not None
    LOGGER.info("\n" + "=" * 20 + "execute_selective_dq: DQ Policy Execution Result Details " + "=" * 20 + "\n")
    LOGGER.info(policy_execution_result)
