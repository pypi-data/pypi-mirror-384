"""Tests for authentication and token handling."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
from tvDatafeed import TvDatafeed


class TestTokenCaching:
    """Test token caching functionality."""

    def test_load_valid_token_from_cache(self, tmp_path, mock_token):
        """Test loading a valid token from cache."""
        token_file = tmp_path / ".tv_token.json"
        token_file.write_text(json.dumps({"token": mock_token}))

        with patch('tvDatafeed.main.TvDatafeed._is_token_valid', return_value=True):
            tv = TvDatafeed(token_cache_file=token_file)
            assert tv.token == mock_token

    def test_expired_token_removed_from_cache(self, tmp_path, mock_expired_token):
        """Test that expired tokens are removed from cache."""
        token_file = tmp_path / ".tv_token.json"
        token_file.write_text(json.dumps({"token": mock_expired_token}))

        tv = TvDatafeed(token_cache_file=token_file)
        assert tv.token is None
        assert not token_file.exists()

    def test_no_cache_file_anonymous_access(self, tmp_path):
        """Test anonymous access when no cache file exists."""
        token_file = tmp_path / "nonexistent.json"
        tv = TvDatafeed(token_cache_file=token_file)
        assert tv.token is None

    def test_save_token_after_login(self, tmp_path, mock_requests_post):
        """Test that token is saved after successful login."""
        token_file = tmp_path / ".tv_token.json"
        
        with patch('tvDatafeed.main.TvDatafeed._is_token_valid', return_value=True):
            tv = TvDatafeed(
                username="testuser",
                password="testpass",
                token_cache_file=token_file
            )
            
            assert token_file.exists()
            data = json.loads(token_file.read_text())
            assert "token" in data
            assert data["token"] == "test_token_123"


class TestTokenValidation:
    """Test JWT token validation."""

    def test_valid_token_jwt_validation(self, mock_token):
        """Test that a valid JWT token passes validation."""
        tv = TvDatafeed()
        assert tv._is_token_valid(mock_token) is True

    def test_expired_token_jwt_validation(self, mock_expired_token):
        """Test that an expired JWT token fails validation."""
        tv = TvDatafeed()
        assert tv._is_token_valid(mock_expired_token) is False

    def test_invalid_token_format(self):
        """Test that invalid token format fails validation."""
        tv = TvDatafeed()
        assert tv._is_token_valid("invalid_token") is False
        assert tv._is_token_valid("not.a.jwt") is False
        assert tv._is_token_valid("") is False

    def test_token_without_expiration(self):
        """Test token without expiration claim fails validation."""
        # JWT without exp claim
        token = "eyJhbGciOiJSUzUxMiJ9.eyJ1c2VyX2lkIjoxMjM0NX0.signature"
        tv = TvDatafeed()
        assert tv._is_token_valid(token) is False


class TestAuthentication:
    """Test authentication flow."""

    def test_successful_login(self, mock_requests_post, tmp_path):
        """Test successful login with username and password."""
        token_file = tmp_path / ".tv_token.json"
        
        with patch('tvDatafeed.main.TvDatafeed._is_token_valid', return_value=True):
            tv = TvDatafeed(
                username="testuser",
                password="testpass",
                token_cache_file=token_file
            )
            
            assert tv.token == "test_token_123"
            mock_requests_post.assert_called_once()

    def test_failed_login_no_auth_token(self, tmp_path):
        """Test failed login when no auth_token in response."""
        response = Mock()
        response.status_code = 200
        response.json.return_value = {"user": {"username": "test"}}
        
        with patch('tvDatafeed.main.requests.post', return_value=response):
            with patch('tvDatafeed.main.TvDatafeed._handle_captcha_login', return_value=None):
                with pytest.raises(ValueError, match="Login failed"):
                    TvDatafeed(
                        username="testuser",
                        password="testpass",
                        token_cache_file=tmp_path / ".tv_token.json"
                    )

    def test_anonymous_access_no_credentials(self):
        """Test anonymous access without credentials."""
        tv = TvDatafeed()
        assert tv.token is None

    def test_get_token_method(self, mock_token, tmp_path):
        """Test get_token() method."""
        token_file = tmp_path / ".tv_token.json"
        token_file.write_text(json.dumps({"token": mock_token}))
        
        with patch('tvDatafeed.main.TvDatafeed._is_token_valid', return_value=True):
            tv = TvDatafeed(token_cache_file=token_file)
            assert tv.get_token() == mock_token


class TestCaptchaHandling:
    """Test CAPTCHA detection and handling."""

    def test_captcha_detected_in_error(self, tmp_path):
        """Test that CAPTCHA error is detected in login response."""
        response = Mock()
        response.status_code = 200
        response.json.return_value = {
            "error": "CAPTCHA verification required"
        }
        
        with patch('tvDatafeed.main.requests.post', return_value=response):
            with patch('tvDatafeed.main.TvDatafeed._handle_captcha_login', return_value="captcha_token") as mock_captcha:
                with patch('tvDatafeed.main.TvDatafeed._is_token_valid', return_value=True):
                    tv = TvDatafeed(
                        username="testuser",
                        password="testpass",
                        token_cache_file=tmp_path / ".tv_token.json"
                    )
                    mock_captcha.assert_called_once()

    def test_captcha_fallback_on_invalid_response(self, tmp_path):
        """Test CAPTCHA fallback when response format is invalid."""
        response = Mock()
        response.status_code = 200
        response.json.return_value = {"status": "failed"}
        
        with patch('tvDatafeed.main.requests.post', return_value=response):
            with patch('tvDatafeed.main.TvDatafeed._handle_captcha_login', return_value="captcha_token") as mock_captcha:
                with patch('tvDatafeed.main.TvDatafeed._is_token_valid', return_value=True):
                    tv = TvDatafeed(
                        username="testuser",
                        password="testpass",
                        token_cache_file=tmp_path / ".tv_token.json"
                    )
                    mock_captcha.assert_called_once()
