# client/pip/qingclient/msg_service.py
from typing import Optional
from .base_client import BaseClient
from .types import (
     RequestOptions, MailRequest, FeishuMessage,CreateMessageRequest,MessageQueryParams,
     MarkAsReadRequest, BatchMarkAsReadRequest, BatchCreateMessageRequest
)

class MsgService(BaseClient):
    def __init__(self, config):
        super().__init__(config, 'msg')
    
    def send_mail(self, request: MailRequest, options: RequestOptions = None):
        """发送邮件"""
        return self.request('/mail/send', RequestOptions(
            method='POST',
            body=request.__dict__,
            headers=options.headers if options else None
        ))
    
    def send_feishu_message(self, message: FeishuMessage, options: RequestOptions = None):
        """发送飞书消息"""
        return self.request('/webhook/feishu/send', RequestOptions(
            method='POST',
            body=message.__dict__,
            headers=options.headers if options else None
        ))
    
    # === 消息中心相关接口 ===
    
    def get_messages(self, params: Optional[MessageQueryParams] = None, options: RequestOptions = None):
        """获取用户消息列表"""
        return self.request('/message/list', RequestOptions(
            method='GET',
            params=params.__dict__ if params else {},
            headers=options.headers if options else None
        ))
    
    def get_admin_messages(self, params: Optional[MessageQueryParams] = None, options: RequestOptions = None):
        """管理员获取消息列表（需要管理员权限）"""
        return self.request('/message/admin/list', RequestOptions(
            method='GET',
            params=params.__dict__ if params else {},
            headers=options.headers if options else None
        ))
    
    def mark_as_read(self, message_id: str, request: Optional[MarkAsReadRequest] = None, options: RequestOptions = None):
        """标记单条消息为已读"""
        return self.request(f'/message/{message_id}/read', RequestOptions(
            method='PATCH',
            body=request.__dict__ if request else {},
            headers=options.headers if options else None
        ))
    
    def mark_many_as_read(self, request: BatchMarkAsReadRequest, options: RequestOptions = None):
        """批量标记消息为已读"""
        return self.request('/message/batch/read', RequestOptions(
            method='PATCH',
            body=request.__dict__,
            headers=options.headers if options else None
        ))
    
    def delete_message(self, message_id: str, request: Optional[MarkAsReadRequest] = None, options: RequestOptions = None):
        """删除消息（软删除）"""
        return self.request(f'/message/{message_id}', RequestOptions(
            method='DELETE',
            body=request.__dict__ if request else {},
            headers=options.headers if options else None
        ))
    
    def get_unread_stats(self, user_id: Optional[str] = None, options: RequestOptions = None):
        """获取未读消息统计"""
        params = {'userId': user_id} if user_id else {}
        return self.request('/message/stats', RequestOptions(
            method='GET',
            params=params,
            headers=options.headers if options else None
        ))
    
    def get_categories(self, options: RequestOptions = None):
        """获取用户消息分类"""
        return self.request('/message/categories', RequestOptions(
            method='GET',
            headers=options.headers if options else None
        ))
    
    def create_message(self, request: CreateMessageRequest, options: RequestOptions = None):
        """创建消息（需要管理员权限）"""
        return self.request('/message', RequestOptions(
            method='POST',
            body=request.__dict__,
            headers=options.headers if options else None
        ))
    
    def create_many_messages(self, request: BatchCreateMessageRequest, options: RequestOptions = None):
        """批量创建消息（需要管理员权限）"""
        return self.request('/message/batch', RequestOptions(
            method='POST',
            body=request.__dict__,
            headers=options.headers if options else None
        ))
        
        