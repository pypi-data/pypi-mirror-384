"""Image processing and composition"""

from PIL import Image, ImageDraw, ImageFilter
import math

class ImageProcessor:
    def embed_favicon(self, qr_image, favicon):
        """Integrate favicon with clean white background"""
        qr_image = qr_image.convert('RGBA')
        
        # Calculate maximum favicon size
        favicon_size = min(qr_image.size) // 3
        favicon = self._resize_favicon(favicon, (favicon_size, favicon_size))
        
        # Resize favicon to fill maximum space
        favicon = favicon.resize((favicon_size, favicon_size), Image.Resampling.LANCZOS)
        
        # Create minimal white background just for the favicon
        bg = Image.new('RGBA', (favicon_size, favicon_size), (255, 255, 255, 255))
        bg.paste(favicon, (0, 0), favicon)
        
        # Paste on QR code center
        paste_x = (qr_image.size[0] - favicon_size) // 2
        paste_y = (qr_image.size[1] - favicon_size) // 2
        qr_image.paste(bg, (paste_x, paste_y))
        
        return qr_image
    
    def _create_favicon_background(self, size, qr_image):
        """Create elegant circular background for favicon"""
        bg = Image.new('RGBA', (size, size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(bg)
        
        # Create circular white background with subtle gradient
        center = size // 2
        radius = center - 2
        
        # Draw multiple circles for gradient effect
        for i in range(radius, 0, -2):
            alpha = int(255 * (1 - i / radius * 0.1))
            color = (255, 255, 255, alpha)
            draw.ellipse([center-i, center-i, center+i, center+i], fill=color)
        
        # Add subtle shadow
        shadow = Image.new('RGBA', (size, size), (0, 0, 0, 0))
        shadow_draw = ImageDraw.Draw(shadow)
        shadow_draw.ellipse([1, 1, size-1, size-1], fill=(0, 0, 0, 30))
        shadow = shadow.filter(ImageFilter.GaussianBlur(radius=1))
        
        # Composite shadow and background
        result = Image.alpha_composite(shadow, bg)
        return result
    
    def _resize_favicon(self, favicon, size):
        """Resize favicon with high quality resampling"""
        favicon_copy = favicon.copy()
        
        # Use high-quality resampling
        favicon_copy.thumbnail(size, Image.Resampling.LANCZOS)
        
        # Ensure favicon has alpha channel
        if favicon_copy.mode != 'RGBA':
            favicon_copy = favicon_copy.convert('RGBA')
        
        return favicon_copy