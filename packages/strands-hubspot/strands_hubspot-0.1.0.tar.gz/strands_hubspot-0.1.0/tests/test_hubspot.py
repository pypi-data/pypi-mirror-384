"""Tests for strands-hubspot package.

Basic test coverage to ensure package quality and functionality.
"""

import os
import pytest
from unittest.mock import Mock, patch, MagicMock
import requests

from strands_hubspot import hubspot
from strands_hubspot.hubspot import HubSpotClient


class TestHubSpotClient:
    """Test HubSpotClient class functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.api_key = "test_api_key_123"
        self.client = HubSpotClient(self.api_key)

    def test_client_initialization(self):
        """Test client initialization with API key."""
        assert self.client.api_key == self.api_key
        assert self.client.base_url == "https://api.hubapi.com"
        assert "Bearer test_api_key_123" in self.client.headers["Authorization"]

    @patch('strands_hubspot.hubspot.requests.post')
    def test_search_objects_success(self, mock_post):
        """Test successful object search."""
        # Mock successful response
        mock_response = Mock()
        mock_response.json.return_value = {
            "results": [
                {"id": "123", "properties": {"email": "test@example.com"}}
            ],
            "total": 1
        }
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        result = self.client.search_objects(
            object_type="contacts",
            filters=[{"propertyName": "email", "operator": "EQ", "value": "test@example.com"}],
            limit=10
        )

        assert "results" in result
        assert len(result["results"]) == 1
        assert result["results"][0]["id"] == "123"

    @patch('strands_hubspot.hubspot.requests.get')
    def test_get_object_success(self, mock_get):
        """Test successful object retrieval."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "id": "123",
            "properties": {"email": "test@example.com", "firstname": "John"}
        }
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        result = self.client.get_object("contacts", "123")

        assert result["id"] == "123"
        assert result["properties"]["email"] == "test@example.com"

    @patch('strands_hubspot.hubspot.requests.get')
    def test_list_properties_success(self, mock_get):
        """Test successful property listing."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "results": [
                {"name": "email", "type": "string"},
                {"name": "firstname", "type": "string"}
            ]
        }
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        result = self.client.list_properties("contacts")

        assert "results" in result
        assert len(result["results"]) == 2


class TestHubSpotTool:
    """Test hubspot tool function."""

    @patch.dict(os.environ, {'HUBSPOT_API_KEY': 'test_key_123'})
    def test_missing_api_key_error(self):
        """Test error when API key is missing."""
        with patch.dict(os.environ, {}, clear=True):
            result = hubspot(action="search", object_type="contacts")
            
            assert result["status"] == "error"
            assert "API key not found" in result["content"][0]["text"]

    @patch.dict(os.environ, {'HUBSPOT_API_KEY': 'test_key_123'})
    @patch('strands_hubspot.hubspot.HubSpotClient')
    def test_search_action_success(self, mock_client_class):
        """Test successful search action."""
        # Mock client instance
        mock_client = Mock()
        mock_client.search_objects.return_value = {
            "results": [{"id": "123", "properties": {"email": "test@example.com"}}]
        }
        mock_client_class.return_value = mock_client

        result = hubspot(
            action="search",
            object_type="contacts",
            filters=[{"propertyName": "email", "operator": "EQ", "value": "test@example.com"}]
        )

        assert result["status"] == "success"
        assert "Found 1 contacts" in result["content"][0]["text"]
        mock_client.search_objects.assert_called_once()

    @patch.dict(os.environ, {'HUBSPOT_API_KEY': 'test_key_123'})
    @patch('strands_hubspot.hubspot.HubSpotClient')
    def test_get_action_success(self, mock_client_class):
        """Test successful get action."""
        mock_client = Mock()
        mock_client.get_object.return_value = {
            "id": "123",
            "properties": {"email": "test@example.com"}
        }
        mock_client_class.return_value = mock_client

        result = hubspot(
            action="get",
            object_type="contacts",
            object_id="123"
        )

        assert result["status"] == "success"
        assert "Retrieved contacts ID: 123" in result["content"][0]["text"]
        mock_client.get_object.assert_called_once_with(
            object_type="contacts",
            object_id="123",
            properties=None
        )

    @patch.dict(os.environ, {'HUBSPOT_API_KEY': 'test_key_123'})
    def test_get_action_missing_object_id(self):
        """Test get action with missing object_id."""
        result = hubspot(action="get", object_type="contacts")
        
        assert result["status"] == "error"
        assert "object_id is required" in result["content"][0]["text"]

    @patch.dict(os.environ, {'HUBSPOT_API_KEY': 'test_key_123'})
    @patch('strands_hubspot.hubspot.HubSpotClient')
    def test_list_properties_action_success(self, mock_client_class):
        """Test successful list_properties action."""
        mock_client = Mock()
        mock_client.list_properties.return_value = {
            "results": [
                {"name": "email", "type": "string"},
                {"name": "firstname", "type": "string"}
            ]
        }
        mock_client_class.return_value = mock_client

        result = hubspot(action="list_properties", object_type="contacts")

        assert result["status"] == "success"
        assert "Found 2 properties" in result["content"][0]["text"]

    @patch.dict(os.environ, {'HUBSPOT_API_KEY': 'test_key_123'})
    def test_unknown_action_error(self):
        """Test error for unknown action."""
        result = hubspot(action="invalid_action", object_type="contacts")
        
        assert result["status"] == "error"
        assert "Unknown action: invalid_action" in result["content"][0]["text"]

    @patch.dict(os.environ, {'HUBSPOT_API_KEY': 'test_key_123'})
    @patch('strands_hubspot.hubspot.HubSpotClient')
    def test_api_error_handling(self, mock_client_class):
        """Test API error handling."""
        mock_client = Mock()
        mock_client.search_objects.side_effect = requests.exceptions.HTTPError("API Error")
        mock_client_class.return_value = mock_client

        result = hubspot(action="search", object_type="contacts")

        assert result["status"] == "error"
        assert "HubSpot API error" in result["content"][0]["text"]


class TestPackageStructure:
    """Test package structure and imports."""

    def test_package_import(self):
        """Test that the package can be imported correctly."""
        from strands_hubspot import hubspot
        assert callable(hubspot)

    def test_version_import(self):
        """Test that version is properly defined."""
        from strands_hubspot import __version__
        assert __version__ == "0.1.0"

    def test_all_exports(self):
        """Test that __all__ is properly defined."""
        from strands_hubspot import __all__
        assert "hubspot" in __all__


if __name__ == "__main__":
    pytest.main([__file__])
