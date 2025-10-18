"""Tests for extended functions"""

import pytest
from unittest.mock import Mock, patch
from src.ctmu.dev_utils import generate_uuid, generate_password, validate_json
from src.ctmu.monitor_utils import cpu_usage, memory_usage
from src.ctmu.backup_utils import create_zip

class TestDevUtils:
    def test_generate_uuid(self):
        uuid_str = generate_uuid()
        assert len(uuid_str) == 36
        assert uuid_str.count('-') == 4
    
    def test_generate_password(self):
        password = generate_password(12)
        assert len(password) == 12
    
    def test_validate_json(self):
        assert validate_json('{"valid": true}') == "Valid JSON"
        assert "Invalid JSON" in validate_json('{"invalid": }')

class TestMonitorUtils:
    @patch('src.ctmu.monitor_utils.psutil.cpu_percent')
    def test_cpu_usage(self, mock_cpu):
        mock_cpu.return_value = 25.5
        result = cpu_usage()
        assert result == 25.5

    @patch('src.ctmu.monitor_utils.psutil.virtual_memory')
    def test_memory_usage(self, mock_memory):
        mock_mem = Mock()
        mock_mem.total = 8 * 1024**3
        mock_mem.available = 4 * 1024**3
        mock_mem.used = 4 * 1024**3
        mock_mem.percent = 50.0
        mock_memory.return_value = mock_mem
        
        result = memory_usage()
        assert result['percentage'] == '50.0%'

class TestBackupUtils:
    @patch('src.ctmu.backup_utils.zipfile.ZipFile')
    @patch('src.ctmu.backup_utils.os.path.isfile')
    def test_create_zip(self, mock_isfile, mock_zipfile):
        mock_isfile.return_value = True
        mock_zip = Mock()
        mock_zipfile.return_value.__enter__.return_value = mock_zip
        
        result = create_zip('test.txt')
        assert "Created ZIP archive" in result