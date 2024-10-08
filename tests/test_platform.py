from aiounittest import AsyncTestCase
from unittest.mock import patch

from optscale_arcee.platform import (
    Platform,
    AzureCollector,
    CollectorFactory,
    PlatformType,
    AlibabaCollector,
    AwsCollector,
    PlatformMeta,
    InstanceLifeCycle,
)
from tests.test_data import TestDataAzure


class TestPlatform(AsyncTestCase):
    def test_platform_is_static(self):
        self.assertRaises(TypeError, Platform())

    @patch("optscale_arcee.platform.Platform.board_version")
    async def test_platform_factory(self, mock_board_version):
        mock_board_version.return_value = PlatformType.aws
        self.assertEqual(await CollectorFactory.get(), AwsCollector)


class TestAzureCollector(AsyncTestCase):
    @patch("optscale_arcee.platform.AzureCollector.collect")
    async def test_azure_base_collector(self, mocked_collect):
        mocked_collect.return_value = TestDataAzure.get_test_data()
        platform_meta = await AzureCollector().get_platform_meta()
        self.assertTrue(isinstance(platform_meta, PlatformMeta))
        self.assertTrue(platform_meta.platform_type, PlatformType.azure)
        self.assertTrue(platform_meta.local_ip)
        self.assertTrue(platform_meta.instance_lc, InstanceLifeCycle.Unknown)
        self.assertTrue(platform_meta.to_dict())

    @patch("optscale_arcee.platform.AzureCollector.collect")
    async def test_azure_no_network(self, mocked_collect):
        mocked_collect.return_value = TestDataAzure.get_test_data_no_network()
        platform_meta = await AzureCollector().get_platform_meta()
        self.assertTrue(isinstance(platform_meta, PlatformMeta))
        self.assertTrue(platform_meta.platform_type, PlatformType.azure)
        self.assertFalse(platform_meta.public_ip)
        self.assertFalse(platform_meta.local_ip)
        self.assertTrue(platform_meta.instance_lc, InstanceLifeCycle.Unknown)
        self.assertTrue(platform_meta.to_dict())

    @patch("optscale_arcee.platform.AzureCollector.collect")
    async def test_azure_no_data(self, mocked_collect):
        mocked_collect.return_value = None
        platform_meta = await AzureCollector().get_platform_meta()
        self.assertTrue(isinstance(platform_meta, PlatformMeta))
        self.assertTrue(platform_meta.platform_type, PlatformType.azure)
        self.assertTrue(platform_meta.instance_lc, InstanceLifeCycle.Unknown)
        self.assertTrue(platform_meta.to_dict())


class TestAwsCollector(AsyncTestCase):
    @patch("optscale_arcee.platform.AwsCollector.get_instance_type")
    @patch("optscale_arcee.platform.AwsCollector.get_region")
    @patch("optscale_arcee.platform.AwsCollector.get_az")
    @patch("optscale_arcee.platform.AwsCollector.get_life_cycle")
    @patch("optscale_arcee.platform.AwsCollector.get_public_ip")
    @patch("optscale_arcee.platform.AwsCollector.get_local_ip")
    @patch("optscale_arcee.platform.AwsCollector.get_account_id")
    @patch("optscale_arcee.platform.AwsCollector.get_instance_id")
    async def test_aws_collector_iface(
        self,
        m_instance_id,
        m_account_id,
        m_local_ip,
        m_public_ip,
        m_life_cycle,
        m_az,
        m_region,
        m_type,
    ):
        m_instance_id.return_value = "i-09dc9f5553f84a9ad"
        m_account_id.return_value = "00000000000"
        m_local_ip.return_value = "172.31.24.6"
        m_public_ip.return_value = "1.1.1.1"
        m_life_cycle.return_value = InstanceLifeCycle.OnDemand
        m_az.return_value = "eu-central-1a"
        m_region.return_value = "eu-central-1a"
        m_type.return_value = "m6in.large"
        platform_meta = await AwsCollector().get_platform_meta()
        self.assertTrue(platform_meta.platform_type, PlatformType.aws)
        self.assertTrue(platform_meta.instance_lc, InstanceLifeCycle.OnDemand)
        self.assertTrue(platform_meta.to_dict())


class TestAlibabaCollector(AsyncTestCase):
    @patch("optscale_arcee.platform.AlibabaCollector.get_instance_type")
    @patch("optscale_arcee.platform.AlibabaCollector.get_region")
    @patch("optscale_arcee.platform.AlibabaCollector.get_az")
    @patch("optscale_arcee.platform.AlibabaCollector.get_life_cycle")
    @patch("optscale_arcee.platform.AlibabaCollector.get_public_ip")
    @patch("optscale_arcee.platform.AlibabaCollector.get_local_ip")
    @patch("optscale_arcee.platform.AlibabaCollector.get_account_id")
    @patch("optscale_arcee.platform.AlibabaCollector.get_instance_id")
    async def test_ali_collector_iface(
        self,
        m_instance_id,
        m_account_id,
        m_local_ip,
        m_public_ip,
        m_life_cycle,
        m_az,
        m_region,
        m_type,
    ):
        m_instance_id.return_value = "i-gw8csaxjubfr17s2e1ip"
        m_account_id.return_value = "00000000000"
        m_local_ip.return_value = "192.168.0.83"
        m_public_ip.return_value = "2.2.2.2"
        m_life_cycle.return_value = InstanceLifeCycle.Spot
        m_az.return_value = "eu-central-1a"
        m_region.return_value = "eu-central-1"
        m_type.return_value = "ecs.t5-c1m1.large"
        platform_meta = await AlibabaCollector().get_platform_meta()
        self.assertTrue(platform_meta.platform_type, PlatformType.alibaba)
        self.assertTrue(platform_meta.instance_lc, InstanceLifeCycle.Spot)
        self.assertTrue(platform_meta.to_dict())
