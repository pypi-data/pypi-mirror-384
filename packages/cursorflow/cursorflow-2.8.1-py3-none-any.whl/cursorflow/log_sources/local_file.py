"""
Local File Log Source

Monitors local log files using file watching and subprocess tail.
Perfect for development environments and local testing.
"""

import subprocess
import threading
import queue
import time
import os
from typing import Dict, List, Optional
from datetime import datetime
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class LocalFileLogSource:
    """Local log file monitoring"""
    
    def __init__(self, log_paths: Dict[str, str]):
        """
        Initialize local log monitoring
        
        Args:
            log_paths: Dictionary mapping log names to local file paths
                {
                    'app_server': 'logs/app.log',
                    'database': 'logs/db.log',
                    'next_server': '.next/trace.log'
                }
        """
        # Handle case where log_paths is a string instead of dict
        if isinstance(log_paths, str):
            self.log_paths = {"default": log_paths}
        elif isinstance(log_paths, list):
            self.log_paths = {f"log_{i}": path for i, path in enumerate(log_paths)}
        else:
            self.log_paths = log_paths
        self.log_queue = queue.Queue()
        self.tail_processes = {}
        self.monitoring = False
        # Note: connect() method implemented below for compatibility
        
        import logging
        self.logger = logging.getLogger(__name__)
        
    async def start_monitoring(self) -> bool:
        """Start monitoring all configured log files"""
        
        if self.monitoring:
            self.logger.warning("Log monitoring already started")
            return False
            
        self.monitoring = True
        self.logger.info(f"Starting local log monitoring for {len(self.log_paths)} log files")
        
        # Verify all log files exist or can be created
        for log_name, log_path in self.log_paths.items():
            if not os.path.exists(log_path):
                # Try to create directory
                os.makedirs(os.path.dirname(log_path), exist_ok=True)
                # Touch file if it doesn't exist
                if not os.path.exists(log_path):
                    with open(log_path, 'a'):
                        pass
        
        # Start tail process for each log file
        for log_name, log_path in self.log_paths.items():
            success = self._start_tail_process(log_name, log_path)
            if not success:
                self.logger.error(f"Failed to start monitoring {log_name}")
                
        return len(self.tail_processes) > 0
    
    def _start_tail_process(self, log_name: str, log_path: str) -> bool:
        """Start tail process for a single log file"""
        
        try:
            # Use tail -F to follow file even if it's rotated
            process = subprocess.Popen(
                ['tail', '-F', log_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True,
                bufsize=1
            )
            
            # Start thread to read output
            thread = threading.Thread(
                target=self._read_tail_output,
                args=(log_name, log_path, process),
                daemon=True
            )
            thread.start()
            
            self.tail_processes[log_name] = {
                'process': process,
                'thread': thread,
                'log_path': log_path
            }
            
            self.logger.info(f"Started tail process for {log_name}")
            return True
            
        except Exception as e:
            # Log as debug instead of error for non-critical issues
            if "No such file or directory" in str(e) or "Permission denied" in str(e):
                self.logger.debug(f"Non-critical log file issue for {log_name}: {e}")
            else:
                self.logger.error(f"Failed to start tail for {log_name}: {e}")
            return False
    
    def _read_tail_output(self, log_name: str, log_path: str, process: subprocess.Popen):
        """Read output from tail process"""
        
        try:
            for line in iter(process.stdout.readline, ''):
                if not self.monitoring:
                    break
                    
                if line.strip():  # Skip empty lines
                    log_entry = {
                        'timestamp': datetime.now(),
                        'source': log_name,
                        'content': line.strip(),
                        'log_path': log_path,
                        'source_type': 'local_file'
                    }
                    
                    self.log_queue.put(log_entry)
                    
        except Exception as e:
            self.logger.error(f"Error reading tail output for {log_name}: {e}")
        
        finally:
            process.terminate()
    
    async def stop_monitoring(self) -> List[Dict]:
        """Stop monitoring and return collected logs"""
        
        if not self.monitoring:
            return []
            
        self.monitoring = False
        self.logger.info("Stopping local log monitoring...")
        
        # Stop all tail processes
        for log_name, process_info in self.tail_processes.items():
            process_info['process'].terminate()
            process_info['thread'].join(timeout=2.0)
            
        # Collect all queued log entries
        logs = []
        while not self.log_queue.empty():
            try:
                log_entry = self.log_queue.get_nowait()
                logs.append(log_entry)
            except queue.Empty:
                break
        
        self.tail_processes.clear()
        self.logger.info(f"Local log monitoring stopped. Collected {len(logs)} log entries")
        
        return logs
    
    async def connect(self):
        """Connect to log sources - compatibility method for log_collector"""
        return await self.start_monitoring()
    
    async def disconnect(self):
        """Disconnect from log sources - compatibility method for log_collector"""
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
        """Get logs from the last N seconds (non-destructive)"""
        from datetime import timedelta
        
        cutoff_time = datetime.now() - timedelta(seconds=seconds)
        recent_logs = []
        
        # Non-destructive queue iteration
        temp_logs = []
        while not self.log_queue.empty():
            try:
                log_entry = self.log_queue.get_nowait()
                temp_logs.append(log_entry)
            except queue.Empty:
                break
        
        # Filter and restore
        for log_entry in temp_logs:
            if log_entry['timestamp'] >= cutoff_time:
                recent_logs.append(log_entry)
            self.log_queue.put(log_entry)
            
        return recent_logs
    
    def tail_file_directly(self, file_path: str, lines: int = 50) -> List[str]:
        """Get last N lines from a file directly (one-time read)"""
        
        try:
            result = subprocess.run(
                ['tail', '-n', str(lines), file_path],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                return result.stdout.strip().split('\n')
            else:
                self.logger.error(f"tail command failed: {result.stderr}")
                return []
                
        except Exception as e:
            self.logger.error(f"Error reading file {file_path}: {e}")
            return []
