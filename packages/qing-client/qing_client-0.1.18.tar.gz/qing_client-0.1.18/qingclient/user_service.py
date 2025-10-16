from .base_client import BaseClient
from .types import RequestOptions, PaginatedResponse, UserResponse, UserListResponse
from .types import UserCreateRequest, UserUpdateRequest, PasswordChangeRequest

class UserService(BaseClient):
    def __init__(self, config):
        super().__init__(config, 'users')
    
    def get_current_user(self, options: RequestOptions = None) -> UserResponse:
        """获取当前用户信息"""
        return self.request('/me', RequestOptions(
            method='GET',
            headers=options.headers if options else None
        ))
    
    def get_user_by_id(self, user_id: int, options: RequestOptions = None) -> UserResponse:
        """根据ID获取用户详情"""
        return self.request(f'/{user_id}', RequestOptions(
            method='GET',
            headers=options.headers if options else None
        ))
    
    def create_user(self, user_data: UserCreateRequest, options: RequestOptions = None) -> UserResponse:
        """创建新用户"""
        return self.request('', RequestOptions(
            method='POST',
            body=user_data.__dict__,
            headers=options.headers if options else None
        ))
    
    def update_user(self, user_id: int, update_data: UserUpdateRequest, options: RequestOptions = None) -> UserResponse:
        """更新用户信息"""
        return self.request(f'/{user_id}', RequestOptions(
            method='PUT',
            body={k: v for k, v in update_data.__dict__.items() if v is not None},
            headers=options.headers if options else None
        ))
    
    def deactivate_user(self, user_id: int, options: RequestOptions = None) -> dict:
        """停用用户"""
        return self.request(f'/{user_id}', RequestOptions(
            method='DELETE',
            headers=options.headers if options else None
        ))
    
    def restore_user(self, user_id: int, options: RequestOptions = None) -> UserResponse:
        """恢复已停用用户"""
        return self.request(f'/{user_id}/restore', RequestOptions(
            method='POST',
            headers=options.headers if options else None
        ))
    
    def admin_reset_password(self, user_id: int, new_password: str, options: RequestOptions = None) -> dict:
        """管理员重置用户密码"""
        return self.request(f'/{user_id}/password', RequestOptions(
            method='PUT',
            body={'new_password': new_password},
            headers=options.headers if options else None
        ))
    
    def list_users(self, include_inactive: bool = False, page: int = 1, per_page: int = 10, options: RequestOptions = None) -> PaginatedResponse[UserListResponse]:
        """获取用户列表"""
        return self.paginated_request('', RequestOptions(
            method='GET',
            params={
                'include_inactive': include_inactive,
                'page': page,
                'per_page': per_page
            },
            headers=options.headers if options else None
        ))
    
    def assign_to_project(self, user_id: int, project_id: int, options: RequestOptions = None) -> dict:
        """将用户分配到项目"""
        return self.request(f'/{user_id}/assign-project', RequestOptions(
            method='POST',
            body={'project_id': project_id},
            headers=options.headers if options else None
        ))
    
    def remove_from_project(self, user_id: int, options: RequestOptions = None) -> dict:
        """将用户从项目中移除"""
        return self.request(f'/{user_id}/remove-project', RequestOptions(
            method='POST',
            headers=options.headers if options else None
        ))