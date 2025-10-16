# client/pip/qingclient/token_service.py

from .base_client import BaseClient
from .types import (
    RequestOptions, WxOfficialAccountTokenResponse, WxJsapiTicketResponse, 
    WxSignatureRequest, WxSignatureResponse, WxMiniProgramTokenResponse,
    WxMiniProgramLoginRequest, WxMiniProgramLoginResponse, WxMiniProgramPhoneRequest, WxMiniProgramPhoneResponse
)

class TokenService(BaseClient):
    def __init__(self, config):
        super().__init__(config, 'token')
    
    def get_wx_official_account_token(self, appid: str, options: RequestOptions = None) -> WxOfficialAccountTokenResponse:
        """
        获取微信公众号access_token
        
        Args:
            appid: 微信公众号appid
            options: 可选的请求配置
            
        Returns:
            WxOfficialAccountTokenResponse: 包含access_token的响应
        """
        return self.request('/wxh5/accesstoken', RequestOptions(
            method='GET',
            params={'appid': appid},
            headers=options.headers if options else None
        ))
    
    def get_wx_jsapi_ticket(self, appid: str, options: RequestOptions = None) -> WxJsapiTicketResponse:
        """
        获取微信公众号jsapi_ticket
        
        Args:
            appid: 微信公众号appid
            options: 可选的请求配置
            
        Returns:
            WxJsapiTicketResponse: 包含jsapi_ticket的响应
        """
        return self.request('/wxh5/jsapi_ticket', RequestOptions(
            method='GET',
            params={'appid': appid},
            headers=options.headers if options else None
        ))
    
    def get_wx_signature(self, signature_request: WxSignatureRequest, options: RequestOptions = None) -> WxSignatureResponse:
        """
        获取微信分享签名
        
        Args:
            signature_request: 包含appid、url和imgUrl的签名请求
            options: 可选的请求配置
            
        Returns:
            WxSignatureResponse: 包含签名信息的响应
        """
        return self.request('/wxh5/signature', RequestOptions(
            method='POST',
            body=signature_request,
            headers=options.headers if options else None
        ))
    
    def get_wx_mini_program_token(self, appid: str, options: RequestOptions = None) -> WxMiniProgramTokenResponse:
        """
        获取微信小程序access_token
        
        Args:
            appid: 微信小程序appid
            options: 可选的请求配置
            
        Returns:
            WxMiniProgramTokenResponse: 包含access_token的响应
        """
        return self.request('/wxmp/accesstoken', RequestOptions(
            method='GET',
            params={'appid': appid},
            headers=options.headers if options else None
        ))
    
    def wx_mini_program_login(self, login_request: WxMiniProgramLoginRequest, options: RequestOptions = None) -> WxMiniProgramLoginResponse:
        """
        微信小程序登录 - 使用code换取session信息
        
        Args:
            login_request: 包含appid和code的登录请求
            options: 可选的请求配置
            
        Returns:
            WxMiniProgramLoginResponse: 包含openid、session_key和unionid的响应
        """
        return self.request('/wxmp/login', RequestOptions(
            method='POST',
            body=login_request,
            headers=options.headers if options else None
        ))

    def get_wx_mini_program_phone(self, phone_request: WxMiniProgramPhoneRequest, options: RequestOptions = None) -> WxMiniProgramPhoneResponse:
        """
        获取微信小程序用户手机号
        
        Args:
            phone_request: 包含appid和code的获取手机号请求
            options: 可选的请求配置
            
        Returns:
            WxMiniProgramPhoneResponse: 包含手机号信息的响应
        """
        return self.request('/wxmp/phone', RequestOptions(
            method='POST',
            body=phone_request,
            headers=options.headers if options else None
        ))