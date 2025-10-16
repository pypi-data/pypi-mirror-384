import os

# setup these 3 env vars in your environment.
# torch_credentials = {
#     'url': os.getenv('TORCH_CATALOG_URL', 'https://torch.acceldata.local:5443/torch'),
#     'access_key': os.getenv('TORCH_ACCESS_KEY', 'P04IM8FNQRUCRTU'),
#     'secret_key': os.getenv('TORCH_SECRET_KEY', 'E6LL9YUPMG4BDTJHT2VZD75HW0B8E5')
# }

torch_credentials = {
    'url': os.getenv('TORCH_CATALOG_URL', 'https://acceldata.dev.10.90.3.89.nip.io'),
    'access_key': os.getenv('TORCH_ACCESS_KEY', '21DK0CVJUAE0LET'),
    'secret_key': os.getenv('TORCH_SECRET_KEY', '1PT5E06TLCHKGELZCOEC7LLOCPYHJO')
}

ds_name = 'java_sdk_snowflake_ds'
ds_id = '2740'
asset_uid = 'java_sdk_snowflake_ds.FINANCE.FINANCE.CUSTOMERS_ACCOUNTS'
asset_id = 1202688
dq_policy_name = "selective_policy_dq"
recon_policy_name = "selective_recon_incremental"

# Profiling constants
table_asset_uid = "java_sdk_snowflake_ds.CUSTOMERS_DATABASE.CUSTOMERS.SELECTIVE_POLICY_DATA"
kafka_asset_uid = "sangeeta_kafka_ds.sangeeta_kaka_asset"
file_based_asset_uid = "sourav_gcs_data_source.gcs_incremental_file"

# Pipeline constants
# UID of the pipeline in torch
job_uid = "read_data_from_s3"
pipeline_uid = "torch.external.integration.demo-default"
# Name of the pipeline in torch
pipeline_name = "Flow ETL External Integration Demo - Default"
pipeline_uid_external = "torch.external.integration.demo-explicit.time"
# Name of the pipeline in torch
pipeline_name_external = "Flow ETL External Integration Demo - Explicit time"
# Name of the postgres datasource in torch
postgres_ds = "POSTGRES-DS"
# Name of the s3 datasource in torch
s3_ds = "S3-DS"
# Name of initial output asset which is the output of job copying generated csv data to s3 as csv
s3_customer = "s3_customers"
# Name of output asset which is the output of job joining data from 2nd csv and postgres by looking up department
# name for department id
s3_postgres_customers = "s3_customers_postgres"
# Name of postgres table where department id vs department name mapping has been created in demo schema
pg_table = "demo.dept_info"

pg_database = "customers"
# Name of postgres field to order sql query on
order_by = "customer_id"
# S3 bucket name
bucket = "airflow-sdk-demo"
# The location of initial csv file in s3 bucket
csv1 = 'demo/customers.csv'
# The location of csv file in s3 bucket after joining with data from postgres table
csv3 = 'demo/customers-with-department-info.csv'
# Number of entries to be generated
csv_size = 30

# DQ Policy Constants
dq_policy_backward_compatible_name = "selective_policy_dq_backward_compatible"
kafka_dq_policy_name = "kafka_dq_policy"
spark_sql_policy_name = "SelectiveDQPolicysparkSQLDynamicFilterVariable"
incremental_dq_policy_name = "selective_dq_incremental"
file_event_based_dq = "gcs_selective_policy"

# Recon Policy Constants
kafka_recon_policy_name = "kafka_recon_policy"
selective_recon_policy_backward_compatible_name = "selective_policy_recon_backward_compatible"  # backward compatible name
selective_recon_policy_name = "selective_policy_recon"
incremental_recon_policy_name = "selective_recon_incremental"
file_event_based_recon = "gcs_incremental_recon"

# Retry settings
RETRY_INTERVAL = 180  # 3 minutes in seconds
MAX_RETRIES = 6
