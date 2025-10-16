import json

from tencentcloud.wedata.v20210820.wedata_client import WedataClient
from tencentcloud.wedata.v20250806.wedata_client import WedataClient as WedataClientV2
from tencentcloud.common import credential
from tencentcloud.common.exception.tencent_cloud_sdk_exception import TencentCloudSDKException
from wedata.feature_store.cloud_sdk_client.utils import get_client_profile, set_request_header
import wedata.feature_store.cloud_sdk_client.models as models


class FeatureCloudSDK:
    def __init__(self, secret_id: str, secret_key: str, region: str):
        self._client = WedataClient(credential.Credential(secret_id, secret_key), region, get_client_profile())
        self._client_v2 = WedataClientV2(credential.Credential(secret_id, secret_key), region, get_client_profile())

    def CreateOnlineFeatureTable(self, request: models.CreateOnlineFeatureTableRequest) -> 'models.CreateOnlineFeatureTableResponse':
        """
        创建在线特征表
        Args:
            request: 创建请求参数

        Returns:
            创建结果响应
        """
        try:
            params = request._serialize()
            headers = set_request_header(request.headers)
            print(f"CreateOnlineFeatureTable params: {params}")
            print(f"CreateOnlineFeatureTable headers: {headers}")
            self._client._apiVersion = "2021-08-20"
            body = self._client.call("CreateOnlineFeatureTable", params, headers=headers)
            response = json.loads(body)
            model = models.CreateOnlineFeatureTableResponse()
            model._deserialize(response["Response"])
            print("CreateOnlineFeatureTable Response: ", response)
            return model
        except Exception as e:
            if isinstance(e, TencentCloudSDKException):
                raise
            else:
                raise TencentCloudSDKException(type(e).__name__, str(e))

    def DescribeNormalSchedulerExecutorGroups(self, request: models.DescribeNormalSchedulerExecutorGroupsRequest) -> 'models.DescribeNormalSchedulerExecutorGroupsResponse':
        """
        查询普通调度器执行器组
        Args:
            request: 查询请求参数

        Returns:
            查询结果响应
        """
        try:
            params = request._serialize()
            headers = set_request_header(request.headers)
            print(f"DescribeNormalSchedulerExecutorGroups params: {params}")
            print(f"DescribeNormalSchedulerExecutorGroups headers: {headers}")
            self._client._apiVersion = "2021-08-20"
            body = self._client.call("DescribeNormalSchedulerExecutorGroups", params, headers=headers)
            response = json.loads(body)
            model = models.DescribeNormalSchedulerExecutorGroupsResponse()
            model._deserialize(response["Response"])
            print("DescribeNormalSchedulerExecutorGroups Response: ", response)
            return model
        except Exception as e:
            if isinstance(e, TencentCloudSDKException):
                raise
            else:
                raise TencentCloudSDKException(type(e).__name__, str(e))

    def RefreshFeatureTable(self, request: models.RefreshFeatureTableRequest) -> 'models.RefreshFeatureTableResponse':
        """
        刷新特征表
        Args:
            request: 刷新请求参数
        Returns:
            刷新结果响应
        """
        try:
            params = request._serialize()
            headers = set_request_header(request.headers)
            print(f"RefreshFeatureTable params: {params}")
            print(f"RefreshFeatureTable headers: {headers}")
            self._client_v2._apiVersion = "2025-08-06"
            body = self._client_v2.call("RefreshFeatureTable", params, headers=headers)
            response = json.loads(body)
            model = models.RefreshFeatureTableResponse()
            model._deserialize(response["Response"])
            print("RefreshFeatureTable Response: ", response)
            return model
        except Exception as e:
            if isinstance(e, TencentCloudSDKException):
                raise
            else:
                raise TencentCloudSDKException(type(e).__name__, str(e))