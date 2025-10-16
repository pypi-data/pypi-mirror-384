import pytest
import pprint
from acceldata_sdk.events.generic_event import GenericEvent
from acceldata_sdk.events.log_events import LogEvent
from acceldata_sdk.models.job import JobMetadata, Node, CreateJob
from acceldata_sdk.models.pipeline import CreatePipeline, PipelineMetadata, PipelineRunResult, PipelineRunStatus
from acceldata_sdk.torch_client import TorchClient
from datetime import datetime
import test_constants as test_const

pp = pprint.PrettyPrinter(indent=4)

# Global variables needed across functions
parent_span_context = None
pipeline_run_id = None

torch_client = TorchClient(**test_const.torch_credentials)

@pytest.fixture(scope="module", autouse=True)
def setup_pipeline_and_run():
    global parent_span_context, pipeline_run_id, torch_client
    pp.pprint("================= entering create_pipeline_and_run ==================")
    meta = PipelineMetadata(owner='sdk/pipeline-user', team='ADOC', codeLocation='...')
    pipeline_name_ = test_const.pipeline_name
    pipeline = CreatePipeline(
        uid=test_const.pipeline_uid,
        name=pipeline_name_,
        description=f'The pipeline {pipeline_name_} has been created from acceldata-sdk using External integration',
        meta=meta,
        context={'pipeline_uid': test_const.pipeline_uid, 'pipeline_name': pipeline_name_}
    )
    pipeline_res = torch_client.create_pipeline(pipeline=pipeline)
    print('Created pipeline with pipeline id :: ', pipeline_res.id)

    pipeline_run = pipeline_res.create_pipeline_run()
    pipeline_run_id = pipeline_run.id
    span_name_ = f'{test_const.pipeline_uid}.root.span'
    parent_span_context = pipeline_run.create_span(uid=span_name_)
    print("===Starting the root span for the pipeline run=====")
    parent_span_context.start()
    yield
    # teardown: End the pipeline
    pipeline = torch_client.get_pipeline(test_const.pipeline_uid)
    pipeline_run = pipeline.get_run(pipeline_run_id)
    parent_span = pipeline_run.get_root_span()
    parent_span.end(context_data={'dag_status': 'SUCCESS', 'time': str(datetime.now())})
    pipeline_run.update_pipeline_run(
        context_data={'status': 'success'},
        result=PipelineRunResult.SUCCESS,
        status=PipelineRunStatus.COMPLETED
    )

def create_job_span_not_bounded(job_uid, inputs, outputs, metadata, context_job, span_uid):
    print(
        "=================entering create_job_span_not_bounded for the job with uid " + job_uid + "==================")
    span_uid_temp = span_uid
    pipeline = torch_client.get_pipeline(test_const.pipeline_uid)
    pipeline_run = pipeline.get_run(pipeline_run_id)
    try:
        job = CreateJob(
            uid=job_uid,
            name=f'{job_uid} Job',
            pipeline_run_id=pipeline_run.id,
            description=f'{job_uid} created using torch job decorator',
            inputs=inputs,
            outputs=outputs,
            meta=metadata,
            context=context_job
        )
        job = pipeline.create_job(job)
        pp.pprint("Create job response: " + str(job))
    except Exception as e:
        print("Error in creating job")
        exception = e.__dict__
        print(exception)
        raise e
    else:
        pp.pprint("Successfully created job." + job_uid)
        parent_span_context1 = pipeline_run.get_root_span()

        associated_job_uids = [job_uid]
        if span_uid is None:
            span_uid_temp = job_uid
        span_context = parent_span_context1.create_child_span(
            uid=span_uid_temp,
            context_data={
                'time': str(datetime.now())
            },
            associatedJobUids=associated_job_uids)
    return span_context

@pytest.mark.order(1)
def test_write_file_func():
    pp.pprint("================= entering write_file_func ==================")
    context_job = {'job': 'data_gene', 'uid': 'customers.data-generation', 'operator': 'write_file_func'}
    span_context_parent = create_job_span_not_bounded(
        job_uid='customers.data-generation',
        inputs=[],
        outputs=[Node(job_uid='customers.s3-upload')],
        metadata=JobMetadata('Jason', 'COKE', 'https://github.com/coke/reports/customers.kt'),
        context_job=context_job,
        span_uid='customers.data.generation')
    pp.pprint("entering write_file_func")
    size = test_const.csv_size
    span_context_parent.start()
    span_context_parent.send_event(GenericEvent(
        context_data={'Size': size - 1, 'total_file': 1, 'schema': 'name,address,dept_id'},
        event_uid="customers.data.generation.metadata"))
    span_context_parent.send_event(LogEvent(
        context_data={'Size': size - 1, 'total_file': 1, 'schema': 'name,address,dept_id'},
        log_data="Customer data generated successfully."))
    span_context_parent.end()

