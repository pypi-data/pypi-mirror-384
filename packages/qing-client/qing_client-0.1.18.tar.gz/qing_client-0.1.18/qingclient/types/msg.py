# client/pip/qingclient/msg_service.py
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class MailRequest:
    to: List[str]
    text: Optional[str] = None
    html: Optional[str] = None
    from_: Optional[str] = None
    sender: Optional[str] = None
    cc: Optional[List[str]] = None
    bcc: Optional[List[str]] = None
    replyTo: Optional[str] = None
    subject: Optional[str] = None
    attachments: Optional[List[Dict[str, Any]]] = None

@dataclass
class FeishuMessage:
    url: str
    elements: List[Dict[str, str]]
    title: Optional[str] = None
    bgColor: Optional[str] = None
    noticeUser: Optional[List[Dict[str, str]]] = None
    actions: Optional[List[Dict[str, str]]] = None

# 消息中心相关数据类型
@dataclass
class Message:
    _id: str
    pid: str
    aid: str
    userId: str
    title: str
    content: str
    type: str  # 'system' | 'business' | 'notice'
    category: str
    isRead: bool
    readAt: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    createdAt: str
    updatedAt: str

@dataclass
class MessageQueryParams:
    type: Optional[str] = None  # 'system' | 'business' | 'notice'
    category: Optional[str] = None
    isRead: Optional[bool] = None
    page: Optional[int] = None
    limit: Optional[int] = None
    userId: Optional[str] = None
    pid: Optional[str] = None
    aid: Optional[str] = None

@dataclass
class MessageStats:
    total: int
    byCategory: Dict[str, int]

@dataclass
class CreateMessageRequest:
    userId: Optional[str] = None
    title: str
    content: str
    type: str  # 'system' | 'business' | 'notice'
    category: str
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class BatchCreateMessageRequest:
    messages: List[Dict[str, Any]]

@dataclass
class MarkAsReadRequest:
    userId: Optional[str] = None

@dataclass
class BatchMarkAsReadRequest:
    messageIds: List[str]
    userId: Optional[str] = None

@dataclass
class CategoryInfo:
    category: str
    unreadCount: int
    latestMessage: Optional[Dict[str, Any]] = None

    