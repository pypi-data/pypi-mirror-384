# client/pip/qingclient/types/wx.py
from dataclasses import dataclass
from typing import Optional

# 微信小程序access_token响应
@dataclass
class WxMiniProgramTokenResponse:
    access_token: str

# 微信公众号access_token响应
@dataclass
class WxOfficialAccountTokenResponse:
    access_token: str

# 微信公众号jsapi_ticket响应
@dataclass
class WxJsapiTicketResponse:
    jsapi_ticket: str

# 微信小程序登录请求
@dataclass
class WxMiniProgramLoginRequest:
    appid: str
    code: str

# 微信小程序登录响应
@dataclass
class WxMiniProgramLoginResponse:
    openid: str
    session_key: str
    unionid: Optional[str] = None

# 微信分享签名请求
@dataclass
class WxSignatureRequest:
    appid: str
    url: str
    imgUrl: Optional[str] = None

# 微信分享签名响应
@dataclass
class WxSignatureResponse:
    appId: str
    timestamp: int
    nonceStr: str
    signature: str
    url: str
    imgUrl: str
    
# 微信小程序获取手机号请求
@dataclass
class WxMiniProgramPhoneRequest:
    appid: str
    code: str

# 微信小程序获取手机号响应中的水印信息
@dataclass
class Watermark:
    timestamp: int
    appid: str

# 微信小程序获取手机号响应中的手机号信息
@dataclass
class PhoneInfo:
    phoneNumber: str
    purePhoneNumber: str
    countryCode: str
    watermark: Watermark

# 微信小程序获取手机号响应
@dataclass
class WxMiniProgramPhoneResponse:
    phone_info: PhoneInfo    