@pytest.mark.order(2)
def test_upload_file_to_s3():
    context_job = {'job': 'data_upload', 'time': str(datetime.now()), 'uid': 'customers.s3-upload', 'operator': 'upload_file_to_s3'}
    span_context_parent = create_job_span_not_bounded(
        job_uid='customers.s3-upload',
        inputs=[Node(job_uid='customers.data-generation')],
        outputs=[Node(asset_uid=f'{test_const.s3_ds}.{test_const.s3_customer}')],
        context_job=context_job,
        metadata=JobMetadata('Jason', 'COKE', 'https://github.com/coke/reports/customers.kt'),
        span_uid='customers.s3.upload')
    pp.pprint("entering upload_file_to_s3")
    span_context_parent.start()
    span_context_parent.end()

@pytest.mark.order(3)
def test_rds_and_s3_clubbing():
    context_job = {'job': 'data_clubbing', 'time': str(datetime.now()), 'uid': 'customers.s3-postgres-clubbing', 'operator': 'rds_and_s3_clubbing'}

    pp.pprint(" ======== Creating Child 3 on the root span =====================")
    parent_span_context1 = create_job_span_not_bounded(
        job_uid='customers.s3-postgres-clubbing',
        inputs=[Node(asset_uid=f'{test_const.s3_ds}.{test_const.s3_customer}'), Node(asset_uid=f'{test_const.postgres_ds}.{test_const.pg_table}')],
        outputs=[Node(asset_uid=f'{test_const.s3_ds}.{test_const.s3_postgres_customers}')],
        context_job=context_job,
        metadata=JobMetadata('BEN', 'COKE', 'https://github.com/coke/reports/rds_customers.kt'),
        span_uid='customers.s3.postgres.clubbing')
    parent_span_context1.start()
    pp.pprint("entering csv_pg_s3")
    pp.pprint("reading csv file")

    pp.pprint(" ======== Creating Child 3 -> 1 =====================")
    read_csv_span = parent_span_context1.create_child_span(uid="read_csv")

    pp.pprint(" ======== Starting Child 3 -> 1 =====================")
    read_csv_span.start()
    read_csv_span.send_event(GenericEvent(context_data={'total_file_to_be_read': 1, 'RDS_TABLES': '1'}, event_uid="read_csv_data"))
    read_csv_span.end()

    pp.pprint(" ======== Generic event Child 3 =====================")
    parent_span_context1.send_event(GenericEvent(
        context_data={'total_file_to_be_read': 1, 'RDS_TABLES': '1', 'DATA_INSERTED': 100, 'RDS_USER': 'postgres'},
        event_uid="customers.rds.migration.metadata"))

    pp.pprint(" ======== Creating Child 3 -> 2 =====================")
    rds_merge_span = parent_span_context1.create_child_span(uid="rds_merge_data")

    pp.pprint(" ======== Starting Child 3 -> 2 =====================")
    rds_merge_span.start()

    pp.pprint(" ======== Creating Child 3 -> 2 -> 1 =====================")
    rds_dataframe_span = rds_merge_span.create_child_span(uid="rds_prepare_dataframe")

    pp.pprint(" ======== Starting Child 3 -> 2 -> 1 =====================")
    rds_dataframe_span.start()
    rds_dataframe_span.end()

    pp.pprint(" ======== Creating Child 3 -> 2 -> 2 =====================")
    rds_save_dataframe_span = rds_merge_span.create_child_span(uid="rds_save_dataframe", context_data={'client_time': str(datetime.now())})

    pp.pprint(" ======== Starting Child 3 -> 2 -> 2 =====================")
    rds_save_dataframe_span.start(context_data={'client_time': str(datetime.now())})
    rds_save_dataframe_span.end(context_data={'client_time': str(datetime.now())})

    pp.pprint(" ======== Ending Child 3 -> 2 =====================")
    rds_merge_span.end()

    pp.pprint(" ======== Creating Child 3 -> 3 =====================")
    write_csv_span = parent_span_context1.create_child_span(uid="write_csv")

    pp.pprint(" ======== Starting Child 3 -> 3 =====================")
    write_csv_span.start()
    print("Sending generic event for child 3->3")
    write_csv_span.send_event(GenericEvent(
        context_data={'client_time': str(datetime.now()), 'total_file_to_be_written': 1, 'RDS_TABLES': '1'},
        event_uid="write_csv_data"))
    write_csv_span.end(context_data={'client_time': "dummy"})

    pp.pprint(" ======== Ending Child 3 =====================")
    parent_span_context1.end()
