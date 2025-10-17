#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
SARM SDK 软件成分 API V2版本

提供软件成分相关的API操作，V2版本已移除所有数据校验逻辑，提供更快的数据处理性能。
"""

from typing import List, Dict, Any, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from ..client_v2 import SARMClientV2


class ComponentAPI:
    """软件成分API类 V2版本 - 已移除数据校验"""

    def __init__(self, client: 'SARMClientV2'):
        self.client = client

    def create_batch(
        self,
        components: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        批量创建成分(预审)

        该方法支持:
        1. 成分信息的创建/更新
        2. 创建成分应用关联关系
        3. 创建成分载体关联关系
        4. 创建成分安全能力关联关系

        Args:
            components: 成分数据列表,每个元素格式如下:
                {
                    "component_name": "成分名称(必填)",
                    "component_version": "成分版本(可选)",
                    "status": "状态(可选)",  # active/approved/deprecated/eol
                    "component_desc": "描述(可选)",
                    "asset_category": "大分类(可选)",
                    "asset_type": "子分类(必填)",  # 见文档详细列表
                    "vendor": "供应商(可选)",
                    "ecosystem": "生态(可选)",  # 组件类型特有
                    "repository": "仓库(可选)",  # 组件类型特有
                    "tags": ["标签1", "标签2"],  # 可选
                    "supplier_name": "供应商名称(可选)",
                    "attributes": {},  # 特征字段(可选)
                    "component_unique_id": "成分唯一标识(可选)",
                    "context": [  # 成分上下文(可选)
                        {
                            "name": "名称",
                            "type": "类型",
                            "content": "内容",
                            "description": "描述"
                        }
                    ],
                    "source": "数据来源(必填)",
                    "component_original_id": "成分原始ID(可选)",
                    "application_unique_id_list": ["app_id1"],  # 应用ID列表(可选)
                    "carrier_unique_id_list": [  # 载体ID列表(可选)
                        {
                            "carrier_unique_id": "载体ID",
                            "component_context": [
                                {
                                    "name": "名称",
                                    "type": "类型",
                                    "content": "内容",
                                    "description": "描述"
                                }
                            ]
                        }
                    ],
                    "security_capability_unique_id_list": ["cap_id1"]  # 安全能力ID列表(可选)
                }

        Returns:
            Dict[str, Any]: 批量操作结果

        Note:
            - application_unique_id_list/carrier_unique_id_list/security_capability_unique_id_list
              不传为不操作,如果传了(空列表)就会覆盖原来关联关系

        Example:
            >>> # 示例1: 创建开源组件
            >>> components = [{
            ...     "component_name": "spring-boot",
            ...     "component_version": "2.7.0",
            ...     "status": "active",
            ...     "asset_type": "open_source_component",
            ...     "vendor": "Apache",
            ...     "ecosystem": "java",
            ...     "repository": "maven",
            ...     "source": "manual",
            ...     "application_unique_id_list": ["app_001"],
            ...     "tags": ["java", "framework"]
            ... }]
            >>> result = api.create_batch(components)
            >>>
            >>> # 示例2: 创建自研组件并关联载体
            >>> components = [{
            ...     "component_name": "user-service-lib",
            ...     "component_version": "1.0.0",
            ...     "asset_type": "in_house_developed_component",
            ...     "component_desc": "用户服务公共库",
            ...     "source": "internal",
            ...     "carrier_unique_id_list": [
            ...         {
            ...             "carrier_unique_id": "carrier_001",
            ...             "component_context": [
            ...                 {
            ...                     "name": "依赖关系",
            ...                     "type": "dependency",
            ...                     "content": "直接依赖",
            ...                     "description": "核心依赖库"
            ...                 }
            ...             ]
            ...         }
            ...     ]
            ... }]
            >>> result = api.create_batch(components)
        """
        # 发送请求到V2预审接口
        response = self.client.post(
            '/api/v2/component/temporary/insert',
            data=components
        )
        return response

    def create(
        self,
        component_name: str,
        asset_type: str,
        source: str,
        component_version: Optional[str] = None,
        status: Optional[str] = None,
        component_desc: Optional[str] = None,
        asset_category: Optional[str] = None,
        vendor: Optional[str] = None,
        ecosystem: Optional[str] = None,
        repository: Optional[str] = None,
        tags: Optional[List[str]] = None,
        supplier_name: Optional[str] = None,
        attributes: Optional[Dict[str, Any]] = None,
        component_unique_id: Optional[str] = None,
        context: Optional[List[Dict[str, Any]]] = None,
        component_original_id: Optional[str] = None,
        application_unique_id_list: Optional[List[str]] = None,
        carrier_unique_id_list: Optional[List[Dict[str, Any]]] = None,
        security_capability_unique_id_list: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        创建单个成分(预审)

        Args:
            component_name: 成分名称(必填)
            asset_type: 子分类(必填)
            source: 数据来源(必填)
            component_version: 成分版本(可选)
            status: 状态(可选) - active/approved/deprecated/eol
            component_desc: 描述(可选)
            asset_category: 大分类(可选)
            vendor: 供应商(可选)
            ecosystem: 生态(可选)
            repository: 仓库(可选)
            tags: 标签列表(可选)
            supplier_name: 供应商名称(可选)
            attributes: 特征字段(可选)
            component_unique_id: 成分唯一标识(可选)
            context: 成分上下文列表(可选)
            component_original_id: 成分原始ID(可选)
            application_unique_id_list: 应用唯一ID列表(可选)
            carrier_unique_id_list: 载体唯一ID列表(可选)
            security_capability_unique_id_list: 安全能力唯一ID列表(可选)

        Returns:
            Dict[str, Any]: 操作结果

        Example:
            >>> # 示例1: 创建开源组件
            >>> result = api.create(
            ...     component_name="spring-boot",
            ...     component_version="2.7.0",
            ...     asset_type="open_source_component",
            ...     source="manual",
            ...     status="active",
            ...     vendor="Apache",
            ...     ecosystem="java",
            ...     repository="maven",
            ...     tags=["java", "framework"],
            ...     application_unique_id_list=["app_001"]
            ... )
            >>>
            >>> # 示例2: 最小化创建
            >>> result = api.create(
            ...     component_name="my-lib",
            ...     asset_type="in_house_developed_component",
            ...     source="internal"
            ... )
        """
        # 构建成分数据
        component_data = {
            "component_name": component_name,
            "asset_type": asset_type,
            "source": source
        }

        # 添加可选字段
        if component_version:
            component_data["component_version"] = component_version
        if status:
            component_data["status"] = status
        if component_desc:
            component_data["component_desc"] = component_desc
        if asset_category:
            component_data["asset_category"] = asset_category
        if vendor:
            component_data["vendor"] = vendor
        if ecosystem:
            component_data["ecosystem"] = ecosystem
        if repository:
            component_data["repository"] = repository
        if tags:
            component_data["tags"] = tags
        if supplier_name:
            component_data["supplier_name"] = supplier_name
        if attributes:
            component_data["attributes"] = attributes
        if component_unique_id:
            component_data["component_unique_id"] = component_unique_id
        if context:
            component_data["context"] = context
        if component_original_id:
            component_data["component_original_id"] = component_original_id
        if application_unique_id_list is not None:
            component_data["application_unique_id_list"] = application_unique_id_list
        if carrier_unique_id_list is not None:
            component_data["carrier_unique_id_list"] = carrier_unique_id_list
        if security_capability_unique_id_list is not None:
            component_data["security_capability_unique_id_list"] = security_capability_unique_id_list

        return self.create_batch([component_data])

    def get_list_temporary(
        self,
        page: int,
        limit: int,
        component_name: Optional[str] = None,
        asset_type: Optional[str] = None,
        status: Optional[str] = None,
        guess_status: Optional[str] = None,
        data_status: Optional[str] = None,
        component_unique_id: Optional[str] = None,
        component_repeat_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        获取成分列表(预审)

        查询处于预审状态的成分数据。

        Args:
            page: 页码(必填)
            limit: 每页条数(必填)
            component_name: 成分名称(可选,支持模糊搜索)
            asset_type: 成分子分类(可选), 见文档asset_type列表
            status: 状态(可选), 可选值:
                - active: 活跃
                - approved: 已批准
                - deprecated: 已弃用
                - eol: 终止支持
            guess_status: 推测状态(可选), 可选值:
                - wait: 待分析
                - process: 分析中
                - finish: 分析完成
                - fail: 分析失败
            data_status: 数据状态(可选), 可选值:
                - imperfect: 待完善
                - wait_confirm: 待确认
                - perfect: 待发布
            component_unique_id: 成分唯一ID(可选)
            component_repeat_id: 成分重复性标识(可选)

        Returns:
            Dict[str, Any]: 预审成分列表响应

        Example:
            >>> # 查询所有预审成分
            >>> result = api.get_list_temporary(page=1, limit=10)
            >>>
            >>> # 按名称搜索
            >>> result = api.get_list_temporary(
            ...     page=1,
            ...     limit=10,
            ...     component_name="spring"
            ... )
            >>>
            >>> # 按类型和状态查询
            >>> result = api.get_list_temporary(
            ...     page=1,
            ...     limit=10,
            ...     asset_type="open_source_component",
            ...     status="active"
            ... )
            >>>
            >>> # 访问结果
            >>> components = result['data']['data_list']
            >>> total = result['data']['total']
        """
        # 构建请求数据
        request_data: Dict[str, Any] = {
            "page": page,
            "limit": limit
        }

        # 添加可选查询条件
        if component_name:
            request_data["component_name"] = component_name
        if asset_type:
            request_data["asset_type"] = asset_type
        if status:
            request_data["status"] = status
        if guess_status:
            request_data["guess_status"] = guess_status
        if data_status:
            request_data["data_status"] = data_status
        if component_unique_id:
            request_data["component_unique_id"] = component_unique_id
        if component_repeat_id:
            request_data["component_repeat_id"] = component_repeat_id

        # 发送POST请求查询预审成分
        response = self.client.post('/api/v2/component/temporary/get_list', data=request_data)
        return response

    def get_list_formal(
        self,
        page: int,
        limit: int,
        component_name: Optional[str] = None,
        asset_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        获取成分列表(正式)

        查询已发布的正式成分数据。

        Args:
            page: 页码(必填)
            limit: 每页条数(必填)
            component_name: 成分名称(可选,支持模糊搜索)
            asset_type: 成分类型(可选), 见文档asset_type列表

        Returns:
            Dict[str, Any]: 正式成分列表响应

        Example:
            >>> # 查询所有正式成分
            >>> result = api.get_list_formal(page=1, limit=10)
            >>>
            >>> # 按名称搜索
            >>> result = api.get_list_formal(
            ...     page=1,
            ...     limit=10,
            ...     component_name="mysql"
            ... )
            >>>
            >>> # 按类型查询
            >>> result = api.get_list_formal(
            ...     page=1,
            ...     limit=10,
            ...     asset_type="database"
            ... )
            >>>
            >>> # 组合查询
            >>> result = api.get_list_formal(
            ...     page=1,
            ...     limit=20,
            ...     component_name="spring",
            ...     asset_type="open_source_component"
            ... )
            >>>
            >>> # 访问结果
            >>> components = result['data']['data_list']
            >>> total = result['data']['total']
        """
        # 构建请求数据
        request_data: Dict[str, Any] = {
            "page": page,
            "limit": limit
        }

        # 添加可选查询条件
        if component_name:
            request_data["component_name"] = component_name
        if asset_type:
            request_data["asset_type"] = asset_type

        # 发送POST请求查询正式成分
        response = self.client.post('/api/v2/component/formal/get_list', data=request_data)
        return response

    def get_list(
        self,
        page: int,
        limit: int,
        component_name: Optional[str] = None,
        asset_type: Optional[str] = None,
        formal: bool = True,
        **kwargs
    ) -> Dict[str, Any]:
        """
        获取成分列表(统一入口)

        统一的成分列表查询方法,可通过formal参数切换查询预审或正式数据。

        Args:
            page: 页码(必填)
            limit: 每页条数(必填)
            component_name: 成分名称(可选,支持模糊搜索)
            asset_type: 成分类型(可选)
            formal: 是否查询正式数据(默认True), False则查询预审数据
            **kwargs: 预审模式额外参数(status, guess_status, data_status等)

        Returns:
            Dict[str, Any]: 成分列表响应

        Example:
            >>> # 查询正式成分(默认)
            >>> result = api.get_list(page=1, limit=10)
            >>>
            >>> # 查询预审成分
            >>> result = api.get_list(page=1, limit=10, formal=False)
            >>>
            >>> # 查询预审成分并指定状态
            >>> result = api.get_list(
            ...     page=1,
            ...     limit=10,
            ...     formal=False,
            ...     status="active",
            ...     data_status="imperfect"
            ... )
        """
        if formal:
            return self.get_list_formal(
                page=page,
                limit=limit,
                component_name=component_name,
                asset_type=asset_type
            )
        else:
            return self.get_list_temporary(
                page=page,
                limit=limit,
                component_name=component_name,
                asset_type=asset_type,
                status=kwargs.get('status'),
                guess_status=kwargs.get('guess_status'),
                data_status=kwargs.get('data_status'),
                component_unique_id=kwargs.get('component_unique_id'),
                component_repeat_id=kwargs.get('component_repeat_id')
            )

    def update(self, component_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        更新软件成分信息

        Args:
            component_data: 软件成分数据

        Returns:
            操作结果
        """
        response = self.client.post('/api/component/update', data=component_data)
        return response

    def add_to_carrier(
        self,
        carrier_unique_id: str,
        component_data: List[Dict[str, Any]],
        security_capability_unique_id: str
    ) -> Dict[str, Any]:
        """
        增加应用载体下软件成分

        注意：此方法可用于创建新的软件成分并关联到特定载体。

        Args:
            carrier_unique_id: 载体唯一ID
            component_data: 软件成分数据
            security_capability_unique_id: 安全能力唯一ID

        Returns:
            操作结果
        """
        params = {"security_capability_unique_id": security_capability_unique_id}
        response = self.client.post(
            f'/api/carrier/add_components/{carrier_unique_id}',
            data=component_data,
            params=params
        )
        return response

    def delete_from_carrier(
        self,
        carrier_unique_id: str,
        component_ids: List[str]
    ) -> Dict[str, Any]:
        """
        删除应用载体下软件成分
        注意：删除软件成分的同时会同步删除对应漏洞

        Args:
            carrier_unique_id: 载体唯一ID
            component_ids: 要删除的成分ID列表

        Returns:
            操作结果
        """
        response = self.client.delete(
            f'/api/carrier/components/{carrier_unique_id}',
            data=component_ids
        )
        return response

    def get_carrier_components(
        self,
        carrier_unique_id: str,
        page: int = 1,
        limit: int = 50,
        component_unique_id: Optional[str] = None,
        component_name: Optional[str] = None,
        component_version: Optional[str] = None,
        status: Optional[str] = None,
        asset_category: Optional[str] = None,
        asset_type: Optional[str] = None,
        vendor: Optional[str] = None,
        ecosystem: Optional[str] = None,
        repository: Optional[str] = None,
        package_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        获取载体下的软件成分列表

        Args:
            carrier_unique_id: 载体唯一ID
            page: 页码
            limit: 每页条数
            component_unique_id: 成分唯一ID
            component_name: 成分名称
            component_version: 成分版本
            status: 状态
            asset_category: 资产类别
            asset_type: 资产类型
            vendor: 供应商
            ecosystem: 生态系统
            repository: 仓库
            package_type: 包类型

        Returns:
            成分列表
        """
        # 构建请求数据
        data = {
            "carrier_unique_id": carrier_unique_id,
            "page": page,
            "limit": limit
        }

        # 添加可选查询参数
        if component_unique_id is not None:
            data["component_unique_id"] = component_unique_id

        if component_name is not None:
            data["component_name"] = component_name

        if component_version is not None:
            data["component_version"] = component_version

        if status is not None:
            data["status"] = status

        if asset_category is not None:
            data["asset_category"] = asset_category

        if asset_type is not None:
            data["asset_type"] = asset_type

        if vendor is not None:
            data["vendor"] = vendor

        if ecosystem is not None:
            data["ecosystem"] = ecosystem

        if repository is not None:
            data["repository"] = repository

        if package_type is not None:
            data["package_type"] = package_type

        response = self.client.post('/api/carrier/components', data=data)
        return response

    def get_component_unique_id(
        self,
        component_name: str,
        component_version: Optional[str] = None,
        vendor: Optional[str] = None,
        ecosystem: Optional[str] = None,
        repository: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        获取软件成分唯一ID

        Args:
            component_name: 成分名称
            component_version: 成分版本
            vendor: 供应商
            ecosystem: 生态系统
            repository: 仓库

        Returns:
            成分唯一ID
        """
        # 构建请求数据
        data = {
            "component_name": component_name
        }

        # 添加可选参数
        if component_version is not None:
            data["component_version"] = component_version

        if vendor is not None:
            data["vendor"] = vendor

        if ecosystem is not None:
            data["ecosystem"] = ecosystem

        if repository is not None:
            data["repository"] = repository

        # 发送请求
        response = self.client.post('/api/component/get_component_unique_id', data=data)
        return response
