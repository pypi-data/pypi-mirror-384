#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
SARM SDK 载体数据录入 API V2版本

提供载体维度的多数据录入功能，V2版本已移除所有数据校验逻辑，提供更快的数据处理性能。
"""

from typing import List, Dict, Any, Optional, TYPE_CHECKING
from ..models.response import BatchOperationResult

if TYPE_CHECKING:
    from ..client_v2 import SARMClientV2


class VulnDataImportAPI:
    """
    漏洞数据导入API V2版本 - 已移除数据校验

    提供漏洞维度的多数据录入功能，一次性录入载体、组件和漏洞数据。
    这是创建载体、组件和漏洞的推荐方式。
    """

    def __init__(self, client: 'SARMClientV2'):
        """
        初始化载体数据导入API

        Args:
            client: SARM客户端实例
        """
        self.client = client

    def import_carrier_data(self, carrier_data_list: List[Dict[str, Any]]):
        """
        载体维度多数据录入，一次性录入载体、组件和漏洞数据

        Args:
            carrier_data_list: 载体数据列表

        Returns:
            BatchOperationResult: 批量操作结果
        """
        response = self.client.post('/api/insert/insert_carrier_vuln', data=carrier_data_list)

        # 处理响应
        # result = BatchOperationResult(**response.get('data', {}))
        return response

    def create_carrier_data_structure(
        self,
        carrier: Dict[str, Any],
        component_list: Optional[List[Dict[str, Any]]] = None,
        vuln_list: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        创建标准的漏洞数据结构

        Args:
            carrier: 载体基础信息
            component_list: 组件列表
            vuln_list: 漏洞列表

        Returns:
            Dict[str, Any]: 标准漏洞数据结构
        """
        # 构建标准数据结构
        carrier_data: Dict[str, Any] = {
            "carrier": carrier
        }

        if component_list:
            carrier_data["component_list"] = component_list

        if vuln_list:
            carrier_data["vuln_list"] = vuln_list

        return carrier_data

    def create_component(
        self,
        carrier_unique_id: str,
        component_data: Dict[str, Any],
        security_capability_unique_id: str
    ) -> Dict[str, Any]:
        """
        创建软件组件并关联到指定载体

        Args:
            carrier_unique_id: 载体唯一ID
            component_data: 组件数据
            security_capability_unique_id: 安全能力唯一ID

        Returns:
            Dict[str, Any]: 操作结果
        """
        # 构建载体数据结构
        carrier_info = {
            "carrier_unique_id": carrier_unique_id
        }

        # 添加安全能力关联
        component_with_capability = component_data.copy()
        component_with_capability["security_capability_unique_id"] = security_capability_unique_id

        carrier_data = self.create_carrier_data_structure(
            carrier=carrier_info,
            component_list=[component_with_capability]
        )

        # 发送请求
        result = self.import_carrier_data([carrier_data])

        # 简化返回结果
        if result.success_count == 1:
            return {"code": 200, "msg": "Success", "msg_zh": "成功"}
        else:
            error_item = next((item for item in result.data if not item.success), None)
            if error_item:
                return {"code": 400, "msg": error_item.msg, "msg_zh": error_item.msg}
            return {"code": 400, "msg": "Failed to create component", "msg_zh": "创建组件失败"}

    def create_vulnerability(
        self,
        carrier_unique_id: str,
        vuln_data: Dict[str, Any],
        component_unique_id: str,
        security_capability_unique_id: str
    ) -> Dict[str, Any]:
        """
        创建漏洞并关联到指定载体和组件

        Args:
            carrier_unique_id: 载体唯一ID
            vuln_data: 漏洞数据
            component_unique_id: 组件唯一ID
            security_capability_unique_id: 安全能力唯一ID

        Returns:
            Dict[str, Any]: 操作结果
        """
        # 构建载体数据结构
        carrier_info = {
            "carrier_unique_id": carrier_unique_id
        }

        # 添加组件和安全能力关联
        vuln_with_relations = vuln_data.copy()
        vuln_with_relations["component_unique_id"] = component_unique_id
        vuln_with_relations["security_capability_unique_id"] = security_capability_unique_id

        carrier_data = self.create_carrier_data_structure(
            carrier=carrier_info,
            vuln_list=[vuln_with_relations]
        )

        # 发送请求
        result = self.import_carrier_data([carrier_data])

        # 简化返回结果
        if result.success_count == 1:
            return {"code": 200, "msg": "Success", "msg_zh": "成功"}
        else:
            error_item = next((item for item in result.data if not item.success), None)
            if error_item:
                return {"code": 400, "msg": error_item.msg, "msg_zh": error_item.msg}
            return {"code": 400, "msg": "Failed to create vulnerability", "msg_zh": "创建漏洞失败"}
