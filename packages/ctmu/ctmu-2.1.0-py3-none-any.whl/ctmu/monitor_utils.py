"""System monitoring utilities"""

import subprocess
import psutil
import time

def cpu_usage():
    """Get CPU usage percentage"""
    return psutil.cpu_percent(interval=1)

def memory_usage():
    """Get memory usage information"""
    mem = psutil.virtual_memory()
    return {
        'total': f"{mem.total // (1024**3)}GB",
        'available': f"{mem.available // (1024**3)}GB",
        'used': f"{mem.used // (1024**3)}GB",
        'percentage': f"{mem.percent}%"
    }

def disk_usage(path='/'):
    """Get disk usage for path"""
    usage = psutil.disk_usage(path)
    return {
        'total': f"{usage.total // (1024**3)}GB",
        'used': f"{usage.used // (1024**3)}GB",
        'free': f"{usage.free // (1024**3)}GB",
        'percentage': f"{(usage.used / usage.total) * 100:.1f}%"
    }

def network_stats():
    """Get network statistics"""
    stats = psutil.net_io_counters()
    return {
        'bytes_sent': f"{stats.bytes_sent // (1024**2)}MB",
        'bytes_recv': f"{stats.bytes_recv // (1024**2)}MB",
        'packets_sent': stats.packets_sent,
        'packets_recv': stats.packets_recv
    }

def top_processes(count=10):
    """Get top processes by CPU usage"""
    processes = []
    for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
        try:
            processes.append(proc.info)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    
    return sorted(processes, key=lambda x: x['cpu_percent'] or 0, reverse=True)[:count]

def port_listeners():
    """Get processes listening on ports"""
    listeners = []
    for conn in psutil.net_connections(kind='inet'):
        if conn.status == 'LISTEN':
            try:
                proc = psutil.Process(conn.pid) if conn.pid else None
                listeners.append({
                    'port': conn.laddr.port,
                    'address': conn.laddr.ip,
                    'pid': conn.pid,
                    'process': proc.name() if proc else 'Unknown'
                })
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
    
    return sorted(listeners, key=lambda x: x['port'])

def system_uptime():
    """Get system uptime"""
    try:
        uptime_seconds = time.time() - psutil.boot_time()
        days = int(uptime_seconds // 86400)
        hours = int((uptime_seconds % 86400) // 3600)
        minutes = int((uptime_seconds % 3600) // 60)
        return f"{days}d {hours}h {minutes}m"
    except Exception as e:
        return f"Error: {e}"