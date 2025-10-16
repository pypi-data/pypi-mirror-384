from dataclasses import dataclass
from typing import Optional
from enum import Enum

class UserRole(str, Enum):
    """用户角色枚举"""
    SUPER_ADMIN = 'SUPER_ADMIN'
    ADMIN = 'ADMIN'
    STAFF = 'STAFF'
    USER = 'USER'

@dataclass
class UserCreateRequest:
    """创建用户请求"""
    username: str
    email: str
    password: str
    name: Optional[str] = None
    role: UserRole = UserRole.USER
    phone: Optional[str] = None
    avatar: Optional[str] = None
    project_id: int = 0

@dataclass
class UserUpdateRequest:
    """更新用户请求"""
    name: Optional[str] = None
    avatar: Optional[str] = None
    phone: Optional[str] = None
    role: Optional[UserRole] = None
    project_id: Optional[int] = None

@dataclass
class PasswordChangeRequest:
    """密码修改请求"""
    new_password: str

@dataclass
class UserResponse:
    """用户响应"""
    id: int
    username: str
    email: str
    name: Optional[str]
    avatar: Optional[str]
    role: str
    phone: Optional[str]
    last_login_ip: Optional[str]
    last_login: Optional[str]
    created_at: str
    updated_at: str
    is_active: bool
    project_id: int

@dataclass
class UserListResponse:
    """用户列表响应"""
    id: int
    username: str
    name: Optional[str]
    email: str
    role: str
    is_active: bool
    created_at: str
    project_id: int