"""
Tests for metadata tags functionality.
"""

import pytest
from unittest.mock import Mock, patch
from euno.metadata_tags import list_metadata_tags, set_metadata_tag_value
from euno.api import EunoAPIClient


class TestMetadataTagsAPI:
    """Test the metadata tags Python API functions."""

    def test_list_metadata_tags_success(self):
        """Test successful listing of metadata tags."""
        mock_response = [
            {"id": 1, "name": "Environment", "type": "string", "description": "Environment type"},
            {"id": 2, "name": "Owner", "type": "string", "description": "Resource owner"},
        ]

        with patch("euno.metadata_tags.api_client") as mock_client:
            mock_client.list_metadata_tags.return_value = mock_response

            with patch("euno.metadata_tags.config") as mock_config:
                mock_config.get_token.return_value = "test-token"
                mock_config.get_account_id.return_value = "123"

                result = list_metadata_tags()

                assert result == mock_response
                mock_client.list_metadata_tags.assert_called_once_with("test-token", "123")

    def test_list_metadata_tags_not_configured(self):
        """Test listing metadata tags when not configured."""
        with patch("euno.metadata_tags.config") as mock_config:
            mock_config.get_token.return_value = None

            with pytest.raises(ValueError, match="No API token configured"):
                list_metadata_tags()

    def test_list_metadata_tags_no_account_id(self):
        """Test listing metadata tags when no account ID is configured."""
        with patch("euno.metadata_tags.config") as mock_config:
            mock_config.get_token.return_value = "test-token"
            mock_config.get_account_id.return_value = None

            with pytest.raises(ValueError, match="No account ID configured"):
                list_metadata_tags()

    def test_set_metadata_tag_value_success(self):
        """Test successful setting of metadata tag values."""
        mock_response = {"status": "success", "updated_count": 2}
        value_updates = [
            {"resource_uri": "table://schema.table1", "value": "production"},
            {"resource_uri": "table://schema.table2", "value": "staging"},
        ]

        with patch("euno.metadata_tags.api_client") as mock_client:
            mock_client.set_metadata_tag_value.return_value = mock_response

            with patch("euno.metadata_tags.config") as mock_config:
                mock_config.get_token.return_value = "test-token"
                mock_config.get_account_id.return_value = "123"

                result = set_metadata_tag_value(456, value_updates)

                assert result == mock_response
                mock_client.set_metadata_tag_value.assert_called_once_with("test-token", "123", 456, value_updates)

    def test_set_metadata_tag_value_not_configured(self):
        """Test setting metadata tag values when not configured."""
        with patch("euno.metadata_tags.config") as mock_config:
            mock_config.get_token.return_value = None

            with pytest.raises(ValueError, match="No API token configured"):
                set_metadata_tag_value(456, [])


class TestEunoAPIClientMetadataTags:
    """Test the EunoAPIClient metadata tags methods."""

    def test_list_metadata_tags_success(self):
        """Test successful API call to list metadata tags."""
        mock_response = Mock()
        mock_response.json.return_value = [{"id": 1, "name": "Environment"}]
        mock_response.raise_for_status.return_value = None

        client = EunoAPIClient()
        with patch.object(client.session, "get", return_value=mock_response) as mock_get:
            result = client.list_metadata_tags("test-token", "123")

            assert result == [{"id": 1, "name": "Environment"}]
            mock_get.assert_called_once_with(
                "https://api.app.euno.ai/v1/accounts/123/metadata_tags",
                headers={
                    "Authorization": "Bearer test-token",
                    "Content-Type": "application/json",
                    "User-Agent": "euno-sdk/0.4.0",
                },
            )

    def test_set_metadata_tag_value_success(self):
        """Test successful API call to set metadata tag values."""
        mock_response = Mock()
        mock_response.json.return_value = {"status": "success"}
        mock_response.raise_for_status.return_value = None

        client = EunoAPIClient()
        value_updates = [{"resource_uri": "table://schema.table", "value": "production"}]

        with patch.object(client.session, "post", return_value=mock_response) as mock_post:
            result = client.set_metadata_tag_value("test-token", "123", 456, value_updates)

            assert result == {"status": "success"}
            mock_post.assert_called_once_with(
                "https://api.app.euno.ai/v1/accounts/123/metadata_tags/456/values",
                headers={
                    "Authorization": "Bearer test-token",
                    "Content-Type": "application/json",
                    "User-Agent": "euno-sdk/0.4.0",
                },
                json=value_updates,
            )
