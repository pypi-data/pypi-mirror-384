#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
SARM SDK 安全问题 API V2版本

提供安全问题相关的API操作，V2版本已移除所有数据校验逻辑，提供更快的数据处理性能。
"""

from typing import List, Dict, Any, Optional, TYPE_CHECKING
from ..models.response import BatchOperationResult

if TYPE_CHECKING:
    from ..client_v2 import SARMClientV2


class SecurityIssueAPI:
    """
    安全问题API类 V2版本 - 已移除数据校验

    注意：安全问题创建应通过 CarrierDataImportAPI 的载体维度多数据录入接口实现，
    本API提供查询、更新和关联管理功能。
    """

    def __init__(self, client: 'SARMClientV2'):
        self.client = client

    def update(self, issue_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        更新安全问题信息

        Args:
            issue_data: 安全问题数据，必须包含 issue_unique_id

        Returns:
            更新结果
        """
        response = self.client.post(
            '/api/issue/update',
            data=issue_data
        )
        return response

    def get_list_temporary(
        self,
        page: int,
        limit: int,
        issue_title: Optional[str] = None,
        issue_repeat_id: Optional[str] = None,
        issue_unique_id: Optional[str] = None,
        issue_level: Optional[str] = None,
        data_status: Optional[str] = None,
        guess_status: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        获取安全问题列表（预审）

        Args:
            page: 页码（必填）
            limit: 每页条数（必填）
            issue_title: 安全问题名称，模糊查询（可选）
            issue_repeat_id: 安全问题重复性标识（可选）
            issue_unique_id: 安全问题唯一id（可选）
            issue_level: 安全问题级别，可选值: critical(严重), high(高), medium(中), low(低)（可选）
            data_status: 安全问题状态，可选值: imperfect(待完善), wait_confirm(待确认), perfect(待发布)（可选）
            guess_status: 安全问题智能分析状态，可选值: wait(待分析), process(分析中), finish(分析完成), fail(分析失败)（可选）

        Returns:
            安全问题列表
        """
        data = {
            "page": page,
            "limit": limit
        }
        if issue_title is not None:
            data["issue_title"] = issue_title
        if issue_repeat_id is not None:
            data["issue_repeat_id"] = issue_repeat_id
        if issue_unique_id is not None:
            data["issue_unique_id"] = issue_unique_id
        if issue_level is not None:
            data["issue_level"] = issue_level
        if data_status is not None:
            data["data_status"] = data_status
        if guess_status is not None:
            data["guess_status"] = guess_status

        response = self.client.post('/api/v2/issue/temporary/get_list', data=data)
        return response

    def get_list(
        self,
        page: int,
        limit: int,
        **kwargs
    ) -> Dict[str, Any]:
        """
        获取安全问题列表（统一接口，默认查询预审数据）

        Args:
            page: 页码
            limit: 每页条数
            **kwargs: 其他查询参数，参考 get_list_temporary 的参数

        Returns:
            安全问题列表
        """
        return self.get_list_temporary(page=page, limit=limit, **kwargs)

    def get_component_vuln_list(self, issue_unique_id: str) -> Dict[str, Any]:
        """
        获取安全问题关联的成分和漏洞列表

        Args:
            issue_unique_id: 安全问题唯一ID

        Returns:
            关联的成分和漏洞列表
        """
        response = self.client.get(f'/api/issue/component_vuln_list/{issue_unique_id}')
        return response

    def update_component_vuln_list(
        self,
        issue_unique_id: str,
        component_ids: List[str],
        vuln_ids: List[str]
    ) -> Dict[str, Any]:
        """
        更新安全问题关联的成分和漏洞列表

        Args:
            issue_unique_id: 安全问题唯一ID
            component_ids: 成分唯一ID列表
            vuln_ids: 漏洞唯一ID列表

        Returns:
            操作结果
        """
        data = {
            "component_unique_id": component_ids,
            "vuln_unique_id": vuln_ids
        }
        response = self.client.post(
            f'/api/issue/update_component_vuln_list/{issue_unique_id}',
            data=data
        )
        return response

    def update_vuln_list(
        self,
        issue_unique_id: str,
        component_unique_id: List[str]
    ) -> Dict[str, Any]:
        """
        更新安全问题关联的成分列表

        Args:
            issue_unique_id: 安全问题唯一ID
            component_unique_id: 成分唯一ID列表

        Returns:
            操作结果
        """
        data = {"component_unique_id": component_unique_id}
        response = self.client.post(
            f'/api/issue/update_component_list/{issue_unique_id}',
            data=data
        )
        return response
