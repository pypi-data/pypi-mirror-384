#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
SARM SDK V2 客户端

提供统一的 V2 API 访问入口。
"""

import json
import requests
from typing import Dict, Any, Optional, List, Union
import time
from urllib.parse import urljoin
from .exceptions import (
    SARMNetworkError,
    SARMAPIError,
    SARMAuthenticationError,
    SARMValidationError
)

# V2 API imports
from sarm_sdk.apis.application_v2 import ApplicationAPI as ApplicationAPIV2
from sarm_sdk.apis.business_system_v2 import BusinessSystemAPI as BusinessSystemAPIV2
from sarm_sdk.apis.carrier_v2 import CarrierAPI as CarrierAPIV2
from sarm_sdk.apis.carrier_data_import_v2 import VulnDataImportAPI as CarrierDataImportAPIV2
from sarm_sdk.apis.issue_data_import_v2 import IssueDataImportAPI as IssueDataImportAPIV2
from sarm_sdk.apis.component_v2 import ComponentAPI as ComponentAPIV2
from sarm_sdk.apis.organization_v2 import OrganizationAPI as OrganizationAPIV2
from sarm_sdk.apis.organize_user_v2 import OrganizeUserAPI as OrganizeUserAPIV2
from sarm_sdk.apis.security_capability_v2 import SecurityCapabilityAPI as SecurityCapabilityAPIV2
from sarm_sdk.apis.security_issue_v2 import SecurityIssueAPI as SecurityIssueAPIV2
from sarm_sdk.apis.vulnerability_v2 import VulnerabilityAPI as VulnerabilityAPIV2
from sarm_sdk.apis.common_v2 import CommonAPI as CommonAPIV2


class SARMClientV2:
    """SARM V2 API 客户端"""

    def __init__(
        self,
        base_url: str,
        token: str,
        factory_log_id: str = "",
        timeout: int = 30,
        max_retries: int = 3,
        retry_delay: float = 1.0
    ):
        """
        初始化客户端

        Args:
            base_url: API基础URL
            token: 认证令牌
            factory_log_id: 工厂日志ID
            timeout: 请求超时时间(秒)
            max_retries: 最大重试次数
            retry_delay: 重试延迟(秒)
        """
        self.base_url = base_url.rstrip('/')
        self.token = token
        self.factory_log_id = factory_log_id
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_delay = retry_delay

        # 设置请求头
        self.headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.token}'
        }

        if factory_log_id:
            self.headers['Factory-Log-Id'] = factory_log_id

        # 创建session
        self.session = requests.Session()
        self.session.headers.update(self.headers)

        # 初始化 V2 API 模块
        self._init_v2_apis()

    def _init_v2_apis(self):
        """初始化所有 V2 API 模块"""
        self.organizations_v2 = OrganizationAPIV2(self)
        self.carriers_v2 = CarrierAPIV2(self)
        self.security_capabilities_v2 = SecurityCapabilityAPIV2(self)
        self.issue_data_import_v2 = IssueDataImportAPIV2(self)
        self.carrier_data_import_v2 = CarrierDataImportAPIV2(self)
        self.common_v2 = CommonAPIV2(self)
        self.vulnerabilities_v2 = VulnerabilityAPIV2(self)
        self.security_issues_v2 = SecurityIssueAPIV2(self)
        self.components_v2 = ComponentAPIV2(self)
        self.business_systems_v2 = BusinessSystemAPIV2(self)
        self.applications_v2 = ApplicationAPIV2(self)
        self.organize_users_v2 = OrganizeUserAPIV2(self)

        # 为了向后兼容，也提供不带 _v2 后缀的属性名
        self.organizations = self.organizations_v2
        self.carriers = self.carriers_v2
        self.security_capabilities = self.security_capabilities_v2
        self.issue_data_import = self.issue_data_import_v2
        self.carrier_data_import = self.carrier_data_import_v2
        self.common = self.common_v2
        self.vulnerabilities = self.vulnerabilities_v2
        self.security_issues = self.security_issues_v2
        self.components = self.components_v2
        self.business_systems = self.business_systems_v2
        self.applications = self.applications_v2
        self.organize_users = self.organize_users_v2

    def _get_full_url(self, endpoint: str) -> str:
        """获取完整的URL"""
        return urljoin(self.base_url, endpoint.lstrip('/'))

    def _make_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Union[Dict[str, Any], List[Any]]] = None,
        params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        发送HTTP请求

        Args:
            method: HTTP方法
            endpoint: API端点
            data: 请求数据
            params: URL参数

        Returns:
            响应数据

        Raises:
            SARMAPIError: API错误
            SARMNetworkError: 连接/网络错误
        """
        url = self._get_full_url(endpoint)

        # 准备请求参数
        request_kwargs = {
            'timeout': self.timeout,
            'params': params
        }

        # 处理请求体
        if data is not None:
            request_kwargs['json'] = data

        # 重试逻辑
        for attempt in range(self.max_retries):
            try:
                response = self.session.request(method, url, **request_kwargs)

                # 检查HTTP状态码
                if response.status_code == 401:
                    raise SARMAuthenticationError("认证失败，请检查token是否正确")

                # 尝试解析JSON响应
                try:
                    result = response.json()
                except json.JSONDecodeError:
                    # 如果不是JSON响应，检查HTTP状态码
                    if response.status_code >= 400:
                        # 对于错误响应，尝试提取更多信息
                        error_text = response.text[:1000] if response.text else '无响应内容'
                        raise SARMAPIError(
                            f"HTTP {response.status_code} 错误: {error_text}",
                            response.status_code
                        )
                    # 如果是成功的非JSON响应，返回文本内容
                    result = {'text': response.text, 'status_code': response.status_code}

                # 检查业务错误码
                if isinstance(result, dict):
                    code = result.get('code')
                    if code and code != 200:
                        message = result.get('message') or result.get('msg') or '未知错误'

                        # 根据错误码类型抛出相应异常
                        if code == 400:
                            raise SARMValidationError(message, response.status_code)
                        elif code == 401:
                            raise SARMAuthenticationError(message)
                        else:
                            raise SARMAPIError(message, response.status_code)

                    # 即使业务code为200或不存在，也要检查HTTP状态码
                    # 这样可以捕获HTTP 500等服务器错误
                    if response.status_code >= 400:
                        # 尝试从多个可能的字段中提取错误信息
                        message = (
                            result.get('message') or
                            result.get('msg') or
                            result.get('error') or
                            result.get('detail') or
                            result.get('error_description')
                        )

                        # 如果还是没有找到错误消息，尝试将整个响应转为字符串
                        if not message:
                            # 排除一些不需要的字段
                            error_data = {k: v for k, v in result.items() if k not in ['code', 'status_code', 'timestamp']}
                            if error_data:
                                message = json.dumps(error_data, ensure_ascii=False, indent=2)
                            else:
                                message = response.text[:1000] if response.text else '服务器错误'

                        raise SARMAPIError(
                            f"{message} (HTTP {response.status_code})",
                            response.status_code
                        )

                return result

            except requests.exceptions.ConnectionError as e:
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay * (attempt + 1))
                    continue
                raise SARMNetworkError(f"连接失败: {str(e)}")
            except requests.exceptions.Timeout:
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay * (attempt + 1))
                    continue
                raise SARMNetworkError(f"请求超时 ({self.timeout}秒)")
            except requests.exceptions.RequestException as e:
                raise SARMNetworkError(f"请求异常: {str(e)}")

    def get(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """发送GET请求"""
        return self._make_request('GET', endpoint, params=params)

    def post(
        self,
        endpoint: str,
        data: Optional[Union[Dict[str, Any], List[Any]]] = None
    ) -> Dict[str, Any]:
        """发送POST请求"""
        return self._make_request('POST', endpoint, data=data)
    def put(
        self,
        endpoint: str,
        data: Optional[Union[Dict[str, Any], List[Any]]] = None
    ) -> Dict[str, Any]:
        """发送PUT请求"""
        return self._make_request('PUT', endpoint, data=data)

    def delete(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """发送DELETE请求"""
        return self._make_request('DELETE', endpoint, params=params)

    def close(self):
        """关闭客户端连接"""
        if self.session:
            self.session.close()

    def __enter__(self):
        """上下文管理器入口"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        self.close()