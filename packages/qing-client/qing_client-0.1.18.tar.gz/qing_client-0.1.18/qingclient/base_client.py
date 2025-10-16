# client/pip/qingclient/base_client.py
import requests
import json
from typing import Dict, Any, Optional, List, TypeVar, Generic
from dataclasses import dataclass
from .types import UserContext, ClientConfig, RequestOptions, ApiResponse, PaginatedResponse

T = TypeVar('T')

class BaseClient:
    def __init__(self, config: ClientConfig, service_name: str):
        self.config = config
        self.service_name = service_name
        self.user_context = None
        self.token = None  # 用于在网关模式下存储认证令牌
        
        # 创建session
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        })
    
    def _get_base_url(self) -> str:
        """根据配置确定基础URL"""
        # 网关模式：所有请求发往网关
        if hasattr(self.config, 'gateway_url') and self.config.gateway_url:
            return self.config.gateway_url
        
        # 后端模式：根据服务名返回对应的独立地址
        service_urls = {
            'auth': getattr(self.config, 'auth_service_url', None),
            'msg': getattr(self.config, 'msg_service_url', None),
            'users': getattr(self.config, 'user_service_url', None),
            'file': getattr(self.config, 'file_service_url', None),
            'survey': getattr(self.config, 'survey_service_url', None),
            'token': getattr(self.config, 'token_service_url', None),
            'aigc': getattr(self.config, 'aigc_service_url', None),
        }
        
        if self.service_name not in service_urls:
            raise ValueError(f"Unsupported service: {self.service_name}")
        
        service_url = service_urls[self.service_name]
        if not service_url:
            raise ValueError(f"Service URL for '{self.service_name}' is not configured")
            
        return service_url
    
    def _is_gateway_mode(self) -> bool:
        """判断是否处于网关模式"""
        return hasattr(self.config, 'gateway_url') and bool(self.config.gateway_url)
    
    def _get_full_path(self, path: str) -> str:
        """获取完整的请求路径，网关模式下添加服务前缀"""
        return f"/api/{self.service_name}{path}"
    
    def set_user_context(self, context: UserContext) -> 'BaseClient':
        """设置用户上下文（后端模式使用）"""
        self.user_context = context
        return self
    
    def set_token(self, token: str) -> 'BaseClient':
        """设置认证令牌（网关模式使用）"""
        self.token = token
        return self
    
    def clear_token(self) -> 'BaseClient':
        """清除认证令牌"""
        self.token = None
        return self
    
    def init_user_context_headers(self, context: UserContext) -> Dict[str, str]:
        """生成用户上下文请求头（后端模式使用）"""
        return {
            'v-user-id': context.user_id,
            'v-user-role': context.role,
            'v-project-id': context.project_id
        }
    
    def _handle_api_error(self, error: Exception, path: str) -> None:
        """统一错误处理方法"""
        error_message = f"[{self.service_name}服务] "
        
        if hasattr(error, 'response') and error.response is not None:
            response = error.response
            try:
                response_data = response.json()
                if 'message' in response_data:
                    error_message += response_data['message']
                elif 'error' in response_data:
                    error_message += response_data['error']
                else:
                    error_message += f"请求失败，状态码: {response.status_code}"
            except (json.JSONDecodeError, AttributeError):
                error_message += f"请求失败，状态码: {response.status_code}"
            
            # 添加详细错误信息
            error_message += f" | 状态码: {response.status_code}"
            if hasattr(response, 'headers') and 'x-request-id' in response.headers:
                error_message += f" | 请求ID: {response.headers['x-request-id']}"
        else:
            error_message += str(error)
        
        # 添加路径信息
        error_message += f" (路径: {path})"
        
        raise Exception(error_message)
    
    def request(self, path: str, options: RequestOptions = None) -> Any:
        """
        发送API请求
        
        Args:
            path: 请求路径
            options: 请求选项
            
        Returns:
            API响应数据
            
        Raises:
            Exception: 当请求失败时抛出异常
        """
        if options is None:
            options = RequestOptions(method='GET')
        
        try:
            # 获取基础URL和完整路径
            base_url = self._get_base_url()
            full_path = self._get_full_path(path)
            url = f"{base_url}{full_path}"
            
            # 准备请求参数
            headers = options.headers.copy() if options.headers else {}
            params = options.params.copy() if options.params else {}
            
            # 添加用户上下文（后端模式）
            context = options.user_context or self.user_context
            if context and not self._is_gateway_mode():
                headers.update(self.init_user_context_headers(context))
            
            # 添加认证令牌（网关模式）
            if self._is_gateway_mode() and self.token:
                headers['Authorization'] = f"Bearer {self.token}"
            
            # 发送请求
            response = self.session.request(
                method=options.method,
                url=url,
                headers=headers,
                params=params,
                json=options.body,
                timeout=30
            )
            
            # 检查HTTP状态
            response.raise_for_status()
            
            # 解析响应
            response_data = response.json()
            
            # 检查业务成功状态
            if not response_data.get('success', False):
                raise Exception(response_data.get('message', '业务请求失败'))
            
            # 返回实际数据
            return response_data.get('data')
            
        except Exception as error:
            self._handle_api_error(error, path)
    
    def paginated_request(self, path: str, options: RequestOptions = None) -> PaginatedResponse:
        """
        发送分页API请求
        
        Args:
            path: 请求路径
            options: 请求选项
            
        Returns:
            分页响应对象
            
        Raises:
            Exception: 当请求失败时抛出异常
        """
        if options is None:
            options = RequestOptions(method='GET')
        
        try:
            # 获取基础URL和完整路径
            base_url = self._get_base_url()
            full_path = self._get_full_path(path)
            url = f"{base_url}{full_path}"
            
            # 准备请求参数
            headers = options.headers.copy() if options.headers else {}
            params = options.params.copy() if options.params else {}
            
            # 添加用户上下文（后端模式）
            context = options.user_context or self.user_context
            if context and not self._is_gateway_mode():
                headers.update(self.init_user_context_headers(context))
            
            # 添加认证令牌（网关模式）
            if self._is_gateway_mode() and self.token:
                headers['Authorization'] = f"Bearer {self.token}"
            
            # 发送请求
            response = self.session.request(
                method=options.method,
                url=url,
                headers=headers,
                params=params,
                json=options.body,
                timeout=30
            )
            
            # 检查HTTP状态
            response.raise_for_status()
            
            # 解析响应
            response_data = response.json()
            
            # 检查业务成功状态
            if not response_data.get('success', False):
                raise Exception(response_data.get('message', '业务请求失败'))
            
            # 返回分页响应
            return PaginatedResponse(
                data=response_data.get('data', []),
                success=response_data.get('success', False),
                message=response_data.get('message', ''),
                pagination=response_data.get('pagination', {})
            )
            
        except Exception as error:
            self._handle_api_error(error, path)
            
            