"""
Unit tests for Coremail SDK
"""
import os
import pytest
import responses
from coremail import CoremailClient, CoremailAPI

# Global test constants - defined here since importing from conftest can cause issues
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


class TestCoremailAPI:
    """Test cases for the CoremailAPI class"""
    
    @pytest.fixture
    def api(self):
        """Create a test API instance"""
        client = CoremailClient(
            base_url=TEST_BASE_URL,
            app_id=TEST_APP_ID,
            secret=TEST_SECRET
        )
        return CoremailAPI(client)
    
    @responses.activate
    def test_get_user_info(self, api):
        """Test getting user info through the API wrapper"""
        # Mock the token request
        responses.add(
            responses.POST,
            f"{TEST_BASE_URL}/requestToken",
            json={"code": 0, "result": "test_token_hash"},
            status=200
        )
        
        # Mock the getAttrs request
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
        
        user_info = api.get_user_info(TEST_USER)
        
        assert user_info["code"] == 0
        assert user_info["result"]["user_id"] == "test_user"
    
    @responses.activate
    def test_authenticate_user(self, api):
        """Test user authentication through the API wrapper"""
        # Mock the token request
        responses.add(
            responses.POST,
            f"{TEST_BASE_URL}/requestToken",
            json={"code": 0, "result": "test_token_hash"},
            status=200
        )
        
        # Mock the authenticate request for success
        responses.add(
            responses.POST,
            f"{TEST_BASE_URL}/authenticate",
            json={"code": 0, "message": None},
            status=200
        )
        
        # Mock the authenticate request for failure
        responses.add(
            responses.POST,
            f"{TEST_BASE_URL}/authenticate",
            json={"code": 19, "message": "USER_NOT_FOUND"},
            status=200
        )
        
        # Test successful authentication
        is_authenticated = api.authenticate_user(TEST_USER, "password")
        assert is_authenticated is True
        
        # Test failed authentication
        is_authenticated = api.authenticate_user(TEST_USER2, "password")
        assert is_authenticated is False

    @responses.activate
    def test_change_user_attributes(self, api):
        """Test changing user attributes through the API wrapper"""
        # Mock the token request
        responses.add(
            responses.POST,
            f"{TEST_BASE_URL}/requestToken",
            json={"code": 0, "result": "test_token_hash"},
            status=200
        )
        
        # Mock the changeAttrs request
        responses.add(
            responses.POST,
            f"{TEST_BASE_URL}/changeAttrs",
            json={"code": 0},
            status=200
        )
        
        result = api.change_user_attributes(TEST_USER, {"password": "new_password"})
        
        assert result["code"] == 0

    @responses.activate
    def test_user_exists(self, api):
        """Test checking if a user exists via API wrapper"""
        # Mock the token request
        responses.add(
            responses.POST,
            f"{TEST_BASE_URL}/requestToken",
            json={"code": 0, "result": "test_token_hash"},
            status=200
        )
        
        # Mock the userExist request
        responses.add(
            responses.POST,
            f"{TEST_BASE_URL}/userExist",
            json={"code": 0, "result": True},
            status=200
        )
        
        result = api.user_exists(TEST_USER)
        
        assert result is True