"""
Coremail API wrapper providing higher-level functionality
"""
from typing import Optional, Dict, Any
from ..client import CoremailClient  # Use relative import to avoid circular import
from ..typings import (
    GetAttrsResponse, ChangeAttrsResponse, CreateResponse, DeleteResponse, 
    ListResponse, ListDomainsResponse, GetDomainAttrsResponse, 
    ChangeDomainAttrsResponse, AdminResponse, LogResponse, SearchResponse, 
    GroupResponse, SystemConfigResponse, UserExistResponse
)


class CoremailAPI:
    """
    Higher-level API wrapper for Coremail operations
    """
    
    def __init__(self, client: CoremailClient):
        """
        Initialize the API wrapper.
        
        :param client: CoremailClient instance
        """
        self.client = client
    
    def get_user_info(self, user_at_domain: str) -> GetAttrsResponse:
        """
        Get complete user information.
        
        :param user_at_domain: User identifier in format "user@domain"
        :return: User information dictionary
        """
        result = self.client.getAttrs(user_at_domain)
        return result
    
    def change_user_attributes(self, user_at_domain: str, attrs: Dict[str, Any]) -> ChangeAttrsResponse:
        """
        Change user attributes.
        
        :param user_at_domain: User identifier in format "user@domain"
        :param attrs: Dictionary of attributes to change
        :return: Change result
        """
        return self.client.changeAttrs(user_at_domain, attrs)

    def create_user(self, user_at_domain: str, attrs: Dict[str, Any]) -> CreateResponse:
        """
        Create a new user.
        
        :param user_at_domain: User identifier in format "user@domain"
        :param attrs: Dictionary of attributes for the new user
        :return: Creation result
        """
        try:
            return self.client.create(user_at_domain, attrs)
        except Exception:
            raise

    def delete_user(self, user_at_domain: str) -> DeleteResponse:
        """
        Delete a user.
        
        :param user_at_domain: User identifier in format "user@domain"
        :return: Deletion result
        """
        try:
            return self.client.delete(user_at_domain)
        except Exception:
            raise

    def list_users(self, domain: Optional[str] = None, attrs: Optional[Dict[str, Any]] = None) -> ListResponse:
        """
        List users in the system or in a specific domain.
        
        :param domain: Optional domain to filter users
        :param attrs: Optional attributes to filter or retrieve
        :return: List of users result
        """
        try:
            return self.client.list_users(domain, attrs)
        except Exception:
            raise

    def list_domains(self, attrs: Optional[Dict[str, Any]] = None) -> ListDomainsResponse:
        """
        List domains in the system.
        
        :param attrs: Optional attributes to filter or retrieve
        :return: List of domains result
        """
        try:
            return self.client.listDomains(attrs)
        except Exception:
            raise

    def get_domain_info(self, domain_name: str, attrs: Optional[Dict[str, Any]] = None) -> GetDomainAttrsResponse:
        """
        Get domain information.
        
        :param domain_name: Domain name
        :param attrs: Optional attributes to retrieve
        :return: Domain information
        """
        try:
            return self.client.getDomainAttrs(domain_name, attrs)
        except Exception:
            raise

    def change_domain_attributes(self, domain_name: str, attrs: Dict[str, Any]) -> ChangeDomainAttrsResponse:
        """
        Change domain attributes.
        
        :param domain_name: Domain name
        :param attrs: Dictionary of attributes to change
        :return: Change result
        """
        try:
            return self.client.changeDomainAttrs(domain_name, attrs)
        except Exception:
            raise

    def admin_operation(self, operation: str, params: Optional[Dict[str, Any]] = None) -> AdminResponse:
        """
        Perform administrative operations.
        
        :param operation: The admin operation to perform
        :param params: Parameters for the operation
        :return: Operation result
        """
        try:
            return self.client.admin(operation, params)
        except Exception:
            raise

    def search_messages(self, user_at_domain: str, search_params: Dict[str, Any]) -> SearchResponse:
        """
        Search messages for a user.
        
        :param user_at_domain: User identifier in format "user@domain"
        :param search_params: Search parameters
        :return: Search result
        """
        try:
            return self.client.search(user_at_domain, search_params)
        except Exception:
            raise

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
        try:
            return self.client.get_logs(log_type, start_time, end_time, limit)
        except Exception:
            raise

    def manage_group(self, operation: str, group_name: str, user_at_domain: Optional[str] = None) -> GroupResponse:
        """
        Manage groups (add/remove users, etc.).
        
        :param operation: Group operation ('add', 'remove', 'create', 'delete', 'list')
        :param group_name: Name of the group
        :param user_at_domain: User to add/remove from the group
        :return: Operation result
        """
        try:
            return self.client.manage_group(operation, group_name, user_at_domain)
        except Exception:
            raise

    def get_system_config(self, config_type: Optional[str] = None) -> SystemConfigResponse:
        """
        Get system configuration.
        
        :param config_type: Specific configuration type to retrieve (optional)
        :return: System configuration
        """
        try:
            return self.client.get_system_config(config_type)
        except Exception:
            raise

    def user_exists(self, user_at_domain: str) -> bool:
        """
        Check if a user exists.
        
        :param user_at_domain: User identifier in format "user@domain"
        :return: Boolean indicating if user exists
        """
        try:
            result = self.client.userExist(user_at_domain)
            return result.get('result', False)
        except Exception:
            return False
    
    def authenticate_user(self, user_at_domain: str, password: str = "") -> bool:
        """
        Authenticate a user and return success status.
        
        :param user_at_domain: User identifier in format "user@domain"
        :param password: User password
        :return: True if authentication successful, False otherwise
        """
        try:
            result = self.client.authenticate(user_at_domain, password)
            return result.get('code') == 0
        except Exception:
            return False
    
    def check_user_exists(self, user_at_domain: str) -> bool:
        """
        Check if a user exists by attempting to get their attributes.
        
        :param user_at_domain: User identifier in format "user@domain"
        :return: True if user exists, False otherwise
        """
        try:
            result = self.client.getAttrs(user_at_domain)
            return result.get('code') == 0
        except Exception:
            return False