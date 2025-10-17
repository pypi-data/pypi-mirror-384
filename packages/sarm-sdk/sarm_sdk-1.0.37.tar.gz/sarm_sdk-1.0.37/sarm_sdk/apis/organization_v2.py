#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
SARM SDK 组织架构 API V2 - 无数据校验版本

提供组织架构相关的API操作，包括创建、查询、更新、删除等功能。
此版本移除了所有客户端数据校验逻辑。
"""

from typing import List, Dict, Any, Optional, TYPE_CHECKING
from ..models.organization import OrganizationTree, OrganizeUser
from ..models.response import BatchOperationResult

if TYPE_CHECKING:
    from ..client_v2 import SARMClientV2


class OrganizationAPI:
    """组织架构API类 V2"""

    def __init__(self, client: 'SARMClientV2'):
        self.client = client

    def create_batch(
        self,
        organizations: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        批量创建组织(预审)

        Args:
            organizations: 组织数据列表，每个元素为字典格式，可包含：
                - organize_name: 部门名称 (可选)
                - organize_owner_unique_id: 部门负责人(正式数据组织人员的唯一ID) (可选)
                - source: 来源 (可选)
                - organize_original_id: 部门原始id (可选)
                - desc: 备注 (可选)
                - parent_organize_original_id: 父节点原始id (可选)

        Returns:
            Dict[str, Any]: API响应，格式为：
            {
                "data": "success",
                "code": 200
            }

        Example:
            >>> organizations = [{
            ...     "organize_name": "技术部",
            ...     "organize_owner_unique_id": "user_001",
            ...     "source": "api",
            ...     "organize_original_id": "tech_dept_001",
            ...     "desc": "技术研发部门",
            ...     "parent_organize_original_id": ""
            ... }]
            >>> result = api.create_batch(organizations)
        """
        response = self.client.post(
            '/api/v2/temporary_organize/create_edit',
            data={"organizations": organizations}
        )
        return response

    def create(
        self,
        organize_name: Optional[str] = None,
        organize_owner_unique_id: Optional[str] = None,
        source: Optional[str] = None,
        organize_original_id: Optional[str] = None,
        desc: Optional[str] = None,
        parent_organize_original_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        创建单个组织(预审)

        Args:
            organize_name: 部门名称 (可选)
            organize_owner_unique_id: 部门负责人(正式数据组织人员的唯一ID) (可选)
            source: 来源 (可选)
            organize_original_id: 部门原始id (可选)
            desc: 备注 (可选)
            parent_organize_original_id: 父节点原始id (可选)

        Returns:
            Dict[str, Any]: API响应

        Example:
            >>> result = api.create(
            ...     organize_name="技术部",
            ...     organize_owner_unique_id="user_001",
            ...     source="api",
            ...     organize_original_id="tech_dept_001"
            ... )
        """
        organization = {}
        if organize_name is not None:
            organization["organize_name"] = organize_name
        if organize_owner_unique_id is not None:
            organization["organize_owner_unique_id"] = organize_owner_unique_id
        if source is not None:
            organization["source"] = source
        if organize_original_id is not None:
            organization["organize_original_id"] = organize_original_id
        if desc is not None:
            organization["desc"] = desc
        if parent_organize_original_id is not None:
            organization["parent_organize_original_id"] = parent_organize_original_id

        return self.create_batch([organization])

    def update_batch(
        self,
        organizations: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        批量更新组织(预审)

        注：更新操作与创建操作使用相同的API端点

        Args:
            organizations: 组织数据列表，每个元素为字典格式，可包含：
                - organize_name: 部门名称 (可选)
                - organize_owner_unique_id: 部门负责人(正式数据组织人员的唯一ID) (可选)
                - source: 来源 (可选)
                - organize_original_id: 部门原始id (可选)
                - desc: 备注 (可选)
                - parent_organize_original_id: 父节点原始id (可选)

        Returns:
            Dict[str, Any]: API响应
        """
        response = self.client.post(
            '/api/v2/temporary_organize/create_edit',
            data={"organizations": organizations}
        )
        return response

    def update(
        self,
        organize_name: Optional[str] = None,
        organize_owner_unique_id: Optional[str] = None,
        source: Optional[str] = None,
        organize_original_id: Optional[str] = None,
        desc: Optional[str] = None,
        parent_organize_original_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        更新单个组织(预审)

        Args:
            organize_name: 部门名称 (可选)
            organize_owner_unique_id: 部门负责人(正式数据组织人员的唯一ID) (可选)
            source: 来源 (可选)
            organize_original_id: 部门原始id (可选)
            desc: 备注 (可选)
            parent_organize_original_id: 父节点原始id (可选)

        Returns:
            Dict[str, Any]: API响应
        """
        organization = {}
        if organize_name is not None:
            organization["organize_name"] = organize_name
        if organize_owner_unique_id is not None:
            organization["organize_owner_unique_id"] = organize_owner_unique_id
        if source is not None:
            organization["source"] = source
        if organize_original_id is not None:
            organization["organize_original_id"] = organize_original_id
        if desc is not None:
            organization["desc"] = desc
        if parent_organize_original_id is not None:
            organization["parent_organize_original_id"] = parent_organize_original_id

        return self.update_batch([organization])



    def delete_batch(self, unique_ids: List[str]) -> Dict[str, Any]:
        """
        批量删除组织

        Args:
            unique_ids: 组织唯一ID列表

        Returns:
            删除结果

        Note:
            当层及下级存在关联数据时不允许删除
        """
        response = self.client.post(
            '/api/organize/openapi/delete',
            data=unique_ids
        )

        return response

    def delete(self, unique_id: str) -> Dict[str, Any]:
        """
        删除单个组织

        Args:
            unique_id: 组织唯一ID

        Returns:
            删除结果
        """
        return self.delete_batch([unique_id])

    def get_list(
        self,
        page: int = 1,
        size: int = 10,
        organize_name: Optional[str] = None,
        data_status: Optional[str] = None,
        analyze_status: Optional[str] = None,
        sort_field: str = "created_at",
        sort_order: str = "desc"
    ) -> Dict[str, Any]:
        """
        查询组织架构列表(预审)

        Args:
            page: 页码 (可选，默认1)
            size: 每页数量 (可选，默认10)
            organize_name: 部门名称，模糊查询 (可选)
            data_status: 数据发布状态 (可选)，可选值：
                - "published": 已发布
                - "perfect": 待发布
                - "imperfect": 待完善
                - "wait_confirm": 待确认
                - "intelligent_association": 智能关联中
                - "wait_associated": 待关联
            analyze_status: 数据推理状态 (可选)，可选值：
                - "wait": 待分析
                - "process": 分析中
                - "finish": 分析完成
                - "fail": 分析失败
            sort_field: 排序字段 (可选，默认"created_at")
            sort_order: 排序类型 (可选，默认"desc")

        Returns:
            Dict[str, Any]: API响应，格式为：
            {
                "data": {
                    "total": int,  # 总记录数
                    "data": [      # 组织列表
                        {
                            "temporary_organize_id": int,           # 预审组织ID
                            "organize_name": str,                   # 组织名称
                            "parent_organize_name": str,            # 父组织名称
                            "temporary_organize_pid": int,          # 父组织ID
                            "organize_temporary_owner_id": int,     # 负责人ID
                            "organize_owner_name": str,             # 负责人姓名
                            "data_status": str,                     # 数据状态
                            "analyze_status": str,                  # 分析状态
                            "data_processor_name": str,             # 数据处理人名称
                            "data_processor": int,                  # 数据处理人ID
                            "created_at": str,                      # 创建时间
                            "updated_at": str,                      # 更新时间
                            "source": str,                          # 来源
                            "organize_repeat_id": str,              # 组织重复ID
                            "organize_original_id": str,            # 组织原始ID
                            "desc": str,                            # 描述
                            "factory_log_id": int,                  # 工厂日志ID
                            "factory_log_name": str                 # 工厂日志名称
                        }
                    ]
                },
                "code": int  # 响应状态码
            }

        Example:
            >>> # 查询所有组织
            >>> result = api.get_list(page=1, size=10)
            >>>
            >>> # 按名称搜索
            >>> result = api.get_list(
            ...     page=1,
            ...     size=10,
            ...     organize_name="技术部"
            ... )
            >>>
            >>> # 按状态查询
            >>> result = api.get_list(
            ...     page=1,
            ...     size=10,
            ...     data_status="perfect",
            ...     analyze_status="finish"
            ... )
        """
        query_data = {
            "page": page,
            "size": size,
            "sort_field": sort_field,
            "sort_order": sort_order
        }

        if organize_name is not None:
            query_data["organize_name"] = organize_name
        if data_status is not None:
            query_data["data_status"] = data_status
        if analyze_status is not None:
            query_data["analyze_status"] = analyze_status

        response = self.client.post('/api/v2/temporary_organize/list', data=query_data)
        return response

    def refresh_cache(self) -> Dict[str, Any]:
        """
        刷新组织架构树缓存

        这是一个异步操作，用于在批量导入组织数据后刷新组织架构树缓存，
        确保组织层级关系的数据一致性。

        Returns:
            操作结果

        Note:
            - 这是异步操作，调用成功仅表示任务已提交
            - 建议在批量导入组织后调用此方法
            - 大量组织数据的缓存刷新可能需要一定时间
        """
        response = self.client.get('/api/organize/async_refresh_organize_tree_cache')
        return response

    def get_tree(self):
        """
        获取组织架构树

        Returns:
            组织架构树列表

        Note:
            如果组织架构缓存未更新，建议先调用 refresh_cache() 方法
        """
        # 获取所有组织
        all_orgs = []
        page = 1
        limit = 100

        while True:
            response = self.get(page=page, limit=limit)
            data_list = response.get('data', {}).get('data_list', [])

            if not data_list:
                break

            all_orgs.extend(data_list)

            # 检查是否还有更多数据
            total = response.get('data', {}).get('total', 0)
            if len(all_orgs) >= total:
                break

            page += 1

        # 构建组织树
        return self._build_organization_tree(all_orgs)

    def _build_organization_tree(self, organizations: List[Dict[str, Any]]):
        """
        构建组织架构树

        Args:
            organizations: 组织数据列表

        Returns:
            组织架构树列表
        """
        # 创建组织字典，便于查找
        org_dict = {org['organize_uuid']: org for org in organizations}

        # 查找根节点（父ID为'0'或None的组织）
        roots = []

        for org in organizations:
            parent_id = org.get('organize_puuid')
            if parent_id == '0' or parent_id is None:
                tree_node = OrganizationTree(
                    organize_unique_id=org['organize_uuid'],
                    organize_name=org['organize_name'],
                    level=0,
                    children=[]
                )
                self._build_children(tree_node, org_dict, 1)
                roots.append(tree_node)

        return roots

    def _build_children(
        self,
        parent_node: OrganizationTree,
        org_dict: Dict[str, Dict[str, Any]],
        level: int
    ):
        """
        递归构建子组织节点

        Args:
            parent_node: 父节点
            org_dict: 组织字典
            level: 当前层级
        """
        parent_id = parent_node.organize_unique_id

        for org_id, org in org_dict.items():
            if org.get('organize_puuid') == parent_id:
                child_node = OrganizationTree(
                    organize_unique_id=org['organize_uuid'],
                    organize_name=org['organize_name'],
                    level=level,
                    children=[]
                )
                self._build_children(child_node, org_dict, level + 1)
                parent_node.children.append(child_node)

    # 用户管理相关方法
    def create_users(
        self,
        organize_unique_id: str,
        users: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        批量创建组织用户

        Args:
            organize_unique_id: 组织唯一ID
            users: 用户数据列表

        Returns:
            创建结果
        """
        user_data = []
        for user in users:
            if isinstance(user, OrganizeUser):
                user_data.append(user.dict())
            else:
                user_data.append(user)

        request_data = {
            "organize_unique_id": organize_unique_id,
            "user_list": user_data
        }

        response = self.client.post('/api/organize_user/create', data=request_data)
        return response

    def update_users(self, users: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        批量更新组织用户

        Args:
            users: 用户数据列表

        Returns:
            更新结果
        """
        response = self.client.post('/api/organize_user/update', data=users)
        return response

    def delete_users(self, user_unique_ids: List[str]) -> Dict[str, Any]:
        """
        批量删除组织用户

        Args:
            user_unique_ids: 用户唯一ID列表

        Returns:
            删除结果
        """
        response = self.client.post('/api/organize_user/delete', data=user_unique_ids)
        return response

    def delete_parent_id(self, organize_id: List[str]) -> Dict[str, Any]:
        """
        删除组织的父级ID关联

        Args:
            organize_id: 组织ID列表

        Returns:
            操作结果
        """
        response = self.client.post('/api/organize/openapi/delete_pid', data=organize_id)
        return response

    def delete_leader(self, organize_id: List[str]) -> Dict[str, Any]:
        """
        删除组织的负责人关联

        Args:
            organize_id: 组织ID列表

        Returns:
            操作结果
        """
        response = self.client.post('/api/organize/openapi/delete_leader', data=organize_id)
        return response

    def get_users(
        self,
        organize_unique_id: str,
        user_unique_id: Optional[str] = None,
        user_name: Optional[str] = None,
        enterprise_email: Optional[str] = None,
        page: int = 1,
        limit: int = 50
    ) -> Dict[str, Any]:
        """
        查询组织用户列表

        Args:
            organize_unique_id: 组织唯一ID
            user_unique_id: 用户唯一ID
            user_name: 用户名
            enterprise_email: 企业邮箱
            page: 页码
            limit: 每页数量

        Returns:
            用户列表和分页信息
        """
        user_info = {}
        if user_unique_id:
            user_info["organize_user_unique_id"] = user_unique_id
        if user_name:
            user_info["organize_user_name"] = user_name
        if enterprise_email:
            user_info["organize_user_enterprise_email"] = enterprise_email

        query_data = {
            "organize_unique_id": organize_unique_id,
            "user_info": user_info,
            "page": page,
            "limit": limit
        }

        response = self.client.post('/api/organize_user/list', data=query_data)
        return response
