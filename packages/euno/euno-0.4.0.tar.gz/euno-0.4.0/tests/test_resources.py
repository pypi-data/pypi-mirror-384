"""
Test cases for the Euno SDK resources functionality.
"""

import pytest
from unittest.mock import patch, Mock
from euno.resources import list_resources
from euno.api import EunoAPIClient


class TestResourcesAPI:
    """Test cases for resources API functions."""

    def setup_method(self):
        """Set up test fixtures."""
        pass

    @patch("euno.resources.config")
    @patch("euno.resources.api_client")
    def test_list_resources_success(self, mock_api_client, mock_config):
        """Test successful resources list API call."""
        mock_config.is_configured.return_value = True
        mock_config.get_token.return_value = "test-token"
        mock_config.get_account_id.return_value = "4"

        mock_response = {
            "resources": [
                {"uri": "test.uri.1", "name": "Test Resource 1", "type": "table"},
                {"uri": "test.uri.2", "name": "Test Resource 2", "type": "view"},
            ],
            "count": 2,
            "relevance_sort": None,
            "warnings": [],
        }
        mock_api_client.search_resources.return_value = mock_response

        result = list_resources(
            eql="has child(true, 1)",
            properties="uri,name,type",
            page=1,
            page_size=10,
            sorting="name",
            relationships="parent,child",
        )

        mock_api_client.search_resources.assert_called_once()
        assert result == mock_response
        assert result["count"] == 2
        assert len(result["resources"]) == 2

    @patch("euno.resources.config")
    def test_list_resources_not_configured(self, mock_config):
        """Test resources list API when not configured."""
        mock_config.is_configured.return_value = False

        with pytest.raises(Exception, match="not configured"):
            list_resources()

    @patch("euno.resources.config")
    def test_list_resources_no_account_id(self, mock_config):
        """Test resources list API when no account ID is configured."""
        mock_config.is_configured.return_value = True
        mock_config.get_token.return_value = "test-token"
        mock_config.get_account_id.return_value = None

        with pytest.raises(Exception, match="No account ID configured"):
            list_resources()

    @patch("euno.resources.config")
    def test_list_resources_no_token(self, mock_config):
        """Test resources list API when no token is configured."""
        mock_config.is_configured.return_value = True
        mock_config.get_token.return_value = None
        mock_config.get_account_id.return_value = "4"

        with pytest.raises(Exception, match="No token configured"):
            list_resources()

    @patch("euno.resources.config")
    @patch("euno.resources.api_client")
    def test_list_resources_default_parameters(self, mock_api_client, mock_config):
        """Test resources list API with default parameters."""
        mock_config.is_configured.return_value = True
        mock_config.get_token.return_value = "test-token"
        mock_config.get_account_id.return_value = "4"

        mock_response = {
            "resources": [{"uri": "test.uri", "name": "Test", "type": "table"}],
            "count": 1,
        }
        mock_api_client.search_resources.return_value = mock_response

        result = list_resources()

        # Check that default parameters were used
        call_args = mock_api_client.search_resources.call_args
        params = call_args[0][2]  # Third argument is params
        assert params["page"] == 1
        assert params["page_size"] == 50
        assert params["properties"] == ["uri", "type", "name"]
        assert result == mock_response


class TestEunoAPIClientResources:
    """Test cases for API client resources functionality."""

    def test_search_resources_success(self):
        """Test successful resources search."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "resources": [{"uri": "test.uri", "name": "Test", "type": "table"}],
            "count": 1,
        }
        mock_response.raise_for_status.return_value = None

        with patch("requests.Session.get", return_value=mock_response):
            client = EunoAPIClient()
            result = client.search_resources("test-token", "4", {"page": 1, "page_size": 10})

            assert result["count"] == 1
            assert len(result["resources"]) == 1
            assert result["resources"][0]["uri"] == "test.uri"

    def test_search_resources_failure(self):
        """Test resources search failure."""
        mock_response = Mock()
        mock_response.raise_for_status.side_effect = Exception("Unauthorized")

        with patch("requests.Session.get", return_value=mock_response):
            client = EunoAPIClient()

            with pytest.raises(Exception):
                client.search_resources("invalid-token", "4", {"page": 1})
