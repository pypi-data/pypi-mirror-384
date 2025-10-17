#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
SARM SDK 应用载体 API V2版本

提供应用载体相关的API操作，V2版本已移除所有数据校验逻辑，提供更快的数据处理性能。
"""

from typing import List, Dict, Any, Optional, TYPE_CHECKING
from ..models.carrier import CarrierInsert, Carrier
from ..models.response import BatchOperationResult

if TYPE_CHECKING:
    from ..client_v2 import SARMClientV2


class CarrierAPI:
    """应用载体API类 V2版本 - 已移除数据校验"""

    def __init__(self, client: 'SARMClientV2'):
        self.client = client

    def create_batch(
        self,
        carriers: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        批量创建应用载体(预审)

        对应OpenAPI: POST /api/v2/carrier/temporary/insert

        Args:
            carriers: 应用载体数据列表,每个元素格式如下:
                {
                    # 必填字段
                    "name": "应用载体名称(必填,string)",
                    "carrier_type": "应用载体类型(必填,string)",  # service_address/code_repo/artifact
                    "source": "应用载体信息的来源(必填,string,用户自定义标签字段)",

                    # 可选基础字段
                    "application_unique_id_list": ["应用唯一id"],  # 可选,array[string]
                    "component_unique_id_list": ["成分唯一id"],  # 可选,array[string]
                    "carrier_unique_id": "载体唯一id(可选,string)",
                    "description": "应用载体的描述(可选,string)",
                    "tag": ["标签1", "标签2"],  # 可选,array[string]
                    "carrier_owner_unique_id": "负责人唯一id(可选,string)",

                    # 服务地址类型字段(carrier_type=service_address时使用)
                    "protocol": "协议类型(string)",  # http/https/tcp/udp
                    "ip": "ip地址(string)",
                    "port": 端口号(integer),
                    "path": "URL路径(string)",
                    "domain": "域名(string)",
                    "internet_ip": "互联网IP(string)",
                    "nat_ip": "NAT IP(string)",
                    "internal_ip": "内网IP(string)",

                    # 代码仓库类型字段(carrier_type=code_repo时使用)
                    "repo_namespace": "仓库命名空间/组织(string)",
                    "repo_name": "仓库名称(string)",
                    "repo_url": "仓库URL(string)",
                    "branch": "分支(string)"
                }

        Returns:
            Dict[str, Any]: 批量操作结果,响应格式:
                {
                    "data": "success",
                    "code": 200,
                    "msg_en": "...",
                    "msg_zh": "..."
                }

        Example:
            >>> # 示例1: 创建服务地址类型载体
            >>> carriers = [{
            ...     "carrier_type": "service_address",
            ...     "name": "用户服务API",
            ...     "description": "用户管理服务接口",
            ...     "source": "manual",
            ...     "protocol": "https",
            ...     "domain": "api.example.com",
            ...     "port": 443,
            ...     "path": "/api/v1/users",
            ...     "internal_ip": "192.168.1.100",
            ...     "application_unique_id_list": ["app_001"],
            ...     "carrier_owner_unique_id": "user_001"
            ... }]
            >>> result = api.create_batch(carriers)
            >>>
            >>> # 示例2: 创建代码仓库类型载体
            >>> carriers = [{
            ...     "carrier_type": "code_repo",
            ...     "name": "用户服务代码仓库",
            ...     "description": "用户管理服务源代码",
            ...     "source": "gitlab",
            ...     "repo_namespace": "backend",
            ...     "repo_name": "user-service",
            ...     "repo_url": "https://gitlab.com/backend/user-service.git",
            ...     "branch": "main",
            ...     "application_unique_id_list": ["app_001"]
            ... }]
            >>> result = api.create_batch(carriers)
        """
        # 发送请求到V2预审接口
        response = self.client.post(
            '/api/v2/carrier/temporary/insert',
            data=carriers
        )
        return response

    def create(
        self,
        carrier_type: str,
        name: str,
        source: str,
        description: Optional[str] = None,
        carrier_unique_id: Optional[str] = None,
        application_unique_id_list: Optional[List[str]] = None,
        component_unique_id_list: Optional[List[str]] = None,
        carrier_owner_unique_id: Optional[str] = None,
        tag: Optional[List[str]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        创建单个应用载体(预审)

        对应OpenAPI: POST /api/v2/carrier/temporary/insert (单条数据)

        Args:
            carrier_type: 应用载体类型(必填,string), 可选值: service_address/code_repo/artifact
            name: 应用载体名称(必填,string)
            source: 应用载体信息的来源(必填,string,用户自定义标签字段)
            description: 应用载体的描述(可选,string)
            carrier_unique_id: 载体唯一id(可选,string)
            application_unique_id_list: 应用唯一id列表(可选,array[string])
            component_unique_id_list: 成分唯一id列表(可选,array[string])
            carrier_owner_unique_id: 负责人唯一id(可选,string)
            tag: 标签列表(可选,array[string])
            **kwargs: 其他载体类型特定字段,如:
                - 服务地址(carrier_type=service_address):
                  protocol(string): 协议类型 http/https/tcp/udp
                  ip(string): ip地址
                  port(integer): 端口号
                  path(string): URL路径
                  domain(string): 域名
                  internet_ip(string): 互联网IP
                  nat_ip(string): NAT IP
                  internal_ip(string): 内网IP
                - 代码仓库(carrier_type=code_repo):
                  repo_namespace(string): 仓库命名空间/组织
                  repo_name(string): 仓库名称
                  repo_url(string): 仓库URL
                  branch(string): 分支

        Returns:
            Dict[str, Any]: 操作结果,响应格式:
                {
                    "data": "success",
                    "code": 200,
                    "msg_en": "...",
                    "msg_zh": "..."
                }

        Example:
            >>> # 示例1: 创建服务地址
            >>> result = api.create(
            ...     carrier_type="service_address",
            ...     name="用户服务API",
            ...     source="manual",
            ...     description="用户管理服务接口",
            ...     protocol="https",
            ...     domain="api.example.com",
            ...     port=443,
            ...     path="/api/v1/users",
            ...     internal_ip="192.168.1.100",
            ...     application_unique_id_list=["app_001"],
            ...     carrier_owner_unique_id="user_001"
            ... )
            >>>
            >>> # 示例2: 创建代码仓库
            >>> result = api.create(
            ...     carrier_type="code_repo",
            ...     name="用户服务代码仓库",
            ...     source="gitlab",
            ...     description="用户管理服务源代码",
            ...     repo_namespace="backend",
            ...     repo_name="user-service",
            ...     repo_url="https://gitlab.com/backend/user-service.git",
            ...     branch="main",
            ...     application_unique_id_list=["app_001"]
            ... )
        """
        # 构建载体数据
        carrier_data = {
            "carrier_type": carrier_type,
            "name": name,
            "source": source
        }

        # 添加可选字段
        if description:
            carrier_data["description"] = description
        if carrier_unique_id:
            carrier_data["carrier_unique_id"] = carrier_unique_id
        if application_unique_id_list:
            carrier_data["application_unique_id_list"] = application_unique_id_list
        if component_unique_id_list:
            carrier_data["component_unique_id_list"] = component_unique_id_list
        if carrier_owner_unique_id:
            carrier_data["carrier_owner_unique_id"] = carrier_owner_unique_id
        if tag:
            carrier_data["tag"] = tag

        # 添加其他类型特定字段
        carrier_data.update(kwargs)

        return self.create_batch([carrier_data])

    def get_list_temporary(
        self,
        page: int = 1,
        limit: int = 50,
        name: Optional[str] = None,
        carrier_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        获取载体列表(预审)

        对应OpenAPI: POST /api/v2/carrier/temporary/get_list

        查询处于预审状态的载体数据,包括待审核和审核中的载体信息。

        Args:
            page: 页码(必填)
            limit: 每页条数(必填)
            name: 载体名称(可选,支持模糊搜索)
            carrier_type: 载体类型(可选), 可选值:
                - service_address: 服务地址
                - code_repo: 代码仓库
                - artifact: 制品
                注意: 可以不传但是不能为空串

        Returns:
            Dict[str, Any]: 预审载体列表响应,格式如下:
                {
                    "code": 200,
                    "data": {
                        "data_list": [
                            {
                                "temporary_carrier_id": 临时载体ID,
                                "carrier_unique_id": 唯一标识符,
                                "carrier_repeat_id": 载体重复ID,
                                "carrier_original_id": 载体辅助ID,
                                "carrier_type": 载体类型,
                                "name": 载体名称,
                                "description": 载体描述,
                                "created_at": 创建时间,
                                "updated_at": 更新时间,
                                "tags": 标签列表,
                                "source": 信息来源,
                                "protocol": 协议类型,
                                "ip": IP地址,
                                "port": 端口号,
                                "path": URL路径,
                                "domain": 域名,
                                "internet_ip": 互联网IP,
                                "nat_ip": NAT IP,
                                "internal_ip": 内网IP,
                                "repo_namespace": 仓库命名空间,
                                "repo_name": 仓库名称,
                                "repo_url": 仓库URL,
                                "branch": 分支名,
                                "carrier_owner_id": 负责人ID,
                                "carrier_owner_name": 负责人名称,
                                "carrier_owner_unique_id": 负责人唯一ID,
                                "data_processor": 数据处理人,
                                "factory_log_id": 工厂日志ID
                            }
                        ],
                        "total": 总记录数
                    },
                    "msg_en": 英文消息,
                    "msg_zh": 中文消息
                }

        Raises:
            ValueError: 当carrier_type为空字符串时抛出异常

        Example:
            >>> # 查询所有预审载体
            >>> result = api.get_list_temporary(page=1, limit=10)
            >>>
            >>> # 按名称模糊搜索
            >>> result = api.get_list_temporary(
            ...     page=1,
            ...     limit=10,
            ...     name="user-service"
            ... )
            >>>
            >>> # 按类型查询
            >>> result = api.get_list_temporary(
            ...     page=1,
            ...     limit=10,
            ...     carrier_type="service_address"
            ... )
            >>>
            >>> # 访问结果
            >>> carriers = result['data']['data_list']
            >>> total = result['data']['total']
        """
        # 验证carrier_type不能为空字符串
        if carrier_type is not None and carrier_type == "":
            raise ValueError("carrier_type 可以不传但是不能为空串")

        # 构建请求数据
        request_data: Dict[str, Any] = {
            "page": page,
            "limit": limit
        }

        # 添加可选查询条件
        if name:
            request_data["name"] = name
        if carrier_type:
            request_data["carrier_type"] = carrier_type

        # 发送POST请求查询预审载体
        response = self.client.post('/api/v2/carrier/temporary/get_list', data=request_data)
        return response

    def get_list_formal(
        self,
        page: int = 1,
        limit: int = 50,
        carrier_name: Optional[str] = None,
        carrier_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        获取载体列表(正式)

        对应OpenAPI: POST /api/v2/carrier/formal/get_list

        查询已发布的正式载体数据。

        Args:
            page: 页码(必填)
            limit: 每页条数(必填)
            carrier_name: 载体名称(可选,支持模糊搜索)
            carrier_type: 载体类型(可选), 可选值:
                - service_address: 服务地址
                - code_repo: 代码仓库
                - artifact: 制品

        Returns:
            Dict[str, Any]: 正式载体列表响应,格式如下:
                {
                    "code": 200,
                    "data": {
                        "data_list": [
                            {
                                "carrier_id": 载体ID,
                                "carrier_unique_id": 唯一标识符,
                                "carrier_repeat_id": 载体重复ID,
                                "carrier_original_id": 载体辅助ID,
                                "carrier_type": 载体类型,
                                "name": 载体名称,
                                "description": 载体描述,
                                "created_at": 创建时间,
                                "updated_at": 更新时间,
                                "tags": 标签列表,
                                "source": 信息来源,
                                "protocol": 协议类型,
                                "ip": IP地址,
                                "port": 端口号,
                                "path": URL路径,
                                "domain": 域名,
                                "internet_ip": 互联网IP,
                                "nat_ip": NAT IP,
                                "internal_ip": 内网IP,
                                "repo_namespace": 仓库命名空间,
                                "repo_name": 仓库名称,
                                "repo_url": 仓库URL,
                                "branch": 分支名,
                                "carrier_owner_id": 负责人ID,
                                "issue_count": 问题数量,
                                "data_processor": 数据处理人,
                                "data_status": 数据状态,
                                "factory_log_id": 工厂日志ID
                            }
                        ],
                        "total": 总记录数
                    },
                    "msg_en": 英文消息,
                    "msg_zh": 中文消息
                }

        Example:
            >>> # 查询所有正式载体
            >>> result = api.get_list_formal(page=1, limit=10)
            >>>
            >>> # 按名称模糊搜索
            >>> result = api.get_list_formal(
            ...     page=1,
            ...     limit=10,
            ...     carrier_name="user-service"
            ... )
            >>>
            >>> # 按类型查询
            >>> result = api.get_list_formal(
            ...     page=1,
            ...     limit=10,
            ...     carrier_type="code_repo"
            ... )
            >>>
            >>> # 组合查询
            >>> result = api.get_list_formal(
            ...     page=1,
            ...     limit=20,
            ...     carrier_name="api",
            ...     carrier_type="service_address"
            ... )
            >>>
            >>> # 访问结果
            >>> carriers = result['data']['data_list']
            >>> total = result['data']['total']
        """
        # 构建请求数据
        request_data: Dict[str, Any] = {
            "page": page,
            "limit": limit
        }

        # 添加可选查询条件
        if carrier_name:
            request_data["carrier_name"] = carrier_name
        if carrier_type:
            request_data["carrier_type"] = carrier_type

        # 发送POST请求查询正式载体
        response = self.client.post('/api/v2/carrier/formal/get_list', data=request_data)
        return response

    def get_list(
        self,
        page: int = 1,
        limit: int = 50,
        name: Optional[str] = None,
        carrier_type: Optional[str] = None,
        formal: bool = True
    ) -> Dict[str, Any]:
        """
        获取载体列表(统一入口)

        统一的载体列表查询方法,可通过formal参数切换查询预审或正式数据。

        Args:
            page: 页码(必填)
            limit: 每页条数(必填)
            name: 载体名称(可选,支持模糊搜索)
            carrier_type: 载体类型(可选), 可选值: service_address/code_repo/artifact
            formal: 是否查询正式数据(默认True), False则查询预审数据

        Returns:
            Dict[str, Any]: 载体列表响应

        Example:
            >>> # 查询正式载体(默认)
            >>> result = api.get_list(page=1, limit=10)
            >>>
            >>> # 查询预审载体
            >>> result = api.get_list(page=1, limit=10, formal=False)
            >>>
            >>> # 按名称搜索正式载体
            >>> result = api.get_list(
            ...     page=1,
            ...     limit=10,
            ...     name="user-service",
            ...     formal=True
            ... )
        """
        if formal:
            return self.get_list_formal(
                page=page,
                limit=limit,
                carrier_name=name,
                carrier_type=carrier_type
            )
        else:
            return self.get_list_temporary(
                page=page,
                limit=limit,
                name=name,
                carrier_type=carrier_type
            )

    def update_batch(
        self,
        carriers: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        批量更新应用载体

        Args:
            carriers: 应用载体数据列表

        Returns:
            操作结果
        """
        response = self.client.post(
            '/api/carrier/update',
            data=carriers
        )
        return response

    def update(self, carrier_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        更新单个应用载体

        Args:
            carrier_data: 载体数据

        Returns:
            操作结果
        """
        return self.update_batch([carrier_data])

    def delete_batch(self, carrier_ids: List[str]) -> Dict[str, Any]:
        """
        批量删除应用载体

        Args:
            carrier_ids: 载体ID列表

        Returns:
            操作结果
        """
        req = {}
        req["carrier_id_list"] = carrier_ids
        response = self.client.delete('/api/carrier/delete', data=req)
        return response

    def delete(self, carrier_id: str) -> Dict[str, Any]:
        """
        删除单个应用载体

        Args:
            carrier_id: 载体ID

        Returns:
            操作结果
        """
        return self.delete_batch([carrier_id])

    def get_carrier_unique_id(self, filters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        获取载体唯一ID

        Args:
            filters: 查询过滤条件

        Returns:
            载体唯一ID列表
        """
        data = filters or {}
        response = self.client.post('/api/carrier/get_carrier_unique_id', data=data)
        return response
