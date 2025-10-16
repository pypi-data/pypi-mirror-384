from dataclasses import dataclass

@dataclass
class LoginResponse:
    access_token: str
    token_type: str
    expires_at: str
    project_id: int

@dataclass
class LoginApiResponse:
    success: bool
    message: str
    access_token: str  # 顶层的access_token字段
    data: LoginResponse  # data字段中的登录信息