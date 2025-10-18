"""Tests for CLI interface"""

import pytest
from click.testing import CliRunner
from unittest.mock import patch
from src.ctmu.cli import cli

def test_cli_with_url():
    """Test CLI with URL argument"""
    runner = CliRunner()

    with patch('src.ctmu.core.CTMUCore.generate_qr') as mock_generate:
        mock_generate.return_value = ['file1.png', 'file1.jpg', 'file1.svg']
        result = runner.invoke(cli, ['qr', 'https://example.com'])
        
        assert result.exit_code == 0
        mock_generate.assert_called_once_with('https://example.com', 'bauhaus', '.')
        assert 'QR code generated!' in result.output

def test_cli_with_style_and_output():
    """Test CLI with style and output options"""
    runner = CliRunner()

    with patch('src.ctmu.core.CTMUCore.generate_qr') as mock_generate:
        mock_generate.return_value = ['./output/file1.png', './output/file1.jpg', './output/file1.svg']
        result = runner.invoke(cli, ['qr', '--style', 'hacker', '--output', './output', 'https://example.com'])
        
        assert result.exit_code == 0
        mock_generate.assert_called_once_with('https://example.com', 'hacker', './output')

def test_cli_interactive_mode():
    """Test CLI interactive mode"""
    runner = CliRunner()

    with patch('src.ctmu.core.CTMUCore.generate_qr') as mock_generate:
        mock_generate.return_value = ['file1.png', 'file1.jpg', 'file1.svg']
        result = runner.invoke(cli, ['qr'], input='https://example.com\n')
        
        assert result.exit_code == 0
        mock_generate.assert_called_once()

def test_cli_error_handling():
    """Test CLI error handling"""
    runner = CliRunner()

    with patch('src.ctmu.core.CTMUCore.generate_qr', side_effect=Exception('Test error')):
        result = runner.invoke(cli, ['qr', 'https://example.com'])
        
        assert result.exit_code == 0
        assert 'Error: Test error' in result.output