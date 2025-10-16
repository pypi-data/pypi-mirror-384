import os
import sys
import re

from typing import List

from alibabacloud_cr20181201.client import Client as cr20181201Client
from alibabacloud_credentials.client import Client as CredentialClient
from alibabacloud_tea_openapi import models as open_api_models
from alibabacloud_cr20181201 import models as cr_20181201_models
from alibabacloud_tea_util import models as util_models
from alibabacloud_tea_util.client import Client as UtilClient

from pixelarraylib.monitor.feishu import Feishu

feishu_alert = Feishu("devtoolkit服务报警")


class ACRUtils:
    def __init__(self, region_id: str, access_key_id: str, access_key_secret: str):
        self.region_id = region_id
        self.access_key_id = access_key_id
        self.access_key_secret = access_key_secret
        self.client = self._create_client()

    def _create_client(self):
        credential = CredentialClient()
        config = open_api_models.Config(
            credential=credential,
            access_key_id=self.access_key_id,
            access_key_secret=self.access_key_secret,
        )
        # Endpoint 请参考 https://api.aliyun.com/product/cr
        config.endpoint = f"cr.{self.region_id}.aliyuncs.com"
        return cr20181201Client(config)

    def list_instances(self):
        """
        description:
            列出容器镜像服务实例
        parameters:
            None
        return:
            dict: 包含实例列表的响应数据
            success(bool): 是否成功
        """

        try:
            request = cr_20181201_models.ListInstanceRequest()
            response = self.client.list_instance(request)
            return response.body.to_map(), True
        except Exception as e:
            feishu_alert.send(f"列出实例失败: {e}")
            return {}, False

    def create_namespace(self, instance_id: str, namespace_name: str):
        """
        description:
            创建命名空间
        parameters:
            instance_id (str): 实例ID
            namespace_name (str): 命名空间名称
        return:
            dict: 创建结果
            success(bool): 是否成功
        """

        try:
            request = cr_20181201_models.CreateNamespaceRequest(
                instance_id=instance_id, namespace_name=namespace_name
            )
            response = self.client.create_namespace(request)
            return response.body.to_map(), True
        except Exception as e:
            feishu_alert.send(f"创建命名空间失败: {e}")
            return {}, False

    def delete_namespace(self, instance_id: str, namespace_name: str):
        """
        description:
            删除命名空间
        parameters:
            instance_id (str): 实例ID
            namespace_name (str): 命名空间名称
        return:
            dict: 删除结果
            success(bool): 是否成功
        """
        try:
            request = cr_20181201_models.DeleteNamespaceRequest(
                instance_id=instance_id, namespace_name=namespace_name
            )
            response = self.client.delete_namespace(request)
            return response.body.to_map(), True
        except Exception as e:
            feishu_alert.send(f"删除命名空间失败: {e}")
            return {}, False

    def list_namespaces(self, instance_id: str):
        """
        description:
            列出命名空间
        parameters:
            instance_id (str): 实例ID
        return:
            dict: 包含命名空间列表的响应数据
            success(bool): 是否成功
        """
        try:
            request = cr_20181201_models.ListNamespaceRequest(instance_id=instance_id)
            response = self.client.list_namespace(request)
            return response.body.to_map(), True
        except Exception as e:
            feishu_alert.send(f"列出命名空间失败: {e}")
            return {}, False

    def exists_namespace(self, instance_id: str, namespace_name: str):
        """
        description:
            判断命名空间是否存在
        parameters:
            instance_id (str): 实例ID
            namespace_name (str): 命名空间名称
        return:
            bool: 是否存在
        """
        response, success = self.list_namespaces(instance_id)
        if not success:
            return False, False
        namespace_names = [
            namespace["NamespaceName"] for namespace in response["Namespaces"]
        ]
        return namespace_name in namespace_names, True

    def create_repository(
        self,
        instance_id: str,
        namespace_name: str,
        repository_name: str,
        repository_type: str,
        summary: str,
    ):
        """
        description:
            创建仓库
        parameters:
            instance_id (str): 实例ID
            namespace_name (str): 命名空间名称
            repository_name (str): 仓库名称
            repository_type (str): 仓库类型
            summary (str): 仓库摘要
        return:
            dict: 创建结果
            success(bool): 是否成功
        """
        if not re.fullmatch(r"[a-z\-]+", repository_name):
            print("仓库名称只能包含小写英文字母和横杠")
            return {}, False
        try:
            request = cr_20181201_models.CreateRepositoryRequest(
                instance_id=instance_id,
                repo_namespace_name=namespace_name,
                repo_name=repository_name,
                repo_type=repository_type,
                summary=summary,
            )
            response = self.client.create_repository(request)
            return response.body.to_map(), True
        except Exception as e:
            feishu_alert.send(f"创建仓库失败: {e}")
            return {}, False

    def list_repositories(self, instance_id: str, namespace_name: str):
        """
        description:
            列出仓库
        parameters:
            instance_id (str): 实例ID
            namespace_name (str): 命名空间名称
        return:
            dict: 包含仓库列表的响应数据
            success(bool): 是否成功
        """
        try:
            request = cr_20181201_models.ListRepositoryRequest(
                instance_id=instance_id, repo_namespace_name=namespace_name
            )
            response = self.client.list_repository(request)
            return response.body.to_map(), True
        except Exception as e:
            feishu_alert.send(f"列出仓库失败: {e}")
            return {}, False

    def exists_repository(
        self, instance_id: str, namespace_name: str, repository_name: str
    ):
        """
        description:
            判断仓库是否存在
        parameters:
            instance_id (str): 实例ID
            namespace_name (str): 命名空间名称
            repository_name (str): 仓库名称
        return:
            bool: 是否存在
        """
        response, success = self.list_repositories(instance_id, namespace_name)
        if not success:
            return False, False
        repository_names = [
            repository["RepoName"] for repository in response["Repositories"]
        ]
        return repository_name in repository_names, True

    def delete_repository(
        self, instance_id: str, namespace_name: str, repository_id: str
    ):
        """
        description:
            删除仓库
        parameters:
            instance_id (str): 实例ID
            namespace_name (str): 命名空间名称
            repository_id (str): 仓库ID
        return:
            dict: 删除结果
            success(bool): 是否成功
        """
        try:
            request = cr_20181201_models.DeleteRepositoryRequest(
                instance_id=instance_id,
                repo_namespace_name=namespace_name,
                repo_id=repository_id,
            )
            response = self.client.delete_repository(request)
            return response.body.to_map(), True
        except Exception as e:
            feishu_alert.send(f"删除仓库失败: {e}")
            return {}, False

    def get_repository(
        self, instance_id: str, namespace_name: str, repository_name: str
    ):
        """
        description:
            获取仓库详情信息
        parameters:
            instance_id (str): 实例ID
            namespace_name (str): 命名空间名称
            repository_name (str): 仓库名称
        return:
            dict: 详情信息
            success(bool): 是否成功
        """
        try:
            request = cr_20181201_models.GetRepositoryRequest(
                instance_id=instance_id,
                repo_namespace_name=namespace_name,
                repo_name=repository_name,
            )
            response = self.client.get_repository(request)
            return response.body.to_map(), True
        except Exception as e:
            feishu_alert.send(f"获取仓库详情失败: {e}")
            return {}, False
