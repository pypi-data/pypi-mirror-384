"""QR code styling strategies"""

from PIL import Image, ImageDraw, ImageFilter
from abc import ABC, abstractmethod
import math

class QRStyler(ABC):
    @abstractmethod
    def apply_style(self, img):
        pass

class BauhausStyler(QRStyler):
    def apply_style(self, img):
        """Clean Bauhaus style"""
        img = img.convert('RGBA')
        width, height = img.size
        
        # Minimal padding for clean look
        padding = width // 20
        new_size = width + 2 * padding
        styled = Image.new('RGBA', (new_size, new_size), (255, 255, 255, 255))
        
        # Clean white background
        styled.paste(img, (padding, padding))
        
        return styled
    
    def _add_rounded_corners(self, img, radius):
        """Add rounded corners to image"""
        mask = Image.new('L', img.size, 0)
        draw = ImageDraw.Draw(mask)
        draw.rounded_rectangle([0, 0, img.size[0], img.size[1]], radius, fill=255)
        
        result = Image.new('RGBA', img.size, (0, 0, 0, 0))
        result.paste(img, (0, 0))
        result.putalpha(mask)
        return result

class ClassicStyler(QRStyler):
    def apply_style(self, img):
        """Clean classic style with subtle shadow"""
        img = img.convert('RGBA')
        width, height = img.size
        
        # Minimal shadow and padding
        shadow_offset = 3
        padding = width // 20
        new_size = width + 2 * padding + shadow_offset
        styled = Image.new('RGBA', (new_size, new_size), (255, 255, 255, 255))
        
        # Subtle shadow
        shadow = Image.new('RGBA', (width, height), (0, 0, 0, 40))
        shadow = shadow.filter(ImageFilter.GaussianBlur(radius=2))
        styled.paste(shadow, (padding + shadow_offset, padding + shadow_offset), shadow)
        
        # Clean QR code
        styled.paste(img, (padding, padding))
        
        return styled
    
    def _create_refined_qr(self, img):
        """Create refined QR with better contrast and clean edges"""
        pixels = img.load()
        width, height = img.size
        
        # Enhance contrast and clean up edges
        for x in range(width):
            for y in range(height):
                r, g, b, a = pixels[x, y]
                if r < 128:  # Dark pixels - make them pure black
                    pixels[x, y] = (0, 0, 0, 255)
                else:  # Light pixels - make them pure white
                    pixels[x, y] = (255, 255, 255, 255)
        
        return img

class HackerStyler(QRStyler):
    def apply_style(self, img):
        """Clean dark theme with neon accents"""
        img = img.convert('RGBA')
        width, height = img.size
        
        # Minimal dark background
        padding = width // 20
        new_size = width + 2 * padding
        styled = Image.new('RGBA', (new_size, new_size), (20, 20, 30, 255))
        
        # Create clean neon QR
        neon_qr = self._create_neon_qr(img)
        styled.paste(neon_qr, (padding, padding))
        
        return styled
    
    def _create_neon_qr(self, img):
        """Create neon-style QR code"""
        pixels = img.load()
        width, height = img.size
        
        for x in range(width):
            for y in range(height):
                r, g, b, a = pixels[x, y]
                if r < 128:  # Dark pixels - neon cyan
                    pixels[x, y] = (0, 255, 200, 255)
                else:  # Light pixels - dark background
                    pixels[x, y] = (15, 15, 25, 255)
        
        return img