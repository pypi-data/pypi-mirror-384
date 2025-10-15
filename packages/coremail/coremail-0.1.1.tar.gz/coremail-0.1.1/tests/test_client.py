"""
Unit tests for Coremail SDK - Client only
"""
import os
import pytest
import responses
from coremail import CoremailClient

# Global test constants
TEST_BASE_URL = "http://test-coremail.com/apiws/v3"
TEST_APP_ID = "test_app@test-domain.com"
TEST_SECRET = "test_secret"
TEST_USER = "test_user@test-domain.com"
TEST_USER2 = "test_user2@test-domain.com"
TEST_DOMAIN = "test-domain.com"


class TestCoremailClient:
    """Test cases for the CoremailClient class"""
    
    @pytest.fixture
    def client(self):
        """Create a test client instance"""
        return CoremailClient(
            base_url=TEST_BASE_URL,
            app_id=TEST_APP_ID,
            secret=TEST_SECRET
        )
    
    @responses.activate
    def test_requestToken(self, client):
        """Test requesting a token"""
        # Mock the API response
        responses.add(
            responses.POST,
            f"{TEST_BASE_URL}/requestToken",
            json={"code": 0, "result": "test_token_hash"},
            status=200
        )
        
        token = client.requestToken()
        
        assert token == "test_token_hash"
    
    @responses.activate
    def test_getAttrs(self, client):
        """Test getting user attributes"""
        # First, mock the token request
        responses.add(
            responses.POST,
            f"{TEST_BASE_URL}/requestToken",
            json={"code": 0, "result": "test_token_hash"},
            status=200
        )
        
        # Then, mock the getAttrs request
        responses.add(
            responses.POST,
            f"{TEST_BASE_URL}/getAttrs",
            json={
                "code": 0,
                "result": {
                    "user_id": "test_user",
                    "domain_name": TEST_DOMAIN,
                    "password": "{enc8}encrypted_password"
                }
            },
            status=200
        )
        
        result = client.getAttrs(TEST_USER)
        
        assert result["code"] == 0
        assert result["result"]["user_id"] == "test_user"
    
    @responses.activate
    def test_authenticate(self, client):
        """Test user authentication"""
        # First, mock the token request
        responses.add(
            responses.POST,
            f"{TEST_BASE_URL}/requestToken",
            json={"code": 0, "result": "test_token_hash"},
            status=200
        )
        
        # Then, mock the authenticate request
        responses.add(
            responses.POST,
            f"{TEST_BASE_URL}/authenticate",
            json={"code": 0, "message": None},
            status=200
        )
        
        result = client.authenticate(TEST_USER, "password")
        
        assert result["code"] == 0

    @responses.activate
    def test_changeAttrs(self, client):
        """Test changing user attributes"""
        # First, mock the token request
        responses.add(
            responses.POST,
            f"{TEST_BASE_URL}/requestToken",
            json={"code": 0, "result": "test_token_hash"},
            status=200
        )
        
        # Then, mock the changeAttrs request
        responses.add(
            responses.POST,
            f"{TEST_BASE_URL}/changeAttrs",
            json={"code": 0},
            status=200
        )
        
        result = client.changeAttrs(TEST_USER, {"password": "new_password"})
        
        assert result["code"] == 0

    @responses.activate
    def test_userExist(self, client):
        """Test checking if a user exists"""
        # First, mock the token request
        responses.add(
            responses.POST,
            f"{TEST_BASE_URL}/requestToken",
            json={"code": 0, "result": "test_token_hash"},
            status=200
        )
        
        # Then, mock the userExist request
        responses.add(
            responses.POST,
            f"{TEST_BASE_URL}/userExist",
            json={"code": 0, "result": True},
            status=200
        )
        
        result = client.userExist(TEST_USER)
        
        assert result["code"] == 0
        assert result["result"] is True

    @responses.activate
    def test_create(self, client):
        """Test creating a user"""
        # First, mock the token request
        responses.add(
            responses.POST,
            f"{TEST_BASE_URL}/requestToken",
            json={"code": 0, "result": "test_token_hash"},
            status=200
        )
        
        # Then, mock the create request
        responses.add(
            responses.POST,
            f"{TEST_BASE_URL}/create",
            json={"code": 0},
            status=200
        )
        
        result = client.create(TEST_USER, {"password": "initial_password", "quota_mb": 1024})
        
        assert result["code"] == 0

    @responses.activate
    def test_delete(self, client):
        """Test deleting a user"""
        # First, mock the token request
        responses.add(
            responses.POST,
            f"{TEST_BASE_URL}/requestToken",
            json={"code": 0, "result": "test_token_hash"},
            status=200
        )
        
        # Then, mock the delete request
        responses.add(
            responses.POST,
            f"{TEST_BASE_URL}/delete",
            json={"code": 0},
            status=200
        )
        
        result = client.delete(TEST_USER)
        
        assert result["code"] == 0

    @responses.activate
    def test_list_users(self, client):
        """Test listing users"""
        # First, mock the token request
        responses.add(
            responses.POST,
            f"{TEST_BASE_URL}/requestToken",
            json={"code": 0, "result": "test_token_hash"},
            status=200
        )
        
        # Then, mock the list request
        responses.add(
            responses.POST,
            f"{TEST_BASE_URL}/list",
            json={"code": 0, "result": {"users": [TEST_USER]}},
            status=200
        )
        
        result = client.list_users(domain=TEST_DOMAIN)
        
        assert result["code"] == 0
        assert "users" in result["result"]

    @responses.activate
    def test_listDomains(self, client):
        """Test listing domains"""
        # First, mock the token request
        responses.add(
            responses.POST,
            f"{TEST_BASE_URL}/requestToken",
            json={"code": 0, "result": "test_token_hash"},
            status=200
        )
        
        # Then, mock the listDomains request
        responses.add(
            responses.POST,
            f"{TEST_BASE_URL}/listDomains",
            json={"code": 0, "result": {"domains": [TEST_DOMAIN]}},
            status=200
        )
        
        result = client.listDomains()
        
        assert result["code"] == 0
        assert "domains" in result["result"]

    @responses.activate
    def test_getDomainAttrs(self, client):
        """Test getting domain attributes"""
        # First, mock the token request
        responses.add(
            responses.POST,
            f"{TEST_BASE_URL}/requestToken",
            json={"code": 0, "result": "test_token_hash"},
            status=200
        )
        
        # Then, mock the getDomainAttrs request
        responses.add(
            responses.POST,
            f"{TEST_BASE_URL}/getDomainAttrs",
            json={
                "code": 0,
                "result": {
                    "domain_name": TEST_DOMAIN,
                    "quota_mb": 1024000,
                    "enabled": True
                }
            },
            status=200
        )
        
        result = client.getDomainAttrs(TEST_DOMAIN)
        
        assert result["code"] == 0
        assert result["result"]["domain_name"] == TEST_DOMAIN

    @responses.activate
    def test_changeDomainAttrs(self, client):
        """Test changing domain attributes"""
        # First, mock the token request
        responses.add(
            responses.POST,
            f"{TEST_BASE_URL}/requestToken",
            json={"code": 0, "result": "test_token_hash"},
            status=200
        )
        
        # Then, mock the changeDomainAttrs request
        responses.add(
            responses.POST,
            f"{TEST_BASE_URL}/changeDomainAttrs",
            json={"code": 0},
            status=200
        )
        
        result = client.changeDomainAttrs(TEST_DOMAIN, {"quota_mb": 2048000})
        
        assert result["code"] == 0

    @responses.activate
    def test_search(self, client):
        """Test searching messages"""
        # First, mock the token request
        responses.add(
            responses.POST,
            f"{TEST_BASE_URL}/requestToken",
            json={"code": 0, "result": "test_token_hash"},
            status=200
        )
        
        # Then, mock the search request
        responses.add(
            responses.POST,
            f"{TEST_BASE_URL}/search",
            json={"code": 0, "result": {"messages": []}},
            status=200
        )
        
        result = client.search(TEST_USER, {"keyword": "test"})
        
        assert result["code"] == 0

    @responses.activate
    def test_get_logs(self, client):
        """Test getting logs"""
        # First, mock the token request
        responses.add(
            responses.POST,
            f"{TEST_BASE_URL}/requestToken",
            json={"code": 0, "result": "test_token_hash"},
            status=200
        )
        
        # Then, mock the getLogs request
        responses.add(
            responses.POST,
            f"{TEST_BASE_URL}/getLogs",
            json={"code": 0, "result": {"logs": []}},
            status=200
        )
        
        result = client.get_logs("login")
        
        assert result["code"] == 0

    @responses.activate
    def test_manage_group(self, client):
        """Test managing groups"""
        # First, mock the token request
        responses.add(
            responses.POST,
            f"{TEST_BASE_URL}/requestToken",
            json={"code": 0, "result": "test_token_hash"},
            status=200
        )
        
        # Then, mock the manageGroup request
        responses.add(
            responses.POST,
            f"{TEST_BASE_URL}/manageGroup",
            json={"code": 0},
            status=200
        )
        
        result = client.manage_group("add", "test_group", TEST_USER)
        
        assert result["code"] == 0

    @responses.activate
    def test_get_system_config(self, client):
        """Test getting system config"""
        # First, mock the token request
        responses.add(
            responses.POST,
            f"{TEST_BASE_URL}/requestToken",
            json={"code": 0, "result": "test_token_hash"},
            status=200
        )
        
        # Then, mock the getSystemConfig request
        responses.add(
            responses.POST,
            f"{TEST_BASE_URL}/getSystemConfig",
            json={"code": 0, "result": {"config": {}}},
            status=200
        )
        
        result = client.get_system_config()
        
        assert result["code"] == 0

    @responses.activate
    def test_admin(self, client):
        """Test admin operation"""
        # First, mock the token request
        responses.add(
            responses.POST,
            f"{TEST_BASE_URL}/requestToken",
            json={"code": 0, "result": "test_token_hash"},
            status=200
        )
        
        # Then, mock the admin request
        responses.add(
            responses.POST,
            f"{TEST_BASE_URL}/admin",
            json={"code": 0},
            status=200
        )
        
        result = client.admin("status_check")
        
        assert result["code"] == 0

