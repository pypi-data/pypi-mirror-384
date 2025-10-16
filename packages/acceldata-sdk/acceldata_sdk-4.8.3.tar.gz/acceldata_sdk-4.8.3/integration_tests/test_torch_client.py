import unittest
import random
from unittest.mock import Mock, patch, call
from acceldata_sdk.constants import SdkSupportedVersions, TorchBuildVersion
from acceldata_sdk.torch_client import TorchClient
from acceldata_sdk.models.pipeline import CreatePipeline, PipelineMetadata, PipelineRunResult, PipelineRunStatus
import pprint
import time
import os
from datetime import datetime
from acceldata_sdk.models.job import CreateJob, JobMetadata, Node
from acceldata_sdk.events.generic_event import GenericEvent
from acceldata_sdk.events.log_events import LogEvent
import acceldata_sdk.constants as const
from acceldata_sdk.models.ruleExecutionResult import RuleType, PolicyFilter, ExecutionPeriod
from acceldata_sdk.models.tags import AssetLabel, CustomAssetMetadata
from acceldata_sdk.models.profile import Profile, ProfileRequest, ProfilingType

pp = pprint.PrettyPrinter(indent=4)

# Pipeline constants
pipeline_uid = "adoc.test.pipeline.sanity"
pipeline_uid_with_continuation_id = "adoc.test.pipeline.sanity.continuation"
pipeline_uid_with_continuation_id_name = "ADOC Test Pipeline Sanity ContinuationId"
pipeline_name = "ADOC Test Pipeline Sanity"
job_uid_customers_read = "customers.read"
job_uid_generate_sales = "customers.generate_sales"
job_uid_sales = "aggregated_sales"

# DQ Policy constants
dq_policy_name = "snowflake_dq_automation_null_check_id_success"

# Reconciliation Policy constants
recon_policy_name = "Athena_automation_Hashed_Data_Equality_4_success"

# Datasource name
datasource_name = "Snowflake_stg"

# Asset UID
asset_uid_kafka = "Sample_Kafka.member_updates"
asset_uid_file = "S3_Demo.trans_detail"
asset_uid_table = "Snowflake_stg.SNOWFLAKE_SAMPLE_DATA.TPCDS_SF100TCL.CALL_CENTER"


class TestTorchClientIntegration(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        # Set up common variables or configurations if needed
        pass

    def setUp(self):
        # Create an instance of TorchClient with mock values for testing
        try:
            self.mock_url = os.getenv('TORCH_CATALOG_URL')
            self.mock_access_key = os.getenv('TORCH_ACCESS_KEY')
            self.mock_secret_key = os.getenv('TORCH_SECRET_KEY')
            self.torch_client = TorchClient(url=self.mock_url, access_key=self.mock_access_key,
                                            secret_key=self.mock_secret_key)
        except KeyError as e:
            raise ValueError(f"Environment variable {e} is not set. Please set all required variables.")

    def tearDown(self):
        pass

    # Pipeline test cases

    def test_get_torch_version(self):
        result = self.torch_client.get_torch_version()
        # Assertions
        pp.pprint("Validating get_torch_version")
        pp.pprint(result)
        self.assertIsNotNone(result)

    def test_get_supported_sdk_versions(self):
        result = self.torch_client.get_supported_sdk_versions()
        # Assertions
        pp.pprint("Validating get_supported_sdk_versions")
        pp.pprint(result)
        self.assertIsNotNone(result)

    def test_create_pipeline(self):
        meta = PipelineMetadata(owner='sdk/pipeline-user', team='TORCH', codeLocation='...')
        create_pipeline_payload = CreatePipeline(
            uid=pipeline_uid,
            name=pipeline_name,
            description=f'The has been created from torch-sdk',
            meta=meta,
            context={'pipeline_uid': pipeline_uid, 'pipeline_name': pipeline_name}
        )
        pp.pprint("Validating create_pipeline")
        create_pipeline_response = self.torch_client.create_pipeline(pipeline=create_pipeline_payload)
        pp.pprint(create_pipeline_response)
        pp.pprint("Validating get_pipeline by id")
        pipeline = self.torch_client.get_pipeline(create_pipeline_response.id)
        pp.pprint(pipeline)
        assert pipeline is not None

    def test_get_pipeline_by_uid(self):
        pp.pprint("Validating get_pipeline by UID")
        pipeline = self.torch_client.get_pipeline(pipeline_uid)
        pp.pprint(pipeline)
        assert pipeline is not None

    def test_create_pipeline_run(self):
        pipeline = self.torch_client.get_pipeline(pipeline_uid)
        pp.pprint("Validating create_pipeline_run")
        pipeline_run = pipeline.create_pipeline_run()
        pp.pprint(pipeline_run)
        run_with_id = pipeline.get_run(pipeline_run.id)
        pp.pprint(run_with_id)
        assert pipeline_run == run_with_id

    def test_create_pipeline_run_with_continuation_id(self):
        create_pipeline_payload = CreatePipeline(
            uid=pipeline_uid_with_continuation_id,
            name=pipeline_uid_with_continuation_id_name,
            description=f'The has been created from torch-sdk',
        )
        pipeline = self.torch_client.create_pipeline(pipeline=create_pipeline_payload)
        pp.pprint("Validating test_create_pipeline_run_with_continuation_id")
        pipeline_run = pipeline.create_pipeline_run(continuation_id=f'run.{random.random()}')
        pp.pprint(pipeline_run)
        run_with_id = pipeline.get_run(pipeline_run.id)
        pp.pprint(run_with_id)
        assert pipeline_run == run_with_id

    def test_get_pipelines(self):
        pp.pprint("Validating get_pipelines")
        pipelines = self.torch_client.get_pipelines()
        pp.pprint(pipelines)
        assert pipelines is not None

    def test_get_pipeline_runs(self):
        pp.pprint("Validating test_get_pipeline_runs")
        pipeline = self.torch_client.get_pipeline(pipeline_uid)
        pipeline_runs = pipeline.get_runs()
        pp.pprint(pipeline_runs)
        assert pipeline_runs is not None

    def test_latest_pipeline_run(self):
        pipeline = self.torch_client.get_pipeline(pipeline_uid)
        pp.pprint("Validating get_latest_pipeline_run")
        latest_run = pipeline.get_latest_pipeline_run()
        pp.pprint(latest_run)
        pp.pprint("Validating get_runs")
        pipeline_runs = pipeline.get_runs()
        pp.pprint(pipeline_runs)
        assert latest_run == pipeline_runs[0]

    def test_create_root_span(self):
        pipeline = self.torch_client.get_pipeline(pipeline_uid)
        latest_run = pipeline.get_latest_pipeline_run()
        pp.pprint("Create root span validation")
        root_span = latest_run.create_span(uid=f'{pipeline_uid}.span')
        pp.pprint(root_span)
        assert root_span is not None

    def test_create_job_for_pipeline(self):
        inputs = [Node(asset_uid=f'S3-DS.s3_customers')]
        outputs = [Node(job_uid=job_uid_generate_sales)]
        context_job = {'job': 'data_gene', 'time': str(datetime.now()), 'uid': 'customers.read',
                       'operator': 'write_file_func'}
        metadata = JobMetadata('Jason', 'COKE', 'https://github.com/coke/reports/customers.kt')
        pipeline = self.torch_client.get_pipeline(pipeline_uid)
        latest_run = pipeline.get_latest_pipeline_run()
        pp.pprint("Creating Job using pipeline validation")
        job = CreateJob(
            uid=job_uid_customers_read,
            name=f'{job_uid_customers_read} Job',
            pipeline_run_id=latest_run.id,
            description=f'{job_uid_customers_read} created using torch SDK',
            inputs=inputs,
            outputs=outputs,
            meta=metadata,
            context=context_job,
            bounded_by_span=True,
            span_uid=f'{job_uid_customers_read}.span'
        )
        job = pipeline.create_job(job)
        job_span = latest_run.get_span(f'{job_uid_customers_read}.span')
        pp.pprint(job_span)
        job_span.end()
        assert job is not None

    def test_create_job_for_pipeline_run(self):
        inputs = [Node(job_uid=job_uid_customers_read)]
        outputs = [Node(asset_uid=f'S3-DS.orders')]
        context_job = {'job': 'data_gene', 'time': str(datetime.now()), 'uid': 'customers.data-generation',
                       'operator': 'write_file_func'}
        metadata = JobMetadata('Jason', 'COKE', 'https://github.com/coke/reports/customers.kt')
        pipeline = self.torch_client.get_pipeline(pipeline_uid)
        latest_run = pipeline.get_latest_pipeline_run()
        pp.pprint("Creating Job using pipeline_run validation")
        job = CreateJob(
            uid=job_uid_generate_sales,
            name=f'{job_uid_generate_sales} Job',
            description=f'{job_uid_generate_sales} created using torch SDK',
            inputs=inputs,
            outputs=outputs,
            meta=metadata,
            context=context_job,
            bounded_by_span=True,
            span_uid=f'{job_uid_generate_sales}.span'
        )
        job = latest_run.create_job(job)
        job_span = latest_run.get_span(f'{job_uid_generate_sales}.span')
        pp.pprint(job_span)
        job_span.end()
        assert job is not None

    def test_create_child_span(self):
        pipeline = self.torch_client.get_pipeline(pipeline_uid)
        latest_run = pipeline.get_latest_pipeline_run()
        sales_span = latest_run.get_span(f'{job_uid_generate_sales}.span')
        pp.pprint("Validating create child span")
        span_child = sales_span.create_child_span(
            uid=f'{job_uid_sales}.span',
            context_data={
                'time': str(datetime.now())
            },
            associatedJobUids=[job_uid_sales])
        pp.pprint(span_child)
        pp.pprint("Validating span events")
        span_child.start()
        span_child.send_event(GenericEvent(
            context_data={'client_time': str(datetime.now()), 'total_file': 1,
                          'schema': 'name,address,dept_id'},
            event_uid="customers.data.generation.metadata"))
        span_child.send_event(LogEvent(
            context_data={'Size': 100, 'total_file': 1,
                          'schema': 'name,address,dept_id'},
            log_data="Customer data generated successfully."))
        span_child.end()
        span_child2 = sales_span.create_child_span(
            uid=f'{job_uid_sales}2.span',
            context_data={
                'time': str(datetime.now())
            },
            associatedJobUids=[job_uid_sales])
        pp.pprint(span_child2)
        pp.pprint("Validating span events")
        span_child2.start()
        span_child2.abort()
        sales_span.failed()
        if sales_span.is_root():
            query_span_id = latest_run.get_span(span_child.span.id)
            assert query_span_id is not None
            pp.pprint("query_span_id")
            pp.pprint(query_span_id)
            child_spans = sales_span.get_child_spans()
            assert child_spans is not None
            pp.pprint("Child spans")
            pp.pprint(child_spans)

    def test_spans_pipeline_run(self):
        pipeline = self.torch_client.get_pipeline(pipeline_uid)
        latest_run = pipeline.get_latest_pipeline_run()
        spans = latest_run.get_spans()
        assert spans is not None

    def test_details_pipeline_run(self):
        pipeline = self.torch_client.get_pipeline(pipeline_uid)
        latest_run = pipeline.get_latest_pipeline_run()
        details = latest_run.get_details()
        assert details is not None

    def test_update_pipeline_run(self):
        pipeline = self.torch_client.get_pipeline(pipeline_uid)
        latest_run = pipeline.get_latest_pipeline_run()
        update_pipeline_run_res = latest_run.update_pipeline_run(
            context_data={'key1': 'value2', 'name': 'backend'},
            result=PipelineRunResult.SUCCESS,
            status=PipelineRunStatus.COMPLETED
        )
        assert update_pipeline_run_res is not None

    def test_delete_pipeline(self):
        pipeline = self.torch_client.get_pipeline(pipeline_uid_with_continuation_id)
        delete_res = pipeline.delete()
        assert delete_res is not None

    # DQ Policy Test Cases
    def test_get_dq_policy(self):
        pp.pprint("Validating test test_get_dq_policy")
        dq_rule = self.torch_client.get_policy(const.PolicyType.DATA_QUALITY, dq_policy_name)
        pp.pprint(dq_rule)
        assert dq_rule is not None

    def test_get_dq_policy_without_type(self):
        pp.pprint("Validating test test_get_dq_policy_without_type")
        dq_rule = self.torch_client.get_policy(identifier=dq_policy_name)
        pp.pprint(dq_rule)
        assert dq_rule is not None

    def test_get_all_dq_policy(self):
        pp.pprint("Validating test test_get_all_dq_policy")
        policy_filter = PolicyFilter(policyType=RuleType.DATA_QUALITY, enable=True)
        dq_rules = self.torch_client.list_all_policies(filter=policy_filter)
        pp.pprint(dq_rules)
        assert dq_rules is not None

    def test_cancel_dq_policy(self):
        pp.pprint("Validating test test_cancel_dq_policy")
        dq_rule = self.torch_client.get_policy(const.PolicyType.DATA_QUALITY, dq_policy_name)
        async_executor = dq_rule.execute(sync=False)
        pp.pprint("Validating test async_executor")
        pp.pprint(async_executor)
        if async_executor.errorMessage is None:
            async_execution_status = async_executor.get_status()
            pp.pprint('async_execution_status')
            pp.pprint(async_execution_status)
            async_execution_cancel = async_executor.cancel()
            pp.pprint('async_execution_cancel')
            pp.pprint(async_execution_cancel)

    def test_execute_dq_policy(self):
        pp.pprint("Validating test test_execute_dq_policy")
        dq_rule = self.torch_client.get_policy(const.PolicyType.DATA_QUALITY, dq_policy_name)
        async_executor = dq_rule.execute(sync=False)
        if async_executor.errorMessage is None:
            async_execution_status = async_executor.get_status()
            pp.pprint('async_execution_status')
            pp.pprint(async_execution_status)
            async_execution_result = async_executor.get_result()
            pp.pprint('async_execution_result')
            pp.pprint(async_execution_result)

    def test_get_dq_policy_executions(self):
        pp.pprint("Validating test test_get_dq_policy_executions")
        dq_policy = self.torch_client.get_policy(identifier=dq_policy_name)
        dq_rule_executions = self.torch_client.policy_executions(dq_policy.id, RuleType.DATA_QUALITY)
        assert dq_rule_executions is not None

    # Reconciliation Policy Tests

    def test_get_recon_policy(self):
        pp.pprint("Validating test_get_recon_policy")
        recon_rule = self.torch_client.get_policy(const.PolicyType.RECONCILIATION, recon_policy_name)
        print(recon_rule)
        assert recon_rule is not None

    def test_get_recon_policy_without_type(self):
        pp.pprint("Validating test test_get_recon_policy_without_type")
        recon_rule = self.torch_client.get_policy(identifier=recon_policy_name)
        pp.pprint("recon_rule")
        pp.pprint(recon_rule)
        assert recon_rule is not None

    def test_get_all_recon_policy(self):
        pp.pprint("Validating test test_get_all_dq_policy")
        policy_filter = PolicyFilter(policyType=RuleType.RECONCILIATION, enable=True)
        recon_rules = self.torch_client.list_all_policies(filter=policy_filter)
        pp.pprint("recon_rules")
        pp.pprint(recon_rules)
        assert recon_rules is not None

    def test_cancel_recon_policy(self):
        pp.pprint("Validating test test_cancel_recon_policy")
        recon_rule = self.torch_client.get_policy(const.PolicyType.RECONCILIATION, recon_policy_name)
        pp.pprint("Validating test async_executor")
        async_executor = recon_rule.execute(sync=False)
        if async_executor.errorMessage is None:
            async_execution_status = async_executor.get_status()
            pp.pprint('async_execution_status')
            pp.pprint(async_execution_status)
            async_execution_cancel = async_executor.cancel()
            pp.pprint('async_execution_cancel')
            pp.pprint(async_execution_cancel)

    def test_execute_recon_policy(self):
        pp.pprint("Validating test test_execute_recon_policy")
        recon_rule = self.torch_client.get_policy(const.PolicyType.RECONCILIATION, recon_policy_name)
        async_executor = recon_rule.execute(sync=False)
        if async_executor.errorMessage is None:
            async_execution_status = async_executor.get_status()
            pp.pprint('async_execution_status')
            pp.pprint(async_execution_status)
            async_execution_result = async_executor.get_result()
            pp.pprint('async_execution_result')
            pp.pprint(async_execution_result)

    def test_get_recon_policy_executions(self):
        pp.pprint("Validating test test_get_recon_policy_executions")
        policy = self.torch_client.get_policy(identifier=recon_policy_name)
        recon_rule_executions = self.torch_client.policy_executions(policy.id, RuleType.RECONCILIATION)
        assert recon_rule_executions is not None

    # Data sources  tests
    def test_get_datasource(self):
        pp.pprint("Validating test test_get_datasource")
        datasource = self.torch_client.get_datasource(datasource_name, True)
        pp.pprint(datasource)
        assert datasource is not None

    def test_get_datasource_by_id(self):
        datasource = self.torch_client.get_datasource(datasource_name, True)
        pp.pprint("Validating test test_get_datasource_id")
        datasource_with_id = self.torch_client.get_datasource(datasource.id, False)
        pp.pprint(datasource_with_id)
        assert datasource_with_id is not None

    def test_get_all_data_sources(self):
        pp.pprint("Validating test test_get_all_data_sources")
        datasources = self.torch_client.get_datasources()
        pp.pprint(datasources)
        assert datasources is not None

    def test_get_ds_crawler_status(self):
        pp.pprint("Validating test test_get_ds_crawler_status")
        datasource = self.torch_client.get_datasource(datasource_name, True)
        status = datasource.get_crawler_status()
        pp.pprint(status)
        assert status is not None

    def test_start_crawler(self):
        pp.pprint("Validating test test_start_crawler")
        datasource = self.torch_client.get_datasource(datasource_name, False)
        start_crawler = datasource.start_crawler()
        pp.pprint(start_crawler)
        status = datasource.get_crawler_status()
        pp.pprint(status)
        assert status is not None

    # Assets tests
    def test_get_asset_by_uid(self):
        pp.pprint("Validating test test_get_asset_by_uid")
        asset = self.torch_client.get_asset(asset_uid_table)
        pp.pprint(asset)
        assert asset is not None

    def test_get_asset_by_id(self):
        pp.pprint("Validating test test_get_asset_by_id")
        asset = self.torch_client.get_asset(asset_uid_table)
        asset_with_id = self.torch_client.get_asset(asset.id)
        pp.pprint(asset_with_id)
        assert asset_with_id is not None

    def test_get_asset_metadata(self):
        pp.pprint("Validating test test_get_asset_metadata")
        asset = self.torch_client.get_asset(asset_uid_table)
        metadata_asset = asset.get_metadata()
        pp.pprint(metadata_asset)
        assert metadata_asset is not None

    def test_get_asset_sample_data_table(self):
        pp.pprint("Validating test test_get_asset_sample_data_table")
        asset = self.torch_client.get_asset(asset_uid_table)
        pp.pprint("Asset : {}".format(asset))
        sample_data_asset = asset.sample_data()
        pp.pprint(sample_data_asset)
        assert sample_data_asset is not None

    def test_get_asset_sample_data_file(self):
        pp.pprint("Validating test test_get_asset_sample_data_file")
        asset = self.torch_client.get_asset(asset_uid_file)
        sample_data_asset = asset.sample_data()
        pp.pprint(sample_data_asset)
        assert sample_data_asset is not None

    def test_get_asset_sample_data_kafka(self):
        pp.pprint("Validating test test_get_asset_sample_data_kafka")
        asset = self.torch_client.get_asset(asset_uid_kafka)
        sample_data_asset = asset.sample_data()
        pp.pprint(sample_data_asset)
        assert sample_data_asset is not None

    def test_get_asset_labels(self):
        pp.pprint("Validating test test_get_asset_labels")
        asset = self.torch_client.get_asset(asset_uid_table)
        labels_asset = asset.get_labels()
        pp.pprint(labels_asset)
        assert labels_asset is not None

    def test_add_asset_labels(self):
        pp.pprint("Validating test test_add_asset_labels")
        asset = self.torch_client.get_asset(asset_uid_table)
        asset.add_labels(labels=[AssetLabel('test12', 'shubh12'), AssetLabel('test22', 'shubh32')])
        labels_asset = asset.get_labels()
        pp.pprint(labels_asset)
        assert labels_asset is not None

    def test_add_asset_custom_metadata(self):
        pp.pprint("Validating test test_add_asset_custom_metadata")
        asset = self.torch_client.get_asset(asset_uid_table)
        asset.add_custom_metadata(
            custom_metadata=[CustomAssetMetadata('testcm1', 'shubhcm1'), CustomAssetMetadata('testcm2', 'shubhcm2')])
        metadata_asset = asset.get_metadata()
        pp.pprint(metadata_asset)
        assert metadata_asset is not None

    def test_profile_status(self):
        pp.pprint("Validating test test_profile_status")
        asset = self.torch_client.get_asset(asset_uid_table)
        latest_profile_status_asset = asset.get_latest_profile_status()
        pp.pprint(latest_profile_status_asset)
        assert latest_profile_status_asset is not None

    def test_cancel_profile(self):
        pp.pprint("Validating test test_cancel_profile")
        asset = self.torch_client.get_asset(asset_uid_table)
        latest_profile_status_asset = asset.get_latest_profile_status()
        pp.pprint("Latest profile status")
        pp.pprint(latest_profile_status_asset)
        if latest_profile_status_asset.status != 'IN PROGRESS':
            pp.pprint("Triggering profiling start request")
            start_profile_asset = asset.start_profile(ProfilingType.FULL)
            pp.pprint(start_profile_asset)
            time.sleep(15)
            profile_status = start_profile_asset.get_status()
            if profile_status['profileRequest']['status'] == 'IN PROGRESS':
                pp.pprint("Cancelling profiling request")
                cancel_res = start_profile_asset.cancel()
                pp.pprint(profile_status)
                assert cancel_res is not None
        else:
            pp.pprint("Profile execution request already in progress")

    def test_execute_profile(self):
        pp.pprint("Validating test test_execute_profile")
        asset = self.torch_client.get_asset(asset_uid_table)
        latest_profile_status_asset = asset.get_latest_profile_status()
        pp.pprint("Latest profile status")
        pp.pprint(latest_profile_status_asset)
        if latest_profile_status_asset.status != 'IN PROGRESS':
            start_profile_asset = asset.start_profile(ProfilingType.FULL)
            pp.pprint(start_profile_asset)
            profile_status = start_profile_asset.get_status()
            pp.pprint("Current profiling result status")
            pp.pprint(profile_status)
            assert profile_status is not None
        else:
            pp.pprint("Profile execution request already in progress")


if __name__ == '__main__':
    suite = unittest.TestSuite()

    # Pipeline Test cases
    suite.addTest(TestTorchClientIntegration('test_get_torch_version'))
    suite.addTest(TestTorchClientIntegration('test_get_supported_sdk_versions'))
    suite.addTest(TestTorchClientIntegration('test_create_pipeline'))
    suite.addTest(TestTorchClientIntegration('test_get_pipeline_by_uid'))
    suite.addTest(TestTorchClientIntegration('test_create_pipeline_run'))
    suite.addTest(TestTorchClientIntegration('test_latest_pipeline_run'))
    suite.addTest(TestTorchClientIntegration('test_create_root_span'))
    suite.addTest(TestTorchClientIntegration('test_create_job_for_pipeline'))
    suite.addTest(TestTorchClientIntegration('test_create_job_for_pipeline_run'))
    suite.addTest(TestTorchClientIntegration('test_create_child_span'))
    suite.addTest(TestTorchClientIntegration('test_update_pipeline_run'))
    suite.addTest(TestTorchClientIntegration('test_spans_pipeline_run'))
    suite.addTest(TestTorchClientIntegration('test_details_pipeline_run'))
    suite.addTest(TestTorchClientIntegration('test_get_pipelines'))
    suite.addTest(TestTorchClientIntegration('test_get_pipeline_runs'))
    suite.addTest(TestTorchClientIntegration('test_create_pipeline_run_with_continuation_id'))
    suite.addTest(TestTorchClientIntegration('test_delete_pipeline'))

    # DQ Policy Test Cases
    suite.addTest(TestTorchClientIntegration('test_execute_dq_policy'))
    suite.addTest(TestTorchClientIntegration('test_get_dq_policy'))
    suite.addTest(TestTorchClientIntegration('test_get_dq_policy_without_type'))
    suite.addTest(TestTorchClientIntegration('test_get_all_dq_policy'))
    suite.addTest(TestTorchClientIntegration('test_cancel_dq_policy'))
    suite.addTest(TestTorchClientIntegration('test_get_dq_policy_executions'))

    # Reconciliation Policy Test Cases
    suite.addTest(TestTorchClientIntegration('test_execute_recon_policy'))
    suite.addTest(TestTorchClientIntegration('test_get_recon_policy'))
    suite.addTest(TestTorchClientIntegration('test_get_recon_policy_without_type'))
    suite.addTest(TestTorchClientIntegration('test_get_all_recon_policy'))
    suite.addTest(TestTorchClientIntegration('test_cancel_recon_policy'))
    suite.addTest(TestTorchClientIntegration('test_get_recon_policy_executions'))

    # Data sources and Assets Test Cases
    suite.addTest(TestTorchClientIntegration('test_get_datasource'))
    suite.addTest(TestTorchClientIntegration('test_get_datasource_by_id'))
    suite.addTest(TestTorchClientIntegration('test_get_all_data_sources'))
    suite.addTest(TestTorchClientIntegration('test_get_ds_crawler_status'))
    suite.addTest(TestTorchClientIntegration('test_start_crawler'))
    suite.addTest(TestTorchClientIntegration('test_get_asset_by_uid'))
    suite.addTest(TestTorchClientIntegration('test_get_asset_by_id'))
    suite.addTest(TestTorchClientIntegration('test_get_asset_metadata'))
    suite.addTest(TestTorchClientIntegration('test_get_asset_sample_data_table'))
    suite.addTest(TestTorchClientIntegration('test_get_asset_sample_data_file'))
    suite.addTest(TestTorchClientIntegration('test_get_asset_sample_data_kafka'))
    suite.addTest(TestTorchClientIntegration('test_get_asset_labels'))
    suite.addTest(TestTorchClientIntegration('test_get_asset_labels'))
    suite.addTest(TestTorchClientIntegration('test_add_asset_labels'))
    suite.addTest(TestTorchClientIntegration('test_add_asset_custom_metadata'))
    suite.addTest(TestTorchClientIntegration('test_execute_profile'))
    suite.addTest(TestTorchClientIntegration('test_profile_status'))
    suite.addTest(TestTorchClientIntegration('test_cancel_profile'))

    unittest.TextTestRunner().run(suite)
