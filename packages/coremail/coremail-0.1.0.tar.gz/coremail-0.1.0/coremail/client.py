"""
Coremail API Client
"""
import os
import time
import requests
from typing import Optional, Dict, Any
from cachetools import TTLCache
from dotenv import load_dotenv
from .typings import (
    TokenResponse, AuthenticateResponse, GetAttrsResponse, ChangeAttrsResponse, 
    CreateResponse, DeleteResponse, ListResponse, ListDomainsResponse, 
    GetDomainAttrsResponse, ChangeDomainAttrsResponse, AdminResponse,
    LogResponse, SearchResponse, GroupResponse, SystemConfigResponse,
    UserExistResponse
)

# Load environment variables
load_dotenv()

class CoremailClient:
    """
    Coremail API Client for authentication and token management.
    """
    
    def __init__(self, base_url: Optional[str] = None, app_id: Optional[str] = None, secret: Optional[str] = None):
        """
        Initialize the Coremail client.
        
        :param base_url: Base URL for the Coremail API
        :param app_id: Application ID for authentication
        :param secret: Secret key for authentication
        """
        self.base_url = base_url or os.getenv('COREMAIL_BASE_URL', 'http://mail.ynu.edu.cn:9900/apiws/v3')
        self.app_id = app_id or os.getenv('COREMAIL_APP_ID')
        self.secret = secret or os.getenv('COREMAIL_SECRET')
        self.session = requests.Session()
        
        # Use TTLCache for token caching (1 hour = 3600 seconds)
        self.token_cache: TTLCache = TTLCache(maxsize=1, ttl=3600)
        
        # Set default headers
        self.session.headers.update({
            'Content-Type': 'application/json'
        })
    
    def requestToken(self) -> str:
        """
        Request a new authentication token.
        
        :return: Authentication token
        """
        # Check if we have a valid cached token
        if 'token' in self.token_cache:
            return self.token_cache['token']
        
        url = f"{self.base_url}/requestToken"
        
        payload = {
            "app_id": self.app_id,
            "secret": self.secret
        }
        
        response = self.session.post(url, json=payload)
        response.raise_for_status()
        
        result: TokenResponse = response.json()
        
        if result.get('code') != 0:
            raise Exception(f"API Error: {result.get('message', 'Unknown error')}")
        
        # Extract token from result - the API returns a space-separated string
        token_data = result.get('result', '')
        if isinstance(token_data, str):
            token = token_data
        else:
            token = f"{token_data.get('token', '')} {token_data.get('hash', '')}".strip()
        
        # Cache the token
        self.token_cache['token'] = token
        
        return token
    
    def authenticate(self, user_at_domain: str, password: str = "") -> AuthenticateResponse:
        """
        Authenticate a user.
        
        :param user_at_domain: User identifier in format "user@domain"
        :param password: User password
        :return: Authentication result
        """
        # Ensure we have a valid token (this will refresh if needed)
        token = self.requestToken()
        
        url = f"{self.base_url}/authenticate"
        
        payload = {
            "_token": token,
            "user_at_domain": user_at_domain,
            "password": password
        }
        
        response = self.session.post(url, json=payload)
        response.raise_for_status()
        
        result: AuthenticateResponse = response.json()
        
        # Check for API errors
        if result.get('code') != 0:
            raise Exception(f"API Error: {result.get('message', 'Unknown error')}")
        
        return result
    
    def getAttrs(self, user_at_domain: str, attrs: Optional[Dict[str, Any]] = None) -> GetAttrsResponse:
        """
        Get user attributes.
        
        :param user_at_domain: User identifier in format "user@domain"
        :param attrs: Dictionary of attributes to retrieve (default: all)
        :return: User attributes
        """
        # Ensure we have a valid token (this will refresh if needed)
        token = self.requestToken()
        
        url = f"{self.base_url}/getAttrs"
        
        payload = {
            "_token": token,
            "user_at_domain": user_at_domain,
            "attrs": attrs or {
                "user_id": None,
                "user_name": None,
                "domain_name": None,
                "alias": None,
                "password": None,
                "password_expired": None,
                "password_change_date": None,
                "password_change_cycle": None,
                "password_change_next_time": None,
                "password_lock_date": None,
                "password_lock_cycle": None,
                "password_lock_next_time": None,
                "password_lock_time": None,
                "password_lock_count": None,
                "password_lock_interval": None,
                "password_lock_admin": None,
                "password_lock_enabled": None,
                "quota_mb": None,
                "quota_used_mb": None,
                "quota_used_percent": None,
                "mailsize_limit_mb": None,
                "receive_size_limit_mb": None,
                "send_size_limit_mb": None,
                "receive_limit_count": None,
                "send_limit_count": None,
                "receive_limit_cycle": None,
                "send_limit_cycle": None,
                "receive_limit_enabled": None,
                "send_limit_enabled": None,
                "receive_limit_time": None,
                "send_limit_time": None,
                "receive_limit_exception": None,
                "send_limit_exception": None,
                "receive_limit_white_list": None,
                "send_limit_white_list": None,
                "receive_limit_black_list": None,
                "send_limit_black_list": None,
                "mail_days_keep": None,
                "receive_mail_days_keep": None,
                "send_mail_days_keep": None,
                "receive_mail_days_keep_enabled": None,
                "send_mail_days_keep_enabled": None,
                "forward_type": None,
                "forward_addr": None,
                "forward_backup": None,
                "auto_reply_enabled": None,
                "auto_reply_subject": None,
                "auto_reply_message": None,
                "auto_reply_date_start": None,
                "auto_reply_date_end": None,
                "auto_reply_holidays_enabled": None,
                "auto_reply_holidays_list": None,
                "auto_reply_vacation_enabled": None,
                "auto_reply_vacation_message": None,
                "auto_reply_vacation_date_start": None,
                "auto_reply_vacation_date_end": None,
                "mail_filter_enabled": None,
                "mail_filter_rules": None,
                "mail_filter_white_list": None,
                "mail_filter_black_list": None,
                "user_enabled": None,
                "admin_enabled": None,
                "admin_privileges": None,
                "admin_domains": None,
                "create_date": None,
                "modify_date": None,
                "last_login_date": None,
                "last_login_ip": None,
                "login_count": None,
                "login_fail_count": None,
                "login_fail_date": None,
                "login_fail_ip": None,
                "login_fail_lock": None,
                "login_fail_lock_time": None,
                "login_fail_lock_count": None,
                "login_fail_lock_interval": None,
                "login_fail_lock_admin": None,
                "login_fail_lock_enabled": None
            }
        }
        
        response = self.session.post(url, json=payload)
        response.raise_for_status()
        
        result: GetAttrsResponse = response.json()
        
        # Check for API errors
        if result.get('code') != 0:
            raise Exception(f"API Error: {result.get('message', 'Unknown error')}")
        
        return result
    
    def changeAttrs(self, user_at_domain: str, attrs: Dict[str, Any]) -> ChangeAttrsResponse:
        """
        Change user attributes.
        
        :param user_at_domain: User identifier in format "user@domain"
        :param attrs: Dictionary of attributes to change
        :return: Change result
        """
        # Ensure we have a valid token (this will refresh if needed)
        token = self.requestToken()
        
        url = f"{self.base_url}/changeAttrs"
        
        payload = {
            "_token": token,
            "user_at_domain": user_at_domain,
            "attrs": attrs
        }
        
        response = self.session.post(url, json=payload)
        response.raise_for_status()
        
        result: ChangeAttrsResponse = response.json()
        
        # Check for API errors
        if result.get('code') != 0:
            raise Exception(f"API Error: {result.get('message', 'Unknown error')}")
        
        return result

    def create(self, user_at_domain: str, attrs: Dict[str, Any]) -> CreateResponse:
        """
        Create a new user.
        
        :param user_at_domain: User identifier in format "user@domain"
        :param attrs: Dictionary of attributes for the new user
        :return: Creation result
        """
        # Ensure we have a valid token (this will refresh if needed)
        token = self.requestToken()
        
        url = f"{self.base_url}/create"
        
        payload = {
            "_token": token,
            "user_at_domain": user_at_domain,
            "attrs": attrs
        }
        
        response = self.session.post(url, json=payload)
        response.raise_for_status()
        
        result: CreateResponse = response.json()
        
        # Check for API errors
        if result.get('code') != 0:
            raise Exception(f"API Error: {result.get('message', 'Unknown error')}")
        
        return result

    def delete(self, user_at_domain: str) -> DeleteResponse:
        """
        Delete a user.
        
        :param user_at_domain: User identifier in format "user@domain"
        :return: Deletion result
        """
        # Ensure we have a valid token (this will refresh if needed)
        token = self.requestToken()
        
        url = f"{self.base_url}/delete"
        
        payload = {
            "_token": token,
            "user_at_domain": user_at_domain
        }
        
        response = self.session.post(url, json=payload)
        response.raise_for_status()
        
        result: DeleteResponse = response.json()
        
        # Check for API errors
        if result.get('code') != 0:
            raise Exception(f"API Error: {result.get('message', 'Unknown error')}")
        
        return result

    def list_users(self, domain: Optional[str] = None, attrs: Optional[Dict[str, Any]] = None) -> ListResponse:
        """
        List users in the system or in a specific domain.
        
        :param domain: Optional domain to filter users
        :param attrs: Optional attributes to filter or retrieve
        :return: List of users result
        """
        # Ensure we have a valid token (this will refresh if needed)
        token = self.requestToken()
        
        url = f"{self.base_url}/list"
        
        payload: Dict[str, Any] = {
            "_token": token
        }
        
        if domain:
            payload["domain"] = domain
            
        if attrs:
            payload["attrs"] = attrs
        else:
            # Default attributes to retrieve
            payload["attrs"] = {
                "user_id": None,
                "user_name": None,
                "domain_name": None,
                "quota_mb": None,
                "user_enabled": None,
                "create_date": None
            }
        
        response = self.session.post(url, json=payload)
        response.raise_for_status()
        
        result: ListResponse = response.json()
        
        # Check for API errors
        if result.get('code') != 0:
            raise Exception(f"API Error: {result.get('message', 'Unknown error')}")
        
        return result

    def listDomains(self, attrs: Optional[Dict[str, Any]] = None) -> ListDomainsResponse:
        """
        List domains in the system.
        
        :param attrs: Optional attributes to filter or retrieve
        :return: List of domains result
        """
        # Ensure we have a valid token (this will refresh if needed)
        token = self.requestToken()
        
        url = f"{self.base_url}/listDomains"
        
        payload: Dict[str, Any] = {
            "_token": token
        }
        
        if attrs:
            payload["attrs"] = attrs
        else:
            # Default attributes to retrieve
            payload["attrs"] = {
                "domain_name": None,
                "domain_alias": None,
                "quota_mb": None,
                "user_count": None,
                "enabled": None,
                "create_date": None
            }
        
        response = self.session.post(url, json=payload)
        response.raise_for_status()
        
        result: ListDomainsResponse = response.json()
        
        # Check for API errors
        if result.get('code') != 0:
            raise Exception(f"API Error: {result.get('message', 'Unknown error')}")
        
        return result

    def getDomainAttrs(self, domain_name: str, attrs: Optional[Dict[str, Any]] = None) -> GetDomainAttrsResponse:
        """
        Get domain attributes.
        
        :param domain_name: Domain name
        :param attrs: Dictionary of attributes to retrieve (default: all)
        :return: Domain attributes
        """
        # Ensure we have a valid token (this will refresh if needed)
        token = self.requestToken()
        
        url = f"{self.base_url}/getDomainAttrs"
        
        payload: Dict[str, Any] = {
            "_token": token,
            "domain_name": domain_name,
            "attrs": attrs or {
                "domain_name": None,
                "domain_alias": None,
                "quota_mb": None,
                "max_users": None,
                "user_count": None,
                "enabled": None,
                "create_date": None,
                "modify_date": None,
                "mail_size_limit_mb": None,
                "receive_size_limit_mb": None,
                "send_size_limit_mb": None,
                "receive_limit_count": None,
                "send_limit_count": None,
                "receive_limit_cycle": None,
                "send_limit_cycle": None,
                "receive_limit_enabled": None,
                "send_limit_enabled": None,
                "admin_user_id": None,
                "admin_email": None,
                "description": None
            }
        }
        
        response = self.session.post(url, json=payload)
        response.raise_for_status()
        
        result: GetDomainAttrsResponse = response.json()
        
        # Check for API errors
        if result.get('code') != 0:
            raise Exception(f"API Error: {result.get('message', 'Unknown error')}")
        
        return result

    def changeDomainAttrs(self, domain_name: str, attrs: Dict[str, Any]) -> ChangeDomainAttrsResponse:
        """
        Change domain attributes.
        
        :param domain_name: Domain name
        :param attrs: Dictionary of attributes to change
        :return: Change result
        """
        # Ensure we have a valid token (this will refresh if needed)
        token = self.requestToken()
        
        url = f"{self.base_url}/changeDomainAttrs"
        
        payload = {
            "_token": token,
            "domain_name": domain_name,
            "attrs": attrs
        }
        
        response = self.session.post(url, json=payload)
        response.raise_for_status()
        
        result: ChangeDomainAttrsResponse = response.json()
        
        # Check for API errors
        if result.get('code') != 0:
            raise Exception(f"API Error: {result.get('message', 'Unknown error')}")
        
        return result

    def admin(self, operation: str, params: Optional[Dict[str, Any]] = None) -> AdminResponse:
        """
        Perform administrative operations.
        
        :param operation: The admin operation to perform
        :param params: Parameters for the operation
        :return: Operation result
        """
        # Ensure we have a valid token (this will refresh if needed)
        token = self.requestToken()
        
        url = f"{self.base_url}/admin"
        
        payload: Dict[str, Any] = {
            "_token": token,
            "operation": operation
        }
        
        if params:
            payload["params"] = params
        
        response = self.session.post(url, json=payload)
        response.raise_for_status()
        
        result: AdminResponse = response.json()
        
        # Check for API errors
        if result.get('code') != 0:
            raise Exception(f"API Error: {result.get('message', 'Unknown error')}")
        
        return result

    def search(self, user_at_domain: str, search_params: Dict[str, Any]) -> SearchResponse:
        """
        Search messages for a user.
        
        :param user_at_domain: User identifier in format "user@domain"
        :param search_params: Search parameters
        :return: Search result
        """
        # Ensure we have a valid token (this will refresh if needed)
        token = self.requestToken()
        
        url = f"{self.base_url}/search"
        
        payload = {
            "_token": token,
            "user_at_domain": user_at_domain,
            "params": search_params
        }
        
        response = self.session.post(url, json=payload)
        response.raise_for_status()
        
        result: SearchResponse = response.json()
        
        # Check for API errors
        if result.get('code') != 0:
            raise Exception(f"API Error: {result.get('message', 'Unknown error')}")
        
        return result

    def get_logs(self, log_type: str, start_time: Optional[str] = None, end_time: Optional[str] = None, 
                limit: Optional[int] = None) -> LogResponse:
        """
        Get system logs.
        
        :param log_type: Type of logs to retrieve (e.g., 'login', 'operation', 'error')
        :param start_time: Start time for log search (ISO format)
        :param end_time: End time for log search (ISO format)
        :param limit: Maximum number of logs to return
        :return: Log entries
        """
        # Ensure we have a valid token (this will refresh if needed)
        token = self.requestToken()
        
        url = f"{self.base_url}/getLogs"
        
        payload: Dict[str, Any] = {
            "_token": token,
            "log_type": log_type
        }
        
        if start_time:
            payload["start_time"] = start_time
        if end_time:
            payload["end_time"] = end_time
        if limit:
            payload["limit"] = limit
        
        response = self.session.post(url, json=payload)
        response.raise_for_status()
        
        result: LogResponse = response.json()
        
        # Check for API errors
        if result.get('code') != 0:
            raise Exception(f"API Error: {result.get('message', 'Unknown error')}")
        
        return result

    def manage_group(self, operation: str, group_name: str, user_at_domain: Optional[str] = None) -> GroupResponse:
        """
        Manage groups (add/remove users, etc.).
        
        :param operation: Group operation ('add', 'remove', 'create', 'delete', 'list')
        :param group_name: Name of the group
        :param user_at_domain: User to add/remove from the group
        :return: Operation result
        """
        # Ensure we have a valid token (this will refresh if needed)
        token = self.requestToken()
        
        url = f"{self.base_url}/manageGroup"
        
        payload: Dict[str, Any] = {
            "_token": token,
            "operation": operation,
            "group_name": group_name
        }
        
        if user_at_domain:
            payload["user_at_domain"] = user_at_domain
        
        response = self.session.post(url, json=payload)
        response.raise_for_status()
        
        result: GroupResponse = response.json()
        
        # Check for API errors
        if result.get('code') != 0:
            raise Exception(f"API Error: {result.get('message', 'Unknown error')}")
        
        return result

    def get_system_config(self, config_type: Optional[str] = None) -> SystemConfigResponse:
        """
        Get system configuration.
        
        :param config_type: Specific configuration type to retrieve (optional)
        :return: System configuration
        """
        # Ensure we have a valid token (this will refresh if needed)
        token = self.requestToken()
        
        url = f"{self.base_url}/getSystemConfig"
        
        payload: Dict[str, Any] = {
            "_token": token
        }
        
        if config_type:
            payload["config_type"] = config_type
        
        response = self.session.post(url, json=payload)
        response.raise_for_status()
        
        result: SystemConfigResponse = response.json()
        
        # Check for API errors
        if result.get('code') != 0:
            raise Exception(f"API Error: {result.get('message', 'Unknown error')}")
        
        return result

    def userExist(self, user_at_domain: str) -> UserExistResponse:
        """
        Check if a user exists.
        
        :param user_at_domain: User identifier in format "user@domain"
        :return: Boolean result indicating if user exists
        """
        # Ensure we have a valid token (this will refresh if needed)
        token = self.requestToken()
        
        url = f"{self.base_url}/userExist"
        
        payload: Dict[str, Any] = {
            "_token": token,
            "user_at_domain": user_at_domain
        }
        
        response = self.session.post(url, json=payload)
        response.raise_for_status()
        
        result: UserExistResponse = response.json()
        
        # Check for API errors
        if result.get('code') != 0:
            raise Exception(f"API Error: {result.get('message', 'Unknown error')}")
        
        return result

    def refresh_token(self) -> str:
        """
        Refresh the authentication token.
        
        :return: New authentication token
        """
        # Clear the cached token to force a refresh
        self.token_cache.clear()
        return self.requestToken()