"""
Tests for the Digilog client.
"""

import pytest
from unittest.mock import Mock, patch
from digilog import init, log, finish, set_token
from digilog.exceptions import AuthenticationError, ValidationError


class TestDigilogClient:
    """Test cases for the main client interface."""
    
    def test_set_token(self):
        """Test setting authentication token."""
        set_token("test-token")
        # This is a simple test to ensure the function doesn't raise an error
        assert True
    
    def test_init_without_token(self):
        """Test that init raises AuthenticationError without token."""
        with pytest.raises(AuthenticationError):
            init(project="test-project")
    
    def test_init_without_project(self):
        """Test that init raises ValidationError without project."""
        with pytest.raises(ValidationError):
            init(project="")
    
    def test_log_without_run(self):
        """Test that log raises ValidationError without active run."""
        with pytest.raises(ValidationError):
            log({"test": 1.0})
    
    def test_finish_without_run(self):
        """Test that finish raises ValidationError without active run."""
        with pytest.raises(ValidationError):
            finish()


class TestConfig:
    """Test cases for the Config class."""
    
    def test_config_creation(self):
        """Test Config object creation."""
        from digilog.config import Config
        
        config = Config({"test": "value"})
        assert config["test"] == "value"
        assert config.test == "value"
    
    def test_config_update(self):
        """Test Config update method."""
        from digilog.config import Config
        
        config = Config()
        config.update({"key1": "value1", "key2": "value2"})
        assert config["key1"] == "value1"
        assert config["key2"] == "value2"
    
    def test_config_freeze(self):
        """Test Config freeze functionality."""
        from digilog.config import Config
        from digilog.exceptions import ValidationError
        
        config = Config({"test": "value"})
        config.freeze()
        
        with pytest.raises(ValidationError):
            config["new_key"] = "new_value"


class TestExceptions:
    """Test cases for custom exceptions."""
    
    def test_digilog_error(self):
        """Test DigilogError base exception."""
        from digilog.exceptions import DigilogError
        
        error = DigilogError("Test error")
        assert str(error) == "Test error"
    
    def test_api_error(self):
        """Test APIError with status code."""
        from digilog.exceptions import APIError
        
        error = APIError("API error", 404)
        assert error.status_code == 404
        assert str(error) == "API error" 