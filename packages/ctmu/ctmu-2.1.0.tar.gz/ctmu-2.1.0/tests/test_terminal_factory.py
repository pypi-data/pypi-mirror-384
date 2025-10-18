"""Tests for terminal factory"""

import pytest
from unittest.mock import patch
from PIL import Image
from src.ctmu.terminal_factory import TerminalFactory, iTerm2Display, StandardTerminalDisplay

def test_terminal_factory_iterm2():
    """Test factory creates iTerm2 display"""
    with patch.dict('os.environ', {'TERM_PROGRAM': 'iTerm.app'}):
        display = TerminalFactory.create_display()
        assert isinstance(display, iTerm2Display)

def test_terminal_factory_default():
    """Test factory creates default terminal display"""
    with patch.dict('os.environ', {'TERM_PROGRAM': 'Terminal.app'}):
        display = TerminalFactory.create_display()
        assert isinstance(display, StandardTerminalDisplay)

def test_iterm2_display(sample_qr_image, capsys):
    """Test iTerm2 display output"""
    display = iTerm2Display()
    display.display(sample_qr_image)
    
    captured = capsys.readouterr()
    assert captured.out

def test_terminal_display(sample_qr_image, capsys):
    """Test terminal display output"""
    display = StandardTerminalDisplay()
    display.display(sample_qr_image)
    
    captured = capsys.readouterr()
    assert captured.out