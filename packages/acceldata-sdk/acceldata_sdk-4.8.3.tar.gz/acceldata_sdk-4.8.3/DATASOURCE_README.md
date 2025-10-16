# Datasource APIs

Acceldata SDK has full access on catalog APIs as well. 

##### Datasource API
Torch has support for more 15+ datasource crawling support. 

```python
# Get datasource
ds_res = torch_client.get_datasource('snowflake_ds_local')
ds_res = torch_client.get_datasource(5, properties=True)

# Get datasources based on type
datasources = torch_client.get_datasources(const.AssetSourceType.SNOWFLAKE)

```


##### Assets APIs
Acceldata sdk has methods to get assets in the given datasource.
```python
from acceldata_sdk.models.create_asset import AssetMetadata

# Get asset by id/uid
asset = torchclient.get_asset(1)
asset = torch_client.get_asset('Feature_bag_datasource.feature_1')
```
##### Asset's tags, labels, metadata and sample data
User can add tags, labels custom metadata and also get sample data of the asset using sdk.
Tags and labels can be used to filter out asset easily.

```python
# asset metadata
from acceldata_sdk.models.tags import AssetLabel, CustomAssetMetadata
asset = torch_client.get_asset(asset_id)

# Get metadata of an asset
asset.get_metadata()

# Get all tags
tags = asset.get_tags()

# Add tag asset
tag_add = asset.add_tag(tag='asset_tag')

# Add asset labels
labels = asset.add_labels(labels=[AssetLabel('test1', 'demo1'), AssetLabel('test2', 'demo2')])

# Get asset labels
labels = asset.get_labels()

# Add custom metadata
asset.add_custom_metadata(custom_metadata=[CustomAssetMetadata('testcm1', 'democm1'), CustomAssetMetadata('testcm2', 'democm2')])
```

##### Crawler Operations
User can start crawler as well as check for running crawler status.
```python
# Start a crawler
datasource.start_crawler()
torch_client.start_crawler('datasource_name')

# Get running crawler status
datasource.get_crawler_status()
torch_client.get_crawler_status('datasource_name')

```

##### Trigger policies, Profiling and sampling of an asset
Crawled assets can be profiled and sampled with use of spark jobs running on the livy. 
Furthermore, Created policies (Recon + DQ) can be triggered too.

```python
import acceldata_sdk.constants as const

# profile an asset, get profile req details, cancel profile
profile_res = asset.start_profile(profiling_type=ProfilingType.FULL)

profile_req_details = profile_res.get_status()

cancel_profile_res = profile_res.cancel()

profile_res = asset.get_latest_profile_status()

profile_req_details_by_req_id = torch_client.get_profile_status(asset_id=profile_req_details.assetId,
                                                                req_id=profile_req_details.id)

# sample data
sample_data = asset.sample_data()

# Rule execution and status
# Execute policy
execute_dq_rule = torch_client.execute_policy(const.PolicyType.DATA_QUALITY, 1114, incremental=False)
failure_strategy = const.FailureStrategy.DoNotFail
# Get policy execution result
result = torch_client.get_policy_execution_result(
    policy_type=const.PolicyType.DATA_QUALITY,
    execution_id=execute_dq_rule.id,
    failure_strategy=failure_strategy
)

# Get policy and execute
from acceldata_sdk.models.ruleExecutionResult import RuleType, PolicyFilter

rule = torch_client.get_policy(const.PolicyType.RECONCILIATION, "auth001_reconciliation")

# Execute policy
async_execution = rule.execute(sync=False)
# Get execution result
async_execution_result = async_execution.get_result()
# Get current execution status
async_execution_status = async_execution.get_status()
# Cancel policy execution job
cancel_rule = async_execution.cancel()

# List all executions
# List executions by id
dq_rule_executions = torch_client.policy_executions(1114, RuleType.DATA_QUALITY)
# List executions by name
dq_rule_executions = torch_client.policy_executions('dq-scala', RuleType.DATA_QUALITY)

# List executions by rule
recon_rule_executions = rule.get_executions()
filter = PolicyFilter(policyType=RuleType.RECONCILIATION, enable=True)
# List all rules
recon_rules = torch_client.list_all_policies(filter=filter)
```