"""Media and file utilities"""

import os
import subprocess
from pathlib import Path

def get_media_info(file_path):
    """Get media file information"""
    try:
        cmd = ['ffprobe', '-v', 'quiet', '-print_format', 'json', '-show_format', '-show_streams', file_path]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            import json
            data = json.loads(result.stdout)
            format_info = data.get('format', {})
            return {
                'duration': format_info.get('duration', 'Unknown'),
                'size': format_info.get('size', 'Unknown'),
                'bitrate': format_info.get('bit_rate', 'Unknown'),
                'format': format_info.get('format_name', 'Unknown')
            }
        return f"Error: {result.stderr}"
    except FileNotFoundError:
        return "Error: ffprobe not installed. Install with: brew install ffmpeg"
    except Exception as e:
        return f"Error: {e}"

def convert_audio(input_path, output_path, format='mp3', bitrate='192k'):
    """Convert audio file format"""
    try:
        cmd = ['ffmpeg', '-i', input_path, '-ab', bitrate, '-f', format, output_path, '-y']
        result = subprocess.run(cmd, capture_output=True, text=True)
        return f"Converted {input_path} to {output_path}" if result.returncode == 0 else f"Error: {result.stderr}"
    except FileNotFoundError:
        return "Error: ffmpeg not installed. Install with: brew install ffmpeg"
    except Exception as e:
        return f"Error: {e}"

def extract_audio(video_path, output_path=None):
    """Extract audio from video"""
    try:
        if not output_path:
            output_path = Path(video_path).stem + '.mp3'
        cmd = ['ffmpeg', '-i', video_path, '-vn', '-acodec', 'mp3', output_path, '-y']
        result = subprocess.run(cmd, capture_output=True, text=True)
        return f"Extracted audio to {output_path}" if result.returncode == 0 else f"Error: {result.stderr}"
    except FileNotFoundError:
        return "Error: ffmpeg not installed. Install with: brew install ffmpeg"
    except Exception as e:
        return f"Error: {e}"

def compress_pdf(input_path, output_path=None, quality='ebook'):
    """Compress PDF file"""
    try:
        if not output_path:
            output_path = input_path.replace('.pdf', '_compressed.pdf')
        
        quality_settings = {
            'screen': '/screen',
            'ebook': '/ebook',
            'printer': '/printer',
            'prepress': '/prepress'
        }
        
        cmd = ['gs', '-sDEVICE=pdfwrite', '-dCompatibilityLevel=1.4',
               f'-dPDFSETTINGS={quality_settings.get(quality, "/ebook")}',
               '-dNOPAUSE', '-dQUIET', '-dBATCH',
               f'-sOutputFile={output_path}', input_path]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        return f"Compressed PDF to {output_path}" if result.returncode == 0 else f"Error: {result.stderr}"
    except FileNotFoundError:
        return "Error: Ghostscript not installed. Install with: brew install ghostscript"
    except Exception as e:
        return f"Error: {e}"