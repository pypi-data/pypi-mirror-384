"""Tests for storage utilities"""

import pytest
import sys
from unittest.mock import Mock, patch, mock_open, MagicMock
from src.ctmu.storage import (
    s3_upload, s3_download, s3_list, s3_delete,
    nextcloud_upload, nextcloud_download, nextcloud_list,
    nextcloud_delete, nextcloud_mkdir
)

class TestS3Functions:

    @patch('boto3.Session')
    def test_s3_upload_success(self, mock_session):
        mock_s3 = Mock()
        mock_session.return_value.client.return_value = mock_s3

        result = s3_upload('test.txt', 'bucket', 'key')

        mock_s3.upload_file.assert_called_once_with('test.txt', 'bucket', 'key')
        assert "Uploaded test.txt to s3://bucket/key" in result

    @patch('boto3.Session')
    def test_s3_download_success(self, mock_session):
        mock_s3 = Mock()
        mock_session.return_value.client.return_value = mock_s3

        result = s3_download('bucket', 'key', 'local.txt')

        mock_s3.download_file.assert_called_once_with('bucket', 'key', 'local.txt')
        assert "Downloaded s3://bucket/key to local.txt" in result

    @patch('boto3.Session')
    def test_s3_list_success(self, mock_session):
        mock_s3 = Mock()
        from datetime import datetime
        mock_response = {
            'Contents': [
                {'Key': 'file1.txt', 'Size': 100, 'LastModified': datetime.now()},
                {'Key': 'file2.txt', 'Size': 200, 'LastModified': datetime.now()}
            ]
        }
        mock_s3.list_objects_v2.return_value = mock_response
        mock_session.return_value.client.return_value = mock_s3

        result = s3_list('bucket')

        assert len(result) == 2
        assert result[0]['Key'] == 'file1.txt'

    def test_s3_upload_no_boto3(self):
        # Mock boto3 import to raise ImportError
        with patch.dict('sys.modules', {'boto3': None}):
            import importlib
            # Reload storage module to trigger ImportError
            result = s3_upload('test.txt', 'bucket')
            assert "boto3 not installed" in result or "Error:" in result

class TestNextcloudFunctions:

    @patch('webdav4.client.Client')
    @patch('builtins.open', mock_open(read_data=b'test data'))
    def test_nextcloud_upload_success(self, mock_client):
        mock_client_instance = Mock()
        mock_client.return_value = mock_client_instance

        result = nextcloud_upload('test.txt', '/remote/test.txt', 'url', 'user', 'pass')

        mock_client_instance.upload_fileobj.assert_called_once()
        assert "Uploaded test.txt to /remote/test.txt" in result

    @patch('webdav4.client.Client')
    @patch('builtins.open', mock_open())
    def test_nextcloud_download_success(self, mock_client):
        mock_client_instance = Mock()
        mock_client.return_value = mock_client_instance

        result = nextcloud_download('/remote/test.txt', 'local.txt', 'url', 'user', 'pass')

        mock_client_instance.download_fileobj.assert_called_once()
        assert "Downloaded /remote/test.txt to local.txt" in result

    @patch('webdav4.client.Client')
    def test_nextcloud_list_success(self, mock_client):
        mock_client_instance = Mock()
        mock_item1 = Mock()
        mock_item1.name = 'file1.txt'
        mock_item1.is_dir = False
        mock_item1.content_length = 100
        mock_item1.__str__ = Mock(return_value='/remote/file1.txt')

        mock_item2 = Mock()
        mock_item2.name = 'folder1'
        mock_item2.is_dir = True
        mock_item2.__str__ = Mock(return_value='/remote/folder1')

        mock_client_instance.ls.return_value = [mock_item1, mock_item2]
        mock_client.return_value = mock_client_instance

        result = nextcloud_list('/remote/', 'url', 'user', 'pass')

        assert len(result) == 2
        assert result[0]['Name'] == 'file1.txt'
        assert result[0]['Type'] == 'File'
        assert result[1]['Type'] == 'Directory'

    def test_nextcloud_upload_no_webdav4(self):
        # Mock webdav4 import to raise ImportError
        with patch.dict('sys.modules', {'webdav4': None, 'webdav4.client': None}):
            result = nextcloud_upload('test.txt', '/remote/', 'url', 'user', 'pass')
            assert "webdav4 not installed" in result or "Error:" in result