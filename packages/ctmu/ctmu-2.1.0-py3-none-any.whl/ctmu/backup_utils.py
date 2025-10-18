"""Backup and archive utilities"""

import os
import shutil
import tarfile
import zipfile
from pathlib import Path
import subprocess

def create_zip(source_path, output_path=None, exclude_patterns=None):
    """Create ZIP archive"""
    try:
        if not output_path:
            output_path = f"{Path(source_path).name}.zip"
        
        exclude_patterns = exclude_patterns or ['.git', '__pycache__', '.DS_Store']
        
        with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            if os.path.isfile(source_path):
                zipf.write(source_path, Path(source_path).name)
            else:
                for root, dirs, files in os.walk(source_path):
                    # Filter out excluded directories
                    dirs[:] = [d for d in dirs if not any(pattern in d for pattern in exclude_patterns)]
                    
                    for file in files:
                        if not any(pattern in file for pattern in exclude_patterns):
                            file_path = os.path.join(root, file)
                            arc_path = os.path.relpath(file_path, source_path)
                            zipf.write(file_path, arc_path)
        
        return f"Created ZIP archive: {output_path}"
    except Exception as e:
        return f"Error: {e}"

def extract_zip(zip_path, extract_to=None):
    """Extract ZIP archive"""
    try:
        if not extract_to:
            extract_to = Path(zip_path).stem
        
        with zipfile.ZipFile(zip_path, 'r') as zipf:
            zipf.extractall(extract_to)
        
        return f"Extracted to: {extract_to}"
    except Exception as e:
        return f"Error: {e}"

def create_tar(source_path, output_path=None, compression='gz'):
    """Create TAR archive"""
    try:
        if not output_path:
            ext = f".tar.{compression}" if compression else ".tar"
            output_path = f"{Path(source_path).name}{ext}"
        
        mode = f"w:{compression}" if compression else "w"
        
        with tarfile.open(output_path, mode) as tar:
            tar.add(source_path, arcname=Path(source_path).name)
        
        return f"Created TAR archive: {output_path}"
    except Exception as e:
        return f"Error: {e}"

def sync_directories(source, destination, delete=False):
    """Sync directories using rsync"""
    try:
        cmd = ['rsync', '-av']
        if delete:
            cmd.append('--delete')
        cmd.extend([source, destination])
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        return f"Synced {source} to {destination}" if result.returncode == 0 else f"Error: {result.stderr}"
    except FileNotFoundError:
        return "Error: rsync not installed"
    except Exception as e:
        return f"Error: {e}"

def backup_database(db_type, db_name, output_path=None, host='localhost', user=None):
    """Backup database"""
    try:
        if not output_path:
            output_path = f"{db_name}_backup.sql"
        
        if db_type.lower() == 'mysql':
            cmd = ['mysqldump', '-h', host]
            if user:
                cmd.extend(['-u', user, '-p'])
            cmd.append(db_name)
        elif db_type.lower() == 'postgresql':
            cmd = ['pg_dump', '-h', host]
            if user:
                cmd.extend(['-U', user])
            cmd.append(db_name)
        else:
            return "Error: Unsupported database type"
        
        with open(output_path, 'w') as f:
            result = subprocess.run(cmd, stdout=f, stderr=subprocess.PIPE, text=True)
        
        return f"Database backed up to: {output_path}" if result.returncode == 0 else f"Error: {result.stderr}"
    except Exception as e:
        return f"Error: {e}"