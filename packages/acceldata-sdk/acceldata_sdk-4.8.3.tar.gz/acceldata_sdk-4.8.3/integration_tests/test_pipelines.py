from acceldata_sdk.torch_client import TorchClient
import test_constants as test_const
from acceldata_sdk.models.pipeline import CreatePipeline, PipelineMetadata, PipelineRunResult, PipelineRunStatus
import pprint
from datetime import datetime
from acceldata_sdk.models.job import CreateJob, JobMetadata, Node
from acceldata_sdk.events.generic_event import GenericEvent

pp = pprint.PrettyPrinter(indent=4)

pipeline_uid = test_const.pipeline_uid
pipeline_name_ = test_const.pipeline_uid
job_uid = test_const.job_uid
torch_client = TorchClient(**test_const.torch_credentials)


def test_list_all_pipelines():
    pipelines = torch_client.get_pipelines()
    assert len(pipelines) > 0


def test_create_pipeline():
    meta = PipelineMetadata(owner='sdk/pipeline-user', team='TORCH', codeLocation='...')
    pipeline = CreatePipeline(
        uid=pipeline_uid,
        name=pipeline_name_,
        description=f'The pipeline {pipeline_name_} has been created from torch-sdk',
        meta=meta,
        context={'pipeline_uid': pipeline_uid, 'pipeline_name': pipeline_name_}
    )
    pipeline_res = torch_client.create_pipeline(pipeline=pipeline)
    pipeline = torch_client.get_pipeline(pipeline_res.id)
    assert pipeline is not None


def test_create_pipeline_run():
    pipeline = torch_client.get_pipeline(pipeline_uid)
    pipeline_run = pipeline.create_pipeline_run()
    run_with_id = pipeline.get_run(pipeline_run.id)
    assert pipeline_run == run_with_id


def test_latest_pipeline_run():
    pipeline = torch_client.get_pipeline(pipeline_uid)
    latest_run = pipeline.get_latest_pipeline_run()
    pipeline_runs = pipeline.get_runs()
    assert latest_run == pipeline_runs[0]


def test_create_root_span():
    pipeline = torch_client.get_pipeline(pipeline_uid)
    latest_run = pipeline.get_latest_pipeline_run()
    span = latest_run.create_span(uid=f'{pipeline_uid}.span')
    assert span is not None


def test_update_pipeline_run():
    pipeline = torch_client.get_pipeline(pipeline_uid)
    latest_run = pipeline.get_latest_pipeline_run()
    update_pipeline_run_res = latest_run.update_pipeline_run(
        context_data={'key1': 'value2', 'name': 'backend'},
        result=PipelineRunResult.SUCCESS,
        status=PipelineRunStatus.COMPLETED
    )
    assert update_pipeline_run_res is not None


def test_details_pipeline_run():
    pipeline = torch_client.get_pipeline(pipeline_uid)
    latest_run = pipeline.get_latest_pipeline_run()
    details = latest_run.get_details()
    assert details is not None


def test_create_job():
    inputs = [Node(job_uid='customers.data-generation')]
    outputs = [Node(asset_uid=f'S3-DS.s3_customers')]
    context_job = {'job': 'data_gene', 'time': str(datetime.now()), 'uid': 'customers.data-generation',
                   'operator': 'write_file_func'}
    metadata = JobMetadata('Jason', 'COKE', 'https://github.com/coke/reports/customers.kt')
    pipeline = torch_client.get_pipeline(pipeline_uid)
    latest_run = pipeline.get_latest_pipeline_run()
    job = CreateJob(
        uid=job_uid,
        name=f'{job_uid} Job',
        pipeline_run_id=latest_run.id,
        description=f'{job_uid} created using torch SDK',
        inputs=inputs,
        outputs=outputs,
        meta=metadata,
        context=context_job
    )
    job = pipeline.create_job(job)
    assert job is not None


def test_create_child_span():
    pipeline = torch_client.get_pipeline(pipeline_uid)
    latest_run = pipeline.get_latest_pipeline_run()
    span_root = latest_run.get_root_span()
    span_child = span_root.create_child_span(
        uid=f'{job_uid}.span',
        context_data={
            'time': str(datetime.now())
        },
        associatedJobUids=[job_uid])
    span_child.start()
    span_child.send_event(GenericEvent(
        context_data={'client_time': str(datetime.now()), 'total_file': 1,
                      'schema': 'name,address,dept_id'},
        event_uid="customers.data.generation.metadata"))
    span_child.end()
    span_root.end()
    if span_root.is_root():
        query_span_id = latest_run.get_span(span_child.span.id)
        child_spans = span_root.get_child_spans()
        assert query_span_id.span == child_spans[0]


def test_spans_pipeline_run():
    pipeline = torch_client.get_pipeline(pipeline_uid)
    latest_run = pipeline.get_latest_pipeline_run()
    spans = latest_run.get_spans()
    assert spans is not None


def test_delete_pipeline():
    pipeline = torch_client.get_pipeline(pipeline_uid)
    delete_res = pipeline.delete()
    assert delete_res is not None
