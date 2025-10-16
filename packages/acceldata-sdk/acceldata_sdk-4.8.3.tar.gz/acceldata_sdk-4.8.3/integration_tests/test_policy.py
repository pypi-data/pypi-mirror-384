from acceldata_sdk.torch_client import TorchClient
import test_constants as test_const
import pprint
import acceldata_sdk.constants as const
from acceldata_sdk.models.ruleExecutionResult import RuleType, PolicyFilter, ExecutionPeriod

pp = pprint.PrettyPrinter(indent=4)


class TestDQPolicy:
    torch_client = TorchClient(**test_const.torch_credentials)

    def __init__(self):
        self.dq_policy_name = test_const.dq_policy_name
        self.dq_policy_id = self.torch_client.get_policy(const.PolicyType.DATA_QUALITY, self.dq_policy_name)

    def test_get_policy(self):
        dq_rule = self.torch_client.get_policy(const.PolicyType.DATA_QUALITY, self.dq_policy_id)
        assert dq_rule is not None

    def test_get_policy_without_type(self):
        dq_rule = self.torch_client.get_policy(identifier=self.dq_policy_id)
        pp.pprint("dq_rule")
        pp.pprint(dq_rule)
        assert dq_rule is not None

    def test_get_all_policy(self):
        filter = PolicyFilter(policyType=RuleType.DATA_QUALITY, enable=True)
        dq_rules = self.torch_client.list_all_policies(filter=filter)
        assert dq_rules is not None

    def test_cancel_policy(self):
        dq_rule = self.torch_client.get_policy(const.PolicyType.DATA_QUALITY, self.dq_policy_id)
        async_executor = dq_rule.execute(sync=False)
        if async_executor.errorMessage is None:
            async_execution_status = async_executor.get_status()
            pp.pprint('async_execution_status')
            pp.pprint(async_execution_status)
            async_execution_cancel = async_executor.cancel()
            pp.pprint('async_execution_cancel')
            pp.pprint(async_execution_cancel)

    def test_execute_policy(self):
        dq_rule = self.torch_client.get_policy(const.PolicyType.DATA_QUALITY, self.dq_policy_id)
        async_executor = dq_rule.execute(sync=False)
        if async_executor.errorMessage is None:
            async_execution_status = async_executor.get_status()
            pp.pprint('async_execution_status')
            pp.pprint(async_execution_status)
            async_execution_result = async_executor.get_result()
            pp.pprint('async_execution_result')
            pp.pprint(async_execution_result)

    def test_get_policy_executions(self):
        dq_rule_executions = self.torch_client.policy_executions(self.dq_policy_id, RuleType.DATA_QUALITY)
        assert dq_rule_executions is not None


class TestReconPolicy:
    def __init__(self):
        self.torch_client = TorchClient(**test_const.torch_credentials)
        self.recon_policy_name = test_const.recon_policy_name
        self.recon_policy_id = self.torch_client.get_policy(const.PolicyType.RECONCILIATION, self.recon_policy_name)

    def test_get_policy(self):
        recon_rule = self.torch_client.get_policy(const.PolicyType.RECONCILIATION, self.recon_policy_id)
        assert recon_rule is not None

    def test_get_policy_without_type(self):
        recon_rule = self.torch_client.get_policy(identifier=self.recon_policy_id)
        pp.pprint("recon_rule")
        pp.pprint(recon_rule)
        assert recon_rule is not None

    def test_get_all_policy(self):
        filter = PolicyFilter(policyType=RuleType.RECONCILIATION, enable=True)
        recon_rules = self.torch_client.list_all_policies(filter=filter)
        assert recon_rules is not None

    def test_cancel_policy(self):
        recon_rule = self.torch_client.get_policy(const.PolicyType.RECONCILIATION, self.recon_policy_id)
        async_executor = recon_rule.execute(sync=False)
        if async_executor.errorMessage is None:
            async_execution_status = async_executor.get_status()
            pp.pprint('async_execution_status')
            pp.pprint(async_execution_status)
            async_execution_cancel = async_executor.cancel()
            pp.pprint('async_execution_cancel')
            pp.pprint(async_execution_cancel)

    def test_execute_policy(self):
        recon_rule = self.torch_client.get_policy(const.PolicyType.RECONCILIATION, self.recon_policy_id)
        async_executor = recon_rule.execute(sync=False)
        if async_executor.errorMessage is None:
            async_execution_status = async_executor.get_status()
            pp.pprint('async_execution_status')
            pp.pprint(async_execution_status)
            async_execution_result = async_executor.get_result()
            pp.pprint('async_execution_result')
            pp.pprint(async_execution_result)

    def test_get_policy_executions(self):
        recon_rule_executions = self.torch_client.policy_executions(self.recon_policy_id, RuleType.RECONCILIATION)
        assert recon_rule_executions is not None
