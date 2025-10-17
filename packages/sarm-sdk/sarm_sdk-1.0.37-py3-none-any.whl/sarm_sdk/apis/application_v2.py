#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
SARM SDK 应用 API V2版本

提供应用相关的API操作，V2版本已移除所有数据校验逻辑，提供更快的数据处理性能。
"""

from typing import List, Dict, Any, Optional, TYPE_CHECKING
from ..models.response import BatchOperationResult

if TYPE_CHECKING:
    from ..client_v2 import SARMClientV2


class ApplicationAPI:
    """应用API类 V2版本 - 已移除数据校验"""

    def __init__(self, client: 'SARMClientV2'):
        self.client = client

    def create_batch(
        self,
        applications: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        批量创建应用

        Args:
            applications: 应用数据列表,每个元素格式如下:
                {
                    "application": {
                        "application_name": "应用名称",
                        "application_desc": "应用描述",
                        "application_version": "应用版本",
                        "application_status": "应用状态(active|maintenance|retired)",
                        "source": "来源标识",
                        "application_original_id": "应用原始id",
                        "application_level_desc": "系统重要性等级（如金/银/铜牌、重保）",
                        "develop_mode": "开发模式（采购/联合/自主）",
                        "cooperate_comp": "合作开发公司名称（仅联合开发或采购时填写）"
                    },
                    "business_system_unique_id": "业务系统唯一ID",
                    "organize_user_unique_id": "组织用户唯一ID"
                }

        Returns:
            Dict[str, Any]: 批量操作结果

        Example:
            >>> # 示例1: 批量创建多个应用(完整字段)
            >>> applications = [
            ...     {
            ...         "application": {
            ...             "application_name": "用户管理服务",
            ...             "application_desc": "负责用户注册、登录、权限管理",
            ...             "application_version": "v1.0.0",
            ...             "application_status": "active",
            ...             "source": "manual",
            ...             "application_original_id": "app_001",
            ...             "application_level_desc": "金牌",
            ...             "develop_mode": "自主",
            ...             "cooperate_comp": ""
            ...         },
            ...         "business_system_unique_id": "bs_001",
            ...         "organize_user_unique_id": "user_001"
            ...     },
            ...     {
            ...         "application": {
            ...             "application_name": "订单管理服务",
            ...             "application_desc": "订单创建、支付、查询功能",
            ...             "application_version": "v2.1.0",
            ...             "application_status": "active",
            ...             "source": "manual",
            ...             "develop_mode": "联合",
            ...             "cooperate_comp": "XX科技公司"
            ...         },
            ...         "business_system_unique_id": "bs_002",
            ...         "organize_user_unique_id": "user_002"
            ...     }
            ... ]
            >>> result = api.create_batch(applications)
            >>>
            >>> # 示例2: 只传入部分字段
            >>> applications = [{
            ...     "application": {
            ...         "application_name": "简单应用",
            ...         "application_status": "active",
            ...         "source": "import"
            ...     },
            ...     "business_system_unique_id": "bs_003"
            ... }]
            >>> result = api.create_batch(applications)
        """
        # 发送请求
        response = self.client.post(
            '/api/application/temporary_application/create',
            data=applications
        )
        return response

    def create(
        self,
        application_name: Optional[str] = None,
        application_desc: Optional[str] = None,
        application_version: Optional[str] = None,
        application_status: Optional[str] = None,
        source: Optional[str] = None,
        application_original_id: Optional[str] = None,
        application_level_desc: Optional[str] = None,
        develop_mode: Optional[str] = None,
        cooperate_comp: Optional[str] = None,
        business_system_unique_id: Optional[str] = None,
        organize_user_unique_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        创建单个应用

        Args:
            application_name: 应用名称
            application_desc: 应用描述
            application_version: 应用版本
            application_status: 应用状态(active|maintenance|retired)
            source: 来源标识
            application_original_id: 应用原始id
            application_level_desc: 系统重要性等级（如金/银/铜牌、重保）
            develop_mode: 开发模式（采购/联合/自主）
            cooperate_comp: 合作开发公司名称（仅联合开发或采购时填写）
            business_system_unique_id: 业务系统唯一ID
            organize_user_unique_id: 组织用户唯一ID

        Returns:
            Dict[str, Any]: 操作结果

        Example:
            >>> # 示例1: 创建完整应用信息
            >>> result = api.create(
            ...     application_name="用户管理服务",
            ...     application_desc="负责用户注册、登录、权限管理",
            ...     application_version="v1.0.0",
            ...     application_status="active",
            ...     source="manual",
            ...     application_original_id="app_001",
            ...     application_level_desc="金牌",
            ...     develop_mode="自主",
            ...     cooperate_comp="",
            ...     business_system_unique_id="bs_001",
            ...     organize_user_unique_id="user_001"
            ... )
            >>>
            >>> # 示例2: 只传入部分字段
            >>> result = api.create(
            ...     application_name="简单应用",
            ...     application_status="active",
            ...     source="import",
            ...     business_system_unique_id="bs_003"
            ... )
            >>>
            >>> # 示例3: 采购模式应用
            >>> result = api.create(
            ...     application_name="采购系统",
            ...     application_status="active",
            ...     source="procurement",
            ...     develop_mode="采购",
            ...     cooperate_comp="XX软件公司",
            ...     application_level_desc="银牌"
            ... )
        """
        # 构建应用数据，只添加用户传入的字段
        application_data = {}

        if application_name is not None:
            application_data["application_name"] = application_name
        if application_desc is not None:
            application_data["application_desc"] = application_desc
        if application_version is not None:
            application_data["application_version"] = application_version
        if application_status is not None:
            application_data["application_status"] = application_status
        if source is not None:
            application_data["source"] = source
        if application_original_id is not None:
            application_data["application_original_id"] = application_original_id
        if application_level_desc is not None:
            application_data["application_level_desc"] = application_level_desc
        if develop_mode is not None:
            application_data["develop_mode"] = develop_mode
        if cooperate_comp is not None:
            application_data["cooperate_comp"] = cooperate_comp

        # 构建完整请求数据
        request_data = {
            "application": application_data
        }

        # 添加关联信息
        if business_system_unique_id is not None:
            request_data["business_system_unique_id"] = business_system_unique_id
        if organize_user_unique_id is not None:
            request_data["organize_user_unique_id"] = organize_user_unique_id

        return self.create_batch([request_data])

    def delete_batch(self, app_ids: List[str]):
        """
        批量删除应用

        Args:
            app_ids: 应用ID列表

        Returns:
            批量操作结果
        """
        data = {"app_id_list": app_ids}
        response = self.client.delete('/api/application/delete', data=data)
        return response

    def delete(self, app_id: str) -> BatchOperationResult:
        """
        删除单个应用

        Args:
            app_id: 应用ID

        Returns:
            操作结果
        """
        return self.delete_batch([app_id])

    def get_list(
        self,
        page: int,
        limit: int,
        application_name: Optional[str] = None,
        application_status: Optional[str] = None,
        application_unique_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        获取应用列表

        Args:
            page: 页码(必填)
            limit: 每页条数(必填)
            application_name: 应用名称(可选)
            application_status: 应用状态(可选)
            application_unique_id: 应用唯一ID(可选)

        Returns:
            Dict[str, Any]: 应用列表响应,格式如下:
                {
                    "code": 200,
                    "data": {
                        "list": [
                            {
                                "application_id": 应用主键,
                                "application_name": 应用名称,
                                "application_status": 应用状态,
                                "application_desc": 应用描述,
                                "application_owner_id": 应用负责人主键,
                                "application_owner_nick_name": 应用负责人昵称,
                                "application_owner_user_name": 应用负责人用户名,
                                "application_owner_unique_id": 应用负责人唯一ID,
                                "organize_user_enterprise_email": 负责人邮箱,
                                "organize_id": 绑定的组织主键,
                                "organize_name": 绑定的组织名称,
                                "organize_unique_id": 绑定的组织唯一ID,
                                "business_system_id": 绑定的系统主键,
                                "business_system_name": 绑定的系统名称,
                                "business_system_unique_id": 绑定的系统唯一ID,
                                "data_processor": 数据处理人主键,
                                "data_processor_name": 数据处理人名称,
                                "created_at": 创建时间,
                                "updated_at": 更新时间,
                                "application_unique_id": 应用唯一ID,
                                "factory_log_name": 任务ID,
                                "application_repeat_id": 应用重复性ID
                            }
                        ],
                        "total": 总记录数
                    }
                }

        Example:
            >>> # 查询所有应用(只传必填参数)
            >>> result = api.get_list(page=1, limit=10)
            >>>
            >>> # 按名称查询
            >>> result = api.get_list(
            ...     page=1,
            ...     limit=10,
            ...     application_name="用户服务"
            ... )
            >>>
            >>> # 按状态查询
            >>> result = api.get_list(
            ...     page=1,
            ...     limit=10,
            ...     application_status="active"
            ... )
            >>>
            >>> # 按应用唯一ID查询
            >>> result = api.get_list(
            ...     page=1,
            ...     limit=10,
            ...     application_unique_id="app_unique_001"
            ... )
            >>>
            >>> # 组合查询
            >>> result = api.get_list(
            ...     page=1,
            ...     limit=20,
            ...     application_name="用户",
            ...     application_status="active"
            ... )
            >>>
            >>> # 访问结果
            >>> applications = result['data']['list']
            >>> total = result['data']['total']
        """
        # 构建请求数据,只包含必填参数
        request_data = {
            "page": page,
            "limit": limit
        }

        # 添加可选参数(只在提供时添加)
        if application_name is not None:
            request_data["application_name"] = application_name
        if application_status is not None:
            request_data["application_status"] = application_status
        if application_unique_id is not None:
            request_data["application_unique_id"] = application_unique_id

        # 发送POST请求
        response = self.client.post('/api/application/list', data=request_data)
        return response

    def update(
        self,
        application_data: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        更新应用

        Args:
            application_data: 应用数据，格式为 {"application": {...}}

        Returns:
            操作结果
        """
        response = self.client.post(
            '/api/application/update',
            data=application_data
        )
        return response

    def delete_business_system(self, app_name: List[str]) -> Dict[str, Any]:
        """删除应用的业务系统关联"""
        data = app_name
        response = self.client.delete('/api/application/delete_business_system', data=data)
        return response

    def get_info_by_repeat_id(self, repeat_id: str) -> Dict[str, Any]:
        """根据重复ID获取应用信息"""
        data = {"repeat_id": repeat_id}
        response = self.client.post('/api/application/temporary_application/get_info_by_repeat_id', data=data)
        return response
