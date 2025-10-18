"""Tests for GPG utilities"""

import pytest
from unittest.mock import Mock, patch
from src.ctmu.gpg_utils import (
    gpg_encrypt_file, gpg_decrypt_file, gpg_sign_file,
    gpg_verify_file, gpg_list_keys, gpg_generate_key,
    gpg_export_key, gpg_import_key
)

class TestGPGFunctions:
    
    @patch('src.ctmu.gpg_utils.subprocess.run')
    def test_gpg_encrypt_success(self, mock_run):
        mock_run.return_value.returncode = 0
        mock_run.return_value.stderr = ""
        
        result = gpg_encrypt_file('test.txt', 'user@example.com')
        
        assert "Encrypted test.txt to test.txt.gpg" in result
        mock_run.assert_called_once()
    
    @patch('src.ctmu.gpg_utils.subprocess.run')
    def test_gpg_decrypt_success(self, mock_run):
        mock_run.return_value.returncode = 0
        mock_run.return_value.stderr = ""
        
        result = gpg_decrypt_file('test.txt.gpg')
        
        assert "Decrypted test.txt.gpg to test.txt" in result
        mock_run.assert_called_once()
    
    @patch('src.ctmu.gpg_utils.subprocess.run')
    def test_gpg_sign_success(self, mock_run):
        mock_run.return_value.returncode = 0
        mock_run.return_value.stderr = ""
        
        result = gpg_sign_file('test.txt')
        
        assert "Signed test.txt to test.txt.sig" in result
        mock_run.assert_called_once()
    
    @patch('src.ctmu.gpg_utils.subprocess.run')
    def test_gpg_verify_success(self, mock_run):
        mock_run.return_value.returncode = 0
        mock_run.return_value.stderr = ""
        
        result = gpg_verify_file('test.txt')
        
        assert "Signature verified" in result
        mock_run.assert_called_once()
    
    @patch('src.ctmu.gpg_utils.subprocess.run')
    def test_gpg_list_keys_success(self, mock_run):
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = "pub:u:4096:1:ABCD1234EFGH5678:1234567890:::u:::scESC:::\nuid:u::::1234567890::Test User <test@example.com>:::\n"
        
        result = gpg_list_keys()
        
        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0]['keyid'] == 'EFGH5678'
    
    def test_gpg_encrypt_no_gpg(self):
        with patch('src.ctmu.gpg_utils.subprocess.run', side_effect=FileNotFoundError):
            result = gpg_encrypt_file('test.txt', 'user@example.com')
            assert "GPG not installed" in result
    
    @patch('src.ctmu.gpg_utils.subprocess.run')
    def test_gpg_generate_key_success(self, mock_run):
        mock_run.return_value.returncode = 0
        mock_run.return_value.stderr = ""
        
        result = gpg_generate_key('Test User', 'test@example.com')
        
        assert "Key generated successfully" in result
        mock_run.assert_called_once()
    
    @patch('src.ctmu.gpg_utils.subprocess.run')
    def test_gpg_export_key_success(self, mock_run):
        mock_run.return_value.returncode = 0
        mock_run.return_value.stderr = ""
        
        result = gpg_export_key('ABCD1234')
        
        assert "Exported key ABCD1234 to ABCD1234.asc" in result
        mock_run.assert_called_once()
    
    @patch('src.ctmu.gpg_utils.subprocess.run')
    def test_gpg_import_key_success(self, mock_run):
        mock_run.return_value.returncode = 0
        mock_run.return_value.stderr = ""
        
        result = gpg_import_key('key.asc')
        
        assert "Key imported successfully" in result
        mock_run.assert_called_once()