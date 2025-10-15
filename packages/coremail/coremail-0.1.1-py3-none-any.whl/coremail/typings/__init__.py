"""
Type definitions for Coremail API responses
"""
from typing import TypedDict, Optional, Dict, Any


class TokenResponse(TypedDict):
    """Response from requestToken API"""
    code: int
    result: str


class AuthenticateResponse(TypedDict):
    """Response from authenticate API"""
    code: int
    message: Optional[str]


class GetAttrsResponse(TypedDict):
    """Response from getAttrs API"""
    code: int
    result: Optional[Dict[str, Any]]


class ChangeAttrsResponse(TypedDict):
    """Response from changeAttrs API"""
    code: int
    message: Optional[str]


class CreateResponse(TypedDict):
    """Response from create API"""
    code: int
    message: Optional[str]


class DeleteResponse(TypedDict):
    """Response from delete API"""
    code: int
    message: Optional[str]


class ListResponse(TypedDict):
    """Response from list API"""
    code: int
    result: Optional[Dict[str, Any]]


class ListDomainsResponse(TypedDict):
    """Response from listDomains API"""
    code: int
    result: Optional[Dict[str, Any]]


class GetDomainAttrsResponse(TypedDict):
    """Response from getDomainAttrs API"""
    code: int
    result: Optional[Dict[str, Any]]


class ChangeDomainAttrsResponse(TypedDict):
    """Response from changeDomainAttrs API"""
    code: int
    message: Optional[str]


class AdminResponse(TypedDict):
    """Response from admin API"""
    code: int
    message: Optional[str]


class MailboxOperationResponse(TypedDict):
    """Response from mailbox operation API"""
    code: int
    message: Optional[str]


class LogResponse(TypedDict):
    """Response from log API"""
    code: int
    result: Optional[Dict[str, Any]]


class SearchResponse(TypedDict):
    """Response from search API"""
    code: int
    result: Optional[Dict[str, Any]]


class GroupResponse(TypedDict):
    """Response from group API"""
    code: int
    message: Optional[str]


class SystemConfigResponse(TypedDict):
    """Response from system config API"""
    code: int
    result: Optional[Dict[str, Any]]


class UserExistResponse(TypedDict):
    """Response from userExist API"""
    code: int
    result: bool


class UserAttributes(TypedDict, total=False):
    """User attributes structure"""
    user_id: Optional[str]
    user_name: Optional[str]
    domain_name: Optional[str]
    alias: Optional[str]
    password: Optional[str]
    password_expired: Optional[bool]
    password_change_date: Optional[str]
    password_change_cycle: Optional[int]
    password_change_next_time: Optional[bool]
    password_lock_date: Optional[str]
    password_lock_cycle: Optional[int]
    password_lock_next_time: Optional[bool]
    password_lock_time: Optional[int]
    password_lock_count: Optional[int]
    password_lock_interval: Optional[int]
    password_lock_admin: Optional[bool]
    password_lock_enabled: Optional[bool]
    quota_mb: Optional[int]
    quota_used_mb: Optional[float]
    quota_used_percent: Optional[float]
    mailsize_limit_mb: Optional[int]
    receive_size_limit_mb: Optional[int]
    send_size_limit_mb: Optional[int]
    receive_limit_count: Optional[int]
    send_limit_count: Optional[int]
    receive_limit_cycle: Optional[str]
    send_limit_cycle: Optional[str]
    receive_limit_enabled: Optional[bool]
    send_limit_enabled: Optional[bool]
    receive_limit_time: Optional[str]
    send_limit_time: Optional[str]
    receive_limit_exception: Optional[str]
    send_limit_exception: Optional[str]
    receive_limit_white_list: Optional[str]
    send_limit_white_list: Optional[str]
    receive_limit_black_list: Optional[str]
    send_limit_black_list: Optional[str]
    mail_days_keep: Optional[int]
    receive_mail_days_keep: Optional[int]
    send_mail_days_keep: Optional[int]
    receive_mail_days_keep_enabled: Optional[bool]
    send_mail_days_keep_enabled: Optional[bool]
    forward_type: Optional[int]
    forward_addr: Optional[str]
    forward_backup: Optional[bool]
    auto_reply_enabled: Optional[bool]
    auto_reply_subject: Optional[str]
    auto_reply_message: Optional[str]
    auto_reply_date_start: Optional[str]
    auto_reply_date_end: Optional[str]
    auto_reply_holidays_enabled: Optional[bool]
    auto_reply_holidays_list: Optional[str]
    auto_reply_vacation_enabled: Optional[bool]
    auto_reply_vacation_message: Optional[str]
    auto_reply_vacation_date_start: Optional[str]
    auto_reply_vacation_date_end: Optional[str]
    mail_filter_enabled: Optional[bool]
    mail_filter_rules: Optional[str]
    mail_filter_white_list: Optional[str]
    mail_filter_black_list: Optional[str]
    user_enabled: Optional[bool]
    admin_enabled: Optional[bool]
    admin_privileges: Optional[str]
    admin_domains: Optional[str]
    create_date: Optional[str]
    modify_date: Optional[str]
    last_login_date: Optional[str]
    last_login_ip: Optional[str]
    login_count: Optional[int]
    login_fail_count: Optional[int]
    login_fail_date: Optional[str]
    login_fail_ip: Optional[str]
    login_fail_lock: Optional[bool]
    login_fail_lock_time: Optional[int]
    login_fail_lock_count: Optional[int]
    login_fail_lock_interval: Optional[int]
    login_fail_lock_admin: Optional[bool]
    login_fail_lock_enabled: Optional[bool]


class CoremailConfig(TypedDict, total=False):
    """Configuration for Coremail client"""
    base_url: str
    app_id: str
    secret: str