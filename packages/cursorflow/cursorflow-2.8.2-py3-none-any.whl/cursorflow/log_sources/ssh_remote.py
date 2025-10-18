"""
SSH Remote Log Source

Monitors log files on remote servers via SSH connection.
Supports real-time tailing of multiple log files simultaneously.
"""

import paramiko
import threading
import queue
import time
import logging
import re
from typing import Dict, List, Optional
from datetime import datetime, timedelta

class SSHRemoteLogSource:
    """Remote log monitoring via SSH"""
    
    def __init__(self, ssh_config: Dict, log_paths: Dict[str, str]):
        """
        Initialize SSH log monitoring
        
        Args:
            ssh_config: SSH connection configuration
                {
                    'hostname': 'server.example.com',
                    'username': 'deploy',
                    'key_filename': '/path/to/key',
                    'password': 'optional_password',
                    'port': 22
                }
            log_paths: Dictionary mapping log names to paths
                {
                    'apache_error': '/var/log/httpd/error_log',
                    'apache_access': '/var/log/httpd/access_log',
                    'app_debug': '/tmp/app_debug.log'
                }
        """
        self.ssh_config = ssh_config
        self.log_paths = log_paths
        self.log_queue = queue.Queue()
        self.ssh_client = None
        self.monitoring_threads = []
        self.monitoring = False
        # Note: connect() method implemented below for compatibility
        
        self.logger = logging.getLogger(__name__)
        
    async def start_monitoring(self) -> bool:
        """Start monitoring all configured log files"""
        
        if self.monitoring:
            self.logger.warning("Log monitoring already started")
            return False
            
        self.monitoring = True
        self.logger.info(f"Starting SSH log monitoring for {len(self.log_paths)} log files")
        
        # Test SSH connection first
        if not self._test_ssh_connection():
            self.logger.error("Failed to establish SSH connection")
            return False
        
        # Start monitoring thread for each log file
        for log_name, log_path in self.log_paths.items():
            thread = threading.Thread(
                target=self._monitor_single_log,
                args=(log_name, log_path),
                daemon=True
            )
            thread.start()
            self.monitoring_threads.append(thread)
            
        self.logger.info("All log monitoring threads started")
        return True
    
    def _test_ssh_connection(self) -> bool:
        """Test SSH connection before starting monitoring"""
        try:
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(**self.ssh_config)
            
            # Test basic command
            stdin, stdout, stderr = ssh.exec_command('echo "test"')
            result = stdout.read().decode().strip()
            ssh.close()
            
            return result == 'test'
            
        except Exception as e:
            # Log SSH connection issues as debug for non-critical cases
            if "Connection refused" in str(e) or "timeout" in str(e).lower():
                self.logger.debug(f"SSH connection issue (may be expected): {e}")
            else:
                self.logger.error(f"SSH connection test failed: {e}")
            return False
    
    def _monitor_single_log(self, log_name: str, log_path: str):
        """Monitor a single log file via SSH"""
        
        self.logger.info(f"Starting monitoring for {log_name}: {log_path}")
        
        ssh = None
        try:
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(**self.ssh_config)
            
            # Use tail -F to follow log file
            stdin, stdout, stderr = ssh.exec_command(f'tail -F {log_path}')
            
            # Read lines as they come in
            for line in iter(stdout.readline, ""):
                if not self.monitoring:
                    break
                    
                log_entry = {
                    'timestamp': datetime.now(),
                    'source': log_name,
                    'content': line.strip(),
                    'log_path': log_path,
                    'source_type': 'ssh_remote'
                }
                
                self.log_queue.put(log_entry)
                
        except Exception as e:
            self.logger.error(f"Error monitoring {log_name}: {e}")
            
        finally:
            if ssh:
                ssh.close()
            self.logger.info(f"Stopped monitoring {log_name}")
    
    async def stop_monitoring(self) -> List[Dict]:
        """Stop monitoring and return collected logs"""
        
        if not self.monitoring:
            return []
            
        self.monitoring = False
        self.logger.info("Stopping log monitoring...")
        
        # Wait for threads to finish (with timeout)
        for thread in self.monitoring_threads:
            thread.join(timeout=2.0)
        
        # Collect all queued log entries
        logs = []
        while not self.log_queue.empty():
            try:
                log_entry = self.log_queue.get_nowait()
                logs.append(log_entry)
            except queue.Empty:
                break
        
        self.monitoring_threads.clear()
        self.logger.info(f"Log monitoring stopped. Collected {len(logs)} log entries")
        
        return logs
    
    async def connect(self):
        """Connect to SSH log sources - compatibility method for log_collector"""
        return await self.start_monitoring()
    
    async def disconnect(self):
        """Disconnect from SSH log sources - compatibility method for log_collector"""
        return await self.stop_monitoring()
    
    async def get_new_entries(self) -> List[Dict]:
        """
        Get new log entries since last call (required interface method)
        
        Returns:
            List of log entry dicts with timestamp, content, source
        """
        new_entries = []
        
        # Drain queue of all available entries
        while not self.log_queue.empty():
            try:
                log_entry = self.log_queue.get_nowait()
                new_entries.append(log_entry)
            except queue.Empty:
                break
        
        return new_entries
    
    def get_recent_logs(self, seconds: int = 10) -> List[Dict]:
        """Get logs from the last N seconds without stopping monitoring"""
        
        cutoff_time = datetime.now() - timedelta(seconds=seconds)
        recent_logs = []
        
        # Create temporary list to avoid modifying queue during iteration
        temp_logs = []
        while not self.log_queue.empty():
            try:
                log_entry = self.log_queue.get_nowait()
                temp_logs.append(log_entry)
            except queue.Empty:
                break
        
        # Filter recent logs and put back in queue
        for log_entry in temp_logs:
            if log_entry['timestamp'] >= cutoff_time:
                recent_logs.append(log_entry)
            # Put back in queue
            self.log_queue.put(log_entry)
            
        return recent_logs
    
    def search_logs(self, pattern: str, log_source: Optional[str] = None) -> List[Dict]:
        """Search for pattern in collected logs"""
        
        # Get all current logs
        all_logs = []
        temp_logs = []
        
        while not self.log_queue.empty():
            try:
                log_entry = self.log_queue.get_nowait()
                temp_logs.append(log_entry)
            except queue.Empty:
                break
        
        # Search and restore
        matches = []
        for log_entry in temp_logs:
            # Filter by log source if specified
            if log_source and log_entry['source'] != log_source:
                self.log_queue.put(log_entry)
                continue
                
            # Search for pattern
            if re.search(pattern, log_entry['content'], re.IGNORECASE):
                matches.append(log_entry)
                
            # Put back in queue
            self.log_queue.put(log_entry)
            
        return matches
