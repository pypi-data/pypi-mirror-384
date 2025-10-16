import json
from typing import Any
from .base_client import BaseClient
from .types import RequestOptions, LoginResponse, LoginApiResponse

class AuthService(BaseClient):
    def __init__(self, config):
        super().__init__(config, 'auth')
    
    def login(self, identifier: str, password: str, project_id: int = 0, options: RequestOptions = None) -> LoginResponse:
        # 构建表单数据
        form_data = {
            'grant_type': 'password', 
            'username': identifier,
            'password': password,
        }
        
        headers = {}
        if options and options.headers:
            headers = options.headers.copy()
        # 正确设置Content-Type
        headers['Content-Type'] = 'application/x-www-form-urlencoded'
        
        login_path = '/login'
        
        api_response = self._raw_request(login_path, RequestOptions(
            method='POST',
            headers=headers,
            body=form_data  # 直接传递字典
        ))
        
        # 从API响应中提取实际的登录数据
        login_data = api_response.get('data', {})
        
        # 网关模式下，登录成功后需要保存token
        if hasattr(self.config, 'is_gateway_mode') and self.config.is_gateway_mode:
            token_to_save = api_response.get('access_token') or login_data.get('access_token')
            if token_to_save:
                self.set_token(token_to_save)
        
        # 返回登录数据
        return LoginResponse(
            access_token=login_data.get('access_token'),
            token_type=login_data.get('token_type'),
            expires_at=login_data.get('expires_at'),
            project_id=login_data.get('project_id')
        )
    
    def logout(self, token: str = None, options: RequestOptions = None):
        headers = {}
        if options and options.headers:
            headers = options.headers.copy()
        
        logout_token = token if token else self.token
        if logout_token:
            headers['Authorization'] = f'Bearer {logout_token}'
        
        return self.request('/logout', RequestOptions(
            method='POST',
            headers=headers
        ))
        
    def _raw_request(self, path: str, options: RequestOptions = None) -> Any:
        """发送请求并返回完整的API响应"""
        if options is None:
            options = RequestOptions(method='GET')
        
        try:
            base_url = self._get_base_url()
            full_path = self._get_full_path(path)
            url = f"{base_url}{full_path}"
            
            headers = options.headers.copy() if options.headers else {}
            params = options.params.copy() if options.params else {}
            
            context = options.user_context or self.user_context
            if context and not self._is_gateway_mode():
                headers.update(self._init_user_context_headers(context))
            
            if self._is_gateway_mode() and self.token:
                headers['Authorization'] = f"Bearer {self.token}"
            
            # 根据Content-Type决定请求体格式
            content_type = headers.get('Content-Type', '').lower()
            request_kwargs = {
                'method': options.method,
                'url': url,
                'headers': headers,
                'params': params,
                'timeout': 30
            }
            
            if content_type == 'application/x-www-form-urlencoded' and isinstance(options.body, dict):
                request_kwargs['data'] = options.body
            else:
                request_kwargs['json'] = options.body
            
            response = self.session.request(**request_kwargs)
            
            response.raise_for_status()
            response_data = response.json()
            
            if not response_data.get('success', False):
                raise Exception(response_data.get('message', '业务请求失败'))
            
            return response_data
            
        except Exception as error:
            self._handle_api_error(error, path)