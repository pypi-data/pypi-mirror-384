"""QR code generation with styling strategies"""

import qrcode
from .stylers import BauhausStyler, ClassicStyler, HackerStyler

class QRGenerator:
    def __init__(self):
        self.stylers = {
            'bauhaus': BauhausStyler(),
            'classic': ClassicStyler(),
            'hacker': HackerStyler()
        }
    
    def generate(self, url, style='bauhaus'):
        """Generate high-quality styled QR code"""
        if not url or not isinstance(url, str):
            raise ValueError("URL must be a non-empty string")
            
        try:
            # Higher quality settings for professional use
            qr = qrcode.QRCode(
                version=None,  # Auto-size based on data
                error_correction=qrcode.constants.ERROR_CORRECT_H,  # Highest error correction
                box_size=12,  # Larger boxes for better quality
                border=0,     # No blank margins
            )
            qr.add_data(url)
            qr.make(fit=True)
            
            # Create high-quality base image
            img = qr.make_image(fill_color="black", back_color="white")
            
            # Convert to RGBA for better styling support
            img = img.convert('RGBA')
            
            # Apply styling
            styler = self.stylers.get(style, self.stylers['bauhaus'])
            return styler.apply_style(img)
        except Exception as e:
            raise RuntimeError(f"Failed to generate QR code: {e}")