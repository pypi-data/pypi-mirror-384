"""Tests for QR code stylers"""

import pytest
from PIL import Image
from src.ctmu.stylers import BauhausStyler, ClassicStyler, HackerStyler

def test_bauhaus_styler():
    styler = BauhausStyler()
    img = Image.new('RGB', (100, 100), 'white')
    try:
        result = styler.apply_style(img)
        try:
            assert result.mode == 'RGBA'
        finally:
            result.close()
    finally:
        img.close()

def test_classic_styler():
    styler = ClassicStyler()
    img = Image.new('RGB', (100, 100), 'white')
    try:
        result = styler.apply_style(img)
        try:
            assert result.mode == 'RGBA'
        finally:
            result.close()
    finally:
        img.close()

def test_hacker_styler():
    styler = HackerStyler()
    img = Image.new('RGB', (100, 100), 'white')
    try:
        result = styler.apply_style(img)
        try:
            assert result.mode == 'RGBA'
        finally:
            result.close()
    finally:
        img.close()