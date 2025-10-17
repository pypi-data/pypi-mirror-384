#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
SARM SDK 业务系统 API V2版本

提供业务系统相关的API操作，V2版本已移除所有数据校验逻辑，提供更快的数据处理性能。
"""

from typing import List, Dict, Any, Optional, TYPE_CHECKING
from ..models.response import BatchOperationResult

if TYPE_CHECKING:
    from ..client_v2 import SARMClientV2


class BusinessSystemAPI:
    """业务系统API类 V2版本 - 已移除数据校验"""

    def __init__(self, client: 'SARMClientV2'):
        self.client = client

    def create_batch(
        self,
        business_systems: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        批量创建业务系统

        Args:
            business_systems: 业务系统数据列表,每个元素格式如下:
                {
                    "business_system": {
                        "business_system_original_id": "原始ID",
                        "business_system_unique_id": "唯一ID(注意:通常由系统自动生成,不建议手动指定)",
                        "business_system_unique_pid": "父级唯一ID(当指定unique_id时必须提供有效的父级ID或留空)",
                        "business_system_name": "业务系统名称(必填)",
                        "business_system_desc": "描述",
                        "business_system_status": "active",  # active/maintenance/retired
                        "dep_id": "部门ID",
                        "dep_name": "部门名称",
                        "group_own": "所属组",
                        "group_own_id": "所属组ID",
                        "system_owner_name": "负责人名称",
                        "application_level_desc": "应用级别描述",
                        "develop_mode": "开发模式",
                        "cooperate_comp": "合作公司",
                        "source": "数据来源(必填), 可选值: 'sys' 或 'openApi'",
                        "business_system_original_pid": "父级原始ID",
                        "factory_log_id": "工厂日志ID",
                        "business_system_repeat_id": "重复ID"
                    },
                    "organize_unique_id": "组织唯一ID",
                    "organize_user_unique_id": "组织用户唯一ID"
                }

        Returns:
            Dict[str, Any]: 批量操作结果

        Example:
            >>> business_systems = [{
            ...     "business_system": {
            ...         "business_system_original_id": "bs001",
            ...         # 注意: business_system_unique_id 通常由系统自动生成，不建议手动指定
            ...         "business_system_name": "核心业务系统",
            ...         "business_system_desc": "系统描述",
            ...         "business_system_status": "active",
            ...         "source": "openApi"  # 必须是 "sys" 或 "openApi"
            ...     },
            ...     "organize_unique_id": "org_123",
            ...     "organize_user_unique_id": "user_456"
            ... }]
            >>> result = api.create_batch(business_systems)
        """
        # 发送请求到正确的端点
        response = self.client.post(
            '/api/business_system/temporary_business_system/create',
            data=business_systems
        )

        return response

    def create(
        self,
        business_system: Dict[str, Any],
        organize_unique_id: Optional[str] = None,
        organize_user_unique_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        创建单个业务系统

        Args:
            business_system: 业务系统数据字典,包含业务系统基本信息
            organize_unique_id: 组织唯一ID(可选)
            organize_user_unique_id: 组织用户唯一ID(可选)

        Returns:
            Dict[str, Any]: 操作结果

        Example:
            >>> business_system = {
            ...     "business_system_original_id": "bs001",
            ...     # 注意: business_system_unique_id 通常由系统自动生成，不建议手动指定
            ...     "business_system_name": "核心业务系统",
            ...     "business_system_desc": "公司核心业务系统",
            ...     "business_system_status": "active",
            ...     "dep_id": "dept001",
            ...     "dep_name": "技术部",
            ...     "source": "openApi"  # 必须是 "sys" 或 "openApi"
            ... }
            >>> result = api.create(
            ...     business_system=business_system,
            ...     organize_unique_id="org_123",
            ...     organize_user_unique_id="user_456"
            ... )
        """
        # 构建完整的请求数据
        request_data = {
            "business_system": business_system
        }

        if organize_unique_id:
            request_data["organize_unique_id"] = organize_unique_id

        if organize_user_unique_id:
            request_data["organize_user_unique_id"] = organize_user_unique_id

        return self.create_batch([request_data])

    def delete_batch(self, business_system_ids: List[str]):
        """
        批量删除业务系统
        注意：业务系统存在关联数据时无法删除

        Args:
            business_system_ids: 业务系统ID列表

        Returns:
            批量操作结果
        """
        data = {"business_system_id_list": business_system_ids}
        response = self.client.delete('/api/business_system/delete', data=data)
        return response

    def delete(self, business_system_id: str) -> BatchOperationResult:
        """
        删除单个业务系统

        Args:
            business_system_id: 业务系统ID

        Returns:
            操作结果
        """
        return self.delete_batch([business_system_id])

    def get_list(
        self,
        page: int = 1,
        limit: int = 10,
        business_system_unique_id: Optional[str] = None,
        business_system_name: Optional[str] = None,
        business_system_status: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        根据条件查询业务系统列表

        Args:
            page: 页码(默认1)
            limit: 每页条数(默认10)
            business_system_unique_id: 系统唯一ID(可选,用于筛选特定系统)
            business_system_name: 业务系统名称(可选,支持模糊搜索)
            business_system_status: 业务系统状态(可选), 可选值:
                - "active": 运行中
                - "maintenance": 维护中
                - "retired": 已退役

        Returns:
            Dict[str, Any]: 业务系统列表响应,格式如下:
                {
                    "code": 200,
                    "data": {
                        "list": [
                            {
                                "business_system_id": 系统主键,
                                "business_system_pid": 系统父级主键,
                                "business_system_name": 系统名称,
                                "business_system_level": 系统层级,
                                "parent_business_system": 父级系统名称,
                                "business_system_status": 系统状态,
                                "business_system_owner_id": 负责人主键,
                                "business_system_owner_nick_name": 负责人昵称,
                                "business_system_owner_name": 负责人用户名,
                                "business_system_desc": 系统描述,
                                "organize_id": 组织主键,
                                "organize_name": 组织名称,
                                "data_processor": 数据处理人主键,
                                "data_processor_name": 数据处理人名称,
                                "updated_at": 更新时间,
                                "created_at": 创建时间,
                                "business_system_unique_id": 系统唯一ID(API使用此ID),
                                "business_system_unique_pid": 系统父级唯一ID,
                                "factory_log_name": 任务名称
                            }
                        ],
                        "total": 总记录数
                    }
                }

        Example:
            >>> # 查询所有业务系统
            >>> result = api.get_list(
            ...     page=1,
            ...     limit=10
            ... )
            >>>
            >>> # 查询指定业务系统
            >>> result = api.get_list(
            ...     page=1,
            ...     limit=10,
            ...     business_system_unique_id="system-6"
            ... )
            >>>
            >>> # 按名称模糊搜索
            >>> result = api.get_list(
            ...     page=1,
            ...     limit=10,
            ...     business_system_name="核心交易"
            ... )
            >>>
            >>> # 查询运行中的系统
            >>> result = api.get_list(
            ...     page=1,
            ...     limit=10,
            ...     business_system_status="active"
            ... )
            >>>
            >>> # 访问结果
            >>> systems = result['data']['list']
            >>> total = result['data']['total']
        """
        # 构建请求数据
        request_data: Dict[str, Any] = {
            "page": page,
            "limit": limit,
            "business_system_unique_id": business_system_unique_id if business_system_unique_id else ""
        }

        # 添加可选的查询条件
        if business_system_name is not None:
            request_data["business_system_name"] = business_system_name
        if business_system_status is not None:
            request_data["business_system_status"] = business_system_status

        # 发送POST请求查询
        response = self.client.post('/api/business_system/list', data=request_data)
        return response

    def update(
            self,
            business_system_data: List[Dict[str, Any]]
        ) -> Dict[str, Any]:
        """
        更新业务系统

        Args:
            business_system_data: 业务系统数据列表（每个元素为一个业务系统字典）

        Returns:
            操作结果
        """
        # 发送请求更新业务系统
        response = self.client.post(
            '/api/business_system/update',
            data=business_system_data
        )
        return response

    def delete_organize(self, businessUniqueId: List[str]) -> Dict[str, Any]:
        """
        删除业务系统的组织关联

        Args:
            organize_id: 组织ID

        Returns:
            操作结果
        """
        data = businessUniqueId
        response = self.client.delete('/api/business_system/delete_organize', data=data)
        return response

    def get_info_by_repeat_id(self, repeat_id: str) -> Dict[str, Any]:
        """根据重复ID获取系统信息"""
        data = {"repeat_id": repeat_id}
        response = self.client.post('/api/business_system/temporary_business_system/get_info_by_repeat_id', data=data)
        return response
