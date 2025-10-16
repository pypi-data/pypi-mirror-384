from .auth_service import AuthService
from .msg_service import MsgService
from .token_service import TokenService
from .user_service import UserService
from .base_client import BaseClient
from .types import ClientConfig, UserContext
from .types import *


class QingClient:
    def __init__(self, config: ClientConfig):
        self.config = config
        self.auth = AuthService(config)
        self.msg = MsgService(config)
        self.token = TokenService(config)
        self.user = UserService(config)
    
    def set_user_context(self, context: UserContext) -> 'QingClient':
        """设置用户上下文（后端模式使用）"""
        self.auth.set_user_context(context)
        self.msg.set_user_context(context)
        self.token.set_user_context(context)
        self.user.set_user_context(context)
        return self
    
    def set_token(self, token: str) -> 'QingClient':
        """设置认证令牌（网关模式使用）"""
        self.auth.set_token(token)
        self.msg.set_token(token)
        self.token.set_token(token)
        self.user.set_token(token)
        return self
    
    def clear_token(self) -> 'QingClient':
        """清除认证令牌"""
        self.auth.clear_token()
        self.msg.clear_token()
        self.token.clear_token()
        self.user.clear_token()
        return self
    
    def is_gateway_mode(self) -> bool:
        """判断是否处于网关模式"""
        return hasattr(self.config, 'is_gateway_mode') and self.config.is_gateway_mode