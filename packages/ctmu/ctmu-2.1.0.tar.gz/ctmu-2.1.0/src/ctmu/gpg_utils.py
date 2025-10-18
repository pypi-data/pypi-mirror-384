"""GPG utilities for encryption and key management"""

import subprocess
import os

def gpg_encrypt_file(file_path, recipient, output_path=None):
    """Encrypt file with GPG"""
    try:
        if not output_path:
            output_path = f"{file_path}.gpg"
        
        cmd = ['gpg', '--encrypt', '--recipient', recipient, '--output', output_path, file_path]
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        return f"Encrypted {file_path} to {output_path}" if result.returncode == 0 else f"Error: {result.stderr}"
    except FileNotFoundError:
        return "Error: GPG not installed. Install with: brew install gnupg"
    except Exception as e:
        return f"Error: {e}"

def gpg_decrypt_file(file_path, output_path=None):
    """Decrypt file with GPG"""
    try:
        if not output_path:
            output_path = file_path.replace('.gpg', '')
        
        cmd = ['gpg', '--decrypt', '--output', output_path, file_path]
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        return f"Decrypted {file_path} to {output_path}" if result.returncode == 0 else f"Error: {result.stderr}"
    except FileNotFoundError:
        return "Error: GPG not installed. Install with: brew install gnupg"
    except Exception as e:
        return f"Error: {e}"

def gpg_sign_file(file_path, output_path=None):
    """Sign file with GPG"""
    try:
        if not output_path:
            output_path = f"{file_path}.sig"
        
        cmd = ['gpg', '--detach-sign', '--output', output_path, file_path]
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        return f"Signed {file_path} to {output_path}" if result.returncode == 0 else f"Error: {result.stderr}"
    except FileNotFoundError:
        return "Error: GPG not installed. Install with: brew install gnupg"
    except Exception as e:
        return f"Error: {e}"

def gpg_verify_file(file_path, sig_path=None):
    """Verify file signature"""
    try:
        if not sig_path:
            sig_path = f"{file_path}.sig"
        
        cmd = ['gpg', '--verify', sig_path, file_path]
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        return "Signature verified" if result.returncode == 0 else f"Error: {result.stderr}"
    except FileNotFoundError:
        return "Error: GPG not installed. Install with: brew install gnupg"
    except Exception as e:
        return f"Error: {e}"

def gpg_list_keys():
    """List GPG keys"""
    try:
        cmd = ['gpg', '--list-keys', '--with-colons']
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            return f"Error: {result.stderr}"
        
        keys = []
        for line in result.stdout.split('\n'):
            if line.startswith('pub:'):
                parts = line.split(':')
                keys.append({
                    'keyid': parts[4][-8:],
                    'algorithm': parts[3],
                    'created': parts[5]
                })
            elif line.startswith('uid:') and keys:
                keys[-1]['uid'] = parts[9]
        
        return keys
    except FileNotFoundError:
        return "Error: GPG not installed. Install with: brew install gnupg"
    except Exception as e:
        return f"Error: {e}"

def gpg_generate_key(name, email, passphrase=""):
    """Generate GPG key pair"""
    try:
        key_params = f"""
Key-Type: RSA
Key-Length: 4096
Name-Real: {name}
Name-Email: {email}
Expire-Date: 0
Passphrase: {passphrase}
%commit
"""
        
        cmd = ['gpg', '--batch', '--generate-key']
        result = subprocess.run(cmd, input=key_params, capture_output=True, text=True)
        
        return "Key generated successfully" if result.returncode == 0 else f"Error: {result.stderr}"
    except FileNotFoundError:
        return "Error: GPG not installed. Install with: brew install gnupg"
    except Exception as e:
        return f"Error: {e}"

def gpg_export_key(keyid, output_path=None, armor=True):
    """Export GPG public key"""
    try:
        if not output_path:
            output_path = f"{keyid}.asc" if armor else f"{keyid}.gpg"
        
        cmd = ['gpg', '--export', '--output', output_path]
        if armor:
            cmd.append('--armor')
        cmd.append(keyid)
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        return f"Exported key {keyid} to {output_path}" if result.returncode == 0 else f"Error: {result.stderr}"
    except FileNotFoundError:
        return "Error: GPG not installed. Install with: brew install gnupg"
    except Exception as e:
        return f"Error: {e}"

def gpg_import_key(key_file):
    """Import GPG key"""
    try:
        cmd = ['gpg', '--import', key_file]
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        return "Key imported successfully" if result.returncode == 0 else f"Error: {result.stderr}"
    except FileNotFoundError:
        return "Error: GPG not installed. Install with: brew install gnupg"
    except Exception as e:
        return f"Error: {e}"