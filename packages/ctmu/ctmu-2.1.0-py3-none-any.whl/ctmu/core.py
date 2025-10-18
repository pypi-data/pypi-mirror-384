"""Core CTMU functionality"""

import os
from urllib.parse import urlparse
from PIL import Image
from .qr_generator import QRGenerator
from .favicon_fetcher import FaviconFetcher
from .image_processor import ImageProcessor
from .validators import URLValidator

class CTMUCore:
    def __init__(self):
        self.qr_gen = QRGenerator()
        self.favicon_fetcher = FaviconFetcher()
        self.image_processor = ImageProcessor()
    
    def generate_qr(self, url, style='bauhaus', output_dir='.'):
        """Generate QR code files with favicon"""
        try:
            # Validate URL
            url = URLValidator.validate(url)
            
            # Generate base QR code
            qr_image = self.qr_gen.generate(url, style)
            
            # Fetch favicon
            favicon = self.favicon_fetcher.fetch(url)
            
            # Compose final image
            final_image = self.image_processor.embed_favicon(qr_image, favicon)
            
            # Generate filename from domain
            domain = urlparse(url).netloc.replace('www.', '')
            base_filename = f"qr_{domain}_{style}"
            
            # Save high-quality files
            files_created = []
            
            # PNG - Highest quality for professional use
            png_path = os.path.join(output_dir, f"{base_filename}.png")
            final_image.save(png_path, 'PNG', optimize=True, compress_level=6)
            files_created.append(png_path)
            
            # JPEG - High quality with white background
            jpeg_path = os.path.join(output_dir, f"{base_filename}.jpg")
            # Create white background for JPEG
            white_bg = Image.new('RGB', final_image.size, (255, 255, 255))
            if final_image.mode == 'RGBA':
                white_bg.paste(final_image, mask=final_image.split()[-1])
            else:
                white_bg.paste(final_image)
            white_bg.save(jpeg_path, 'JPEG', quality=98, optimize=True, progressive=True)
            files_created.append(jpeg_path)
            
            # SVG - Optimized vector format
            svg_path = os.path.join(output_dir, f"{base_filename}.svg")
            self._save_as_svg(final_image, svg_path)
            files_created.append(svg_path)
            
            return files_created
            
        except ValueError as e:
            raise ValueError(f"Invalid URL: {e}")
        except OSError as e:
            raise OSError(f"File system error: {e}")
        except Exception as e:
            raise RuntimeError(f"QR generation failed: {e}")
    
    def _save_as_svg(self, image, svg_path):
        """Convert PIL image to SVG"""
        width, height = image.size
        
        svg_content = f'''<?xml version="1.0" encoding="UTF-8"?>
<svg width="{width}" height="{height}" xmlns="http://www.w3.org/2000/svg">
'''
        
        # Convert pixels to SVG rectangles
        for y in range(height):
            for x in range(width):
                pixel = image.getpixel((x, y))
                if len(pixel) == 4:  # RGBA
                    r, g, b, a = pixel
                    if a > 128:  # Only draw visible pixels
                        color = f"rgb({r},{g},{b})"
                        svg_content += f'<rect x="{x}" y="{y}" width="1" height="1" fill="{color}"/>\n'
                else:  # RGB
                    r, g, b = pixel
                    if sum(pixel) < 600:  # Only draw dark pixels
                        color = f"rgb({r},{g},{b})"
                        svg_content += f'<rect x="{x}" y="{y}" width="1" height="1" fill="{color}"/>\n'
        
        svg_content += '</svg>'
        
        with open(svg_path, 'w', encoding='utf-8') as f:
            f.write(svg_content)