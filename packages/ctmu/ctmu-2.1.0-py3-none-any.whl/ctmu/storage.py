"""Storage utilities for S3 and Nextcloud"""

import os
import json
from pathlib import Path

# S3 Functions
def s3_upload(file_path, bucket, key=None, profile=None):
    """Upload file to S3"""
    try:
        import boto3
        session = boto3.Session(profile_name=profile) if profile else boto3.Session()
        s3 = session.client('s3')
        
        if not key:
            key = Path(file_path).name
        
        s3.upload_file(file_path, bucket, key)
        return f"Uploaded {file_path} to s3://{bucket}/{key}"
    except ImportError:
        return "Error: boto3 not installed. Run: pip install boto3"
    except Exception as e:
        return f"Error: {e}"

def s3_download(bucket, key, local_path=None, profile=None):
    """Download file from S3"""
    try:
        import boto3
        session = boto3.Session(profile_name=profile) if profile else boto3.Session()
        s3 = session.client('s3')
        
        if not local_path:
            local_path = key.split('/')[-1]
        
        s3.download_file(bucket, key, local_path)
        return f"Downloaded s3://{bucket}/{key} to {local_path}"
    except ImportError:
        return "Error: boto3 not installed. Run: pip install boto3"
    except Exception as e:
        return f"Error: {e}"

def s3_list(bucket, prefix="", profile=None):
    """List S3 bucket contents"""
    try:
        import boto3
        session = boto3.Session(profile_name=profile) if profile else boto3.Session()
        s3 = session.client('s3')
        
        response = s3.list_objects_v2(Bucket=bucket, Prefix=prefix)
        objects = []
        
        if 'Contents' in response:
            for obj in response['Contents']:
                objects.append({
                    'Key': obj['Key'],
                    'Size': obj['Size'],
                    'Modified': obj['LastModified'].isoformat()
                })
        
        return objects
    except ImportError:
        return "Error: boto3 not installed. Run: pip install boto3"
    except Exception as e:
        return f"Error: {e}"

def s3_delete(bucket, key, profile=None):
    """Delete file from S3"""
    try:
        import boto3
        session = boto3.Session(profile_name=profile) if profile else boto3.Session()
        s3 = session.client('s3')
        
        s3.delete_object(Bucket=bucket, Key=key)
        return f"Deleted s3://{bucket}/{key}"
    except ImportError:
        return "Error: boto3 not installed. Run: pip install boto3"
    except Exception as e:
        return f"Error: {e}"

# Nextcloud Functions
def nextcloud_upload(file_path, remote_path, url, username, password):
    """Upload file to Nextcloud"""
    try:
        from webdav4.client import Client
        
        client = Client(url, auth=(username, password))
        
        with open(file_path, 'rb') as f:
            client.upload_fileobj(f, remote_path)
        
        return f"Uploaded {file_path} to {remote_path}"
    except ImportError:
        return "Error: webdav4 not installed. Run: pip install webdav4"
    except Exception as e:
        return f"Error: {e}"

def nextcloud_download(remote_path, local_path, url, username, password):
    """Download file from Nextcloud"""
    try:
        from webdav4.client import Client
        
        client = Client(url, auth=(username, password))
        
        with open(local_path, 'wb') as f:
            client.download_fileobj(remote_path, f)
        
        return f"Downloaded {remote_path} to {local_path}"
    except ImportError:
        return "Error: webdav4 not installed. Run: pip install webdav4"
    except Exception as e:
        return f"Error: {e}"

def nextcloud_list(remote_path, url, username, password):
    """List Nextcloud directory contents"""
    try:
        from webdav4.client import Client
        
        client = Client(url, auth=(username, password))
        items = []
        
        for item in client.ls(remote_path):
            items.append({
                'Name': item.name,
                'Path': str(item),
                'Type': 'Directory' if item.is_dir else 'File',
                'Size': getattr(item, 'content_length', 0) if not item.is_dir else 0
            })
        
        return items
    except ImportError:
        return "Error: webdav4 not installed. Run: pip install webdav4"
    except Exception as e:
        return f"Error: {e}"

def nextcloud_delete(remote_path, url, username, password):
    """Delete file from Nextcloud"""
    try:
        from webdav4.client import Client
        
        client = Client(url, auth=(username, password))
        client.remove(remote_path)
        
        return f"Deleted {remote_path}"
    except ImportError:
        return "Error: webdav4 not installed. Run: pip install webdav4"
    except Exception as e:
        return f"Error: {e}"

def nextcloud_mkdir(remote_path, url, username, password):
    """Create directory in Nextcloud"""
    try:
        from webdav4.client import Client
        
        client = Client(url, auth=(username, password))
        client.mkdir(remote_path)
        
        return f"Created directory {remote_path}"
    except ImportError:
        return "Error: webdav4 not installed. Run: pip install webdav4"
    except Exception as e:
        return f"Error: {e}"