#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
SARM SDK 组织用户 API V2版本

提供组织用户相关的API操作，V2版本已移除所有数据校验逻辑，提供更快的数据处理性能。
"""

from typing import List, Dict, Any, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from ..client_v2 import SARMClientV2


class OrganizeUserAPI:
    """组织用户API类 V2版本 - 已移除数据校验"""

    def __init__(self, client: 'SARMClientV2'):
        self.client = client

    @staticmethod
    def _build_user_data(**kwargs) -> Dict[str, Any]:
        """
        构建用户数据字典，自动过滤None值

        Args:
            **kwargs: 用户数据字段

        Returns:
            过滤后的用户数据字典
        """
        return {k: v for k, v in kwargs.items() if v is not None}

    def create_batch(
            self,
            users: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        批量创建组织用户

        Args:
            users: 用户数据列表，每个用户包含:
                - organize_user_name: 用户名 (可选)
                - organize_user_nick_name: 用户昵称 (可选)
                - organize_user_enterprise_email: 邮箱 (可选)
                - organize_user_mobile: 手机号，整数类型 (可选)
                - source: 来源 (可选)
                - organize_user_original_id: 用户原始id (可选)
                - organize_user_job_title: 职务 (可选)
                - organize_user_avatar: 组织用户的头像地址 (可选)
                - organize_user_employee_no: 组织用户工号 (可选)
                - organize_unique_id_list: 正式部门唯一id (可选)

        Returns:
            操作结果
        """
        return self.client.post(
            '/api/v2/temporary_organize_user/create_edit',
            data={"users": users}
        )

    def create(
            self,
            organize_user_name: Optional[str] = None,
            organize_user_nick_name: Optional[str] = None,
            organize_user_enterprise_email: Optional[str] = None,
            organize_user_mobile: Optional[int] = None,
            source: Optional[str] = None,
            organize_user_original_id: Optional[str] = None,
            organize_user_job_title: Optional[str] = None,
            organize_user_avatar: Optional[str] = None,
            organize_user_employee_no: Optional[str] = None,
            organize_unique_id_list: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        创建单个组织用户

        Args:
            organize_user_name: 用户名 (可选)
            organize_user_nick_name: 用户昵称 (可选)
            organize_user_enterprise_email: 邮箱 (可选)
            organize_user_mobile: 手机号 (可选，整数类型)
            source: 来源 (可选)
            organize_user_original_id: 用户原始id (可选)
            organize_user_job_title: 职务 (可选)
            organize_user_avatar: 组织用户的头像地址 (可选)
            organize_user_employee_no: 组织用户工号 (可选)
            organize_unique_id_list: 正式部门唯一id列表 (可选)

        Returns:
            操作结果
        """
        user_data = self._build_user_data(
            organize_user_name=organize_user_name,
            organize_user_nick_name=organize_user_nick_name,
            organize_user_enterprise_email=organize_user_enterprise_email,
            organize_user_mobile=organize_user_mobile,
            source=source,
            organize_user_original_id=organize_user_original_id,
            organize_user_job_title=organize_user_job_title,
            organize_user_avatar=organize_user_avatar,
            organize_user_employee_no=organize_user_employee_no,
            organize_unique_id_list=organize_unique_id_list
        )

        return self.create_batch([user_data])

    def delete_batch(self, user_ids: List[str]) -> Dict[str, Any]:
        """
        批量删除组织用户

        Args:
            user_ids: 用户唯一ID列表

        Returns:
            操作结果
        """
        return self.client.post('/api/organize_user/delete', data=user_ids)

    def delete(self, user_id: str) -> Dict[str, Any]:
        """删除单个组织用户"""
        return self.delete_batch([user_id])

    def _get_list_base(
            self,
            api_path: str,
            user_name_or_email: str = "",
            data_status: Optional[str] = None,
            analyze_status: Optional[str] = None,
            page: int = 1,
            size: int = 10,
            sort_field: str = "created_at",
            sort_order: str = "desc"
    ) -> Dict[str, Any]:
        """
        获取列表的基础方法

        Args:
            api_path: API路径
            user_name_or_email: 用户名和邮箱
            data_status: 数据发布状态
            analyze_status: 数据推理状态
            page: 页码
            size: 每页条数
            sort_field: 排序字段
            sort_order: 排序方式

        Returns:
            响应数据
        """
        data = {
            "user_name_or_email": user_name_or_email,
            "page": page,
            "size": size,
            "sort_field": sort_field,
            "sort_order": sort_order
        }

        if data_status is not None:
            data["data_status"] = data_status
        if analyze_status is not None:
            data["analyze_status"] = analyze_status

        return self.client.post(api_path, data=data)

    def get_list(
            self,
            user_name_or_email: str = "",
            data_status: Optional[str] = None,
            analyze_status: Optional[str] = None,
            page: int = 1,
            size: int = 10,
            sort_field: str = "created_at",
            sort_order: str = "desc"
    ) -> Dict[str, Any]:
        """
        获取组织用户列表（预审数据）

        API路径: POST /api/v2/temporary_organize_user/list

        Args:
            user_name_or_email: 用户名和邮箱 (可选，默认空字符串)
            data_status: 数据发布状态 (可选)
                - "published": 已发布
                - "perfect": 待发布
                - "imperfect": 待完善
                - "wait_confirm": 待确认
                - "intelligent_association": 智能关联中
                - "wait_associated": 待关联
            analyze_status: 数据推理状态 (可选)
                - "wait": 等待
                - "process": 处理中
                - "finish": 完成
                - "fail": 失败
            page: 页码，默认为1
            size: 每页条数，默认为10
            sort_field: 排序字段，默认为"created_at"
            sort_order: 排序方式，默认为"desc" (desc/asc)

        Returns:
            Dict[str, Any]: 响应数据，格式如下：
            {
                "data": {
                    "total": int,  # 总记录数
                    "data": [      # 用户列表
                        {
                            "temporary_organize_user_id": int,         # 预审组织用户ID
                            "organize_user_name": str,                 # 用户名
                            "organize_nick_name": str,                 # 用户昵称
                            "organize_user_enterprise_email": str,     # 企业邮箱
                            "factory_log_id": int,                     # 工厂日志ID
                            "factory_log_name": str,                   # 工厂日志名称
                            "data_status": str,                        # 数据状态
                            "analyze_status": str,                     # 分析状态
                            "data_processor_name": str,                # 数据处理人名称
                            "data_processor": int,                     # 数据处理人ID
                            "created_at": str,                         # 创建时间
                            "updated_at": str,                         # 更新时间
                            "organize_user_repeat_id": str,            # 用户重复ID
                            "source": str,                             # 来源
                            "organize_user_original_id": str,          # 用户原始ID
                            "organize_user_employee_no": str,          # 员工编号
                            "organize_name": str,                      # 组织名称
                            "temporary_organize_id": int               # 预审组织ID
                        }
                    ]
                },
                "code": int  # 响应状态码
            }
        """
        return self._get_list_base(
            '/api/v2/temporary_organize_user/list',
            user_name_or_email=user_name_or_email,
            data_status=data_status,
            analyze_status=analyze_status,
            page=page,
            size=size,
            sort_field=sort_field,
            sort_order=sort_order
        )

    def get_temporary_list(
            self,
            user_name_or_email: str = "",
            data_status: Optional[str] = None,
            analyze_status: Optional[str] = None,
            page: int = 1,
            size: int = 10,
            sort_field: str = "created_at",
            sort_order: str = "desc"
    ) -> Dict[str, Any]:
        """
        获取组织用户预审列表（get_list的别名，更明确的方法名）

        参数和返回值与 get_list 方法相同
        """
        return self.get_list(
            user_name_or_email=user_name_or_email,
            data_status=data_status,
            analyze_status=analyze_status,
            page=page,
            size=size,
            sort_field=sort_field,
            sort_order=sort_order
        )

    def update_batch(self, users: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        批量更新组织用户

        Args:
            users: 用户数据列表

        Returns:
            操作结果
        """
        return self.client.post('/api/organize_user/update', data=users)

    def update(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """更新单个组织用户"""
        return self.update_batch([user_data])

    def get_formal_list(
            self,
            limit: int,
            page: int,
            user_info: Optional[Dict[str, Any]] = None,
            organize_unique_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        获取组织用户列表（正式数据）

        API路径: POST /api/v2/organize_user/list

        Args:
            limit: 每页数量 (必需)
            page: 页码 (必需)
            user_info: 用户信息筛选条件 (可选)，包含以下字段：
                - organize_user_unique_id: 用户唯一id (可选)
                - organize_user_name: 用户名 (可选)
                - organize_user_enterprise_email: 企业邮箱 (可选)
                - organize_user_employee_no: 工号 (可选)
                - organize_user_mobile: 手机号码 (可选)
                - organize_user_job_title: 职务 (可选)
                - organize_nick_name: 用户名称 (可选)
            organize_unique_id: 组织唯一ID (可选)

        Returns:
            Dict[str, Any]: 响应数据，格式如下：
            {
                "data": {
                    "total": int,  # 总记录数
                    "data_list": [  # 用户列表
                        {
                            "organize_user_id": str,                   # 组织用户ID
                            "organize_user_unique_id": str,            # 用户唯一ID
                            "organize_user_name": str,                 # 用户名
                            "organize_nick_name": str,                 # 用户昵称
                            "organize_user_avatar": str,               # 用户头像
                            "organize_user_mobile": str,               # 手机号码（字符串类型）
                            "organize_user_enterprise_email": str,     # 企业邮箱
                            "organize_user_employee_no": str,          # 员工编号
                            "organize_user_job_title": str,            # 职务
                            "created_at": str,                         # 创建时间
                            "updated_at": str,                         # 更新时间
                            "is_manager": int,                         # 是否为管理员
                            "source": str,                             # 来源
                            "status": str,                             # 状态
                            "deleted_at": Any,                         # 删除时间
                            "account_id": str,                         # 账户ID
                            "factory_log_id": int                      # 工厂日志ID
                        }
                    ]
                },
                "code": int  # 响应状态码
            }
        """
        data = {
            "user_info": user_info if user_info is not None else {},
            "limit": limit,
            "page": page
        }

        if organize_unique_id is not None:
            data["organize_unique_id"] = organize_unique_id

        return self.client.post('/api/v2/organize_user/list', data=data)

    def delete_organize_batch(self, organize_user_ids: List[str]) -> Dict[str, Any]:
        """
        批量删除组织用户的组织关联

        Args:
            organize_user_ids: 组织用户ID列表

        Returns:
            操作结果
        """
        return self.client.post('/api/organize_user/delete_organize', data=organize_user_ids)

    def delete_organize(self, organize_user_id: str) -> Dict[str, Any]:
        """
        删除单个组织用户的组织关联

        Args:
            organize_user_id: 组织用户ID

        Returns:
            操作结果
        """
        return self.delete_organize_batch([organize_user_id])
