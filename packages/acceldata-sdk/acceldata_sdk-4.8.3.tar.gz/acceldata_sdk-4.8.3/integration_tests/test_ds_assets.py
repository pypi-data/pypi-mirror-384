from acceldata_sdk.torch_client import TorchClient
import test_constants as test_const
import pprint
from acceldata_sdk.models.tags import AssetLabel, CustomAssetMetadata
from acceldata_sdk.models.profile import Profile, ProfileRequest, ProfilingType
from acceldata_sdk.errors import APIError, TorchSdkException
import time
from test_commons import retry_operation

pp = pprint.PrettyPrinter(indent=4)


class TestDS:
    torch_client = TorchClient(**test_const.torch_credentials)

    def test_get_datasource(self):
        ds_name = self.torch_client.get_datasource(test_const.ds_name, True)
        assert ds_name is not None

    def test_get_datasource_id(self):
        ds_id = self.torch_client.get_datasource(test_const.ds_id, False)
        assert ds_id is not None

    def test_get_all_datsource(self):
        dss = self.torch_client.get_datasources()
        assert dss is not None

    def test_get_ds_crawler(self):
        ds_id = self.torch_client.get_datasource(test_const.ds_id, True)
        status = ds_id.get_crawler_status()
        assert status is not None

    def test_start_crawler(self):
        ds_name = self.torch_client.get_datasource(test_const.ds_name, False)

        def operation():
            return ds_name.start_crawler()

        start_crawler = retry_operation(
            operation,
            test_const.MAX_RETRIES,
            test_const.RETRY_INTERVAL)
        time.sleep(15)
        status = ds_name.get_crawler_status()
        assert status is not None


class TestAsset:
    torch_client = TorchClient(**test_const.torch_credentials)

    def test_get_asset(self):
        asset = self.torch_client.get_asset(test_const.asset_uid)
        assert asset is not None

    def test_get_asset_id(self):
        asset = self.torch_client.get_asset(test_const.asset_id)
        assert asset is not None

    def test_get_asset_metadata(self):
        asset = self.torch_client.get_asset(test_const.asset_id)
        metadata_asset = asset.get_metadata()
        assert metadata_asset is not None

    def test_get_asset_sample_data(self):
        asset = self.torch_client.get_asset(test_const.asset_id)
        sample_data_asset = asset.sample_data()
        assert sample_data_asset is not None

    def test_get_asset_labels(self):
        asset = self.torch_client.get_asset(test_const.asset_id)
        labels_asset = asset.get_labels()
        assert labels_asset is not None

    def test_add_asset_labels(self):
        asset = self.torch_client.get_asset(test_const.asset_id)
        asset.add_labels(labels=[AssetLabel('test12', 'shubh12'), AssetLabel('test22', 'shubh32')])
        labels_asset = asset.get_labels()
        labels_asset = asset.get_labels()
        assert labels_asset is not None

    def test_add_asset_custom_metadata(self):
        asset = self.torch_client.get_asset(test_const.asset_id)
        asset.add_custom_metadata(
            custom_metadata=[CustomAssetMetadata('testcm1', 'shubhcm1'), CustomAssetMetadata('testcm2', 'shubhcm2')])
        metadata_asset = asset.get_metadata()
        assert metadata_asset is not None

    def test_profile_status(self):
        asset = self.torch_client.get_asset(test_const.asset_id)
        latest_profile_status_asset = asset.get_latest_profile_status()
        assert latest_profile_status_asset is not None

    def test_add_tag(self):
        asset = self.torch_client.get_asset(test_const.asset_id)
        try:
            tag = asset.add_tag('test_tag')
            assert tag is not None, "Tag should not be None"
            print("Tag added successfully")
        except APIError as e:
            error_message = str(e)
            assert "A tag already exists with the same name" in error_message, \
                f"Unexpected error message: {error_message}"
            print(f"Expected error occurred: {error_message}")

    def test_cancel_profile(self):
        asset = self.torch_client.get_asset(test_const.asset_id)

        def operation():
            return asset.start_profile(ProfilingType.FULL)

        start_profile_asset = retry_operation(
            operation,
            test_const.MAX_RETRIES,
            test_const.RETRY_INTERVAL)
        time.sleep(15)
        profile_status = start_profile_asset.get_status()
        if profile_status['profileRequest']['status'] == 'IN PROGRESS':
            cancel_res = start_profile_asset.cancel()
            assert cancel_res is not None

    def test_execute_profile(self):
        asset = self.torch_client.get_asset(test_const.asset_id)

        def operation():
            return asset.start_profile(ProfilingType.FULL)

        start_profile_asset = retry_operation(
            operation,
            test_const.MAX_RETRIES,
            test_const.RETRY_INTERVAL)

        profile_status = start_profile_asset.get_status()
        assert profile_status is not None
