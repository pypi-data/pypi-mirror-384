"""
Universal Log Collector

Framework-agnostic log monitoring that works with any log source:
SSH remote, local files, Docker containers, cloud services.
"""

import asyncio
import time
import re
from typing import Dict, List, Optional, Any
from datetime import datetime
import logging
from pathlib import Path

from ..log_sources.ssh_remote import SSHRemoteLogSource
from ..log_sources.local_file import LocalFileLogSource


class LogCollector:
    """
    Universal log collection - works with any backend technology
    
    Supports multiple log sources simultaneously and provides
    unified interface for correlation with browser events.
    """
    
    def __init__(self, config: Dict):
        """
        Initialize log collector with source configuration
        
        Args:
            config: {
                "source": "ssh|local|docker|cloud",
                "host": "server.com",  # for SSH
                "user": "deploy",      # for SSH  
                "key_file": "~/.ssh/key", # for SSH
                "paths": ["/var/log/app.log", "logs/error.log"],
                "containers": ["app", "nginx"]  # for Docker
            }
        """
        self.config = config
        self.source_type = config.get("source", "local")
        self.log_sources = []
        self.monitoring = False
        self.collected_logs = []
        
        self.logger = logging.getLogger(__name__)
        
        # Initialize log sources
        self._initialize_sources()
    
    def _initialize_sources(self):
        """Initialize appropriate log sources based on configuration"""
        try:
            if self.source_type == "ssh":
                self._init_ssh_sources()
            elif self.source_type == "local":
                self._init_local_sources()
            elif self.source_type == "docker":
                self._init_docker_sources()
            elif self.source_type == "cloud":
                self._init_cloud_sources()
            else:
                raise ValueError(f"Unsupported log source type: {self.source_type}")
                
            self.logger.info(f"Initialized {len(self.log_sources)} log sources ({self.source_type})")
            
        except Exception as e:
            self.logger.error(f"Log source initialization failed: {e}")
            raise
    
    def _init_ssh_sources(self):
        """Initialize SSH remote log sources"""
        ssh_config = {
            "hostname": self.config.get("host"),
            "username": self.config.get("user", "deploy"),
            "key_filename": self.config.get("key_file")
        }
        
        paths = self.config.get("paths", [])
        for path in paths:
            source = SSHRemoteLogSource(ssh_config, path)
            self.log_sources.append(source)
    
    def _init_local_sources(self):
        """Initialize local file log sources"""
        paths = self.config.get("paths", ["logs/app.log"])
        
        # Skip local log sources if we're clearly testing a remote URL
        # (they won't work anyway and just cause confusing errors)
        base_url = self.config.get("base_url", "")
        if base_url and (base_url.startswith("http://") or base_url.startswith("https://")):
            if not any("localhost" in base_url or "127.0.0.1" in base_url for url in [base_url]):
                self.logger.debug("Skipping local log sources for remote URL testing")
                return
        
        for path in paths:
            if Path(path).exists() or self.config.get("create_if_missing", True):
                source = LocalFileLogSource(path)
                self.log_sources.append(source)
            else:
                self.logger.debug(f"Log file not found: {path}")
    
    def _init_docker_sources(self):
        """Initialize Docker container log sources"""
        containers = self.config.get("containers", [])
        
        for container in containers:
            try:
                source = DockerLogSource(container)
                self.log_sources.append(source)
            except Exception as e:
                self.logger.warning(f"Docker container {container} not available: {e}")
    
    def _init_cloud_sources(self):
        """Initialize cloud log sources (AWS, GCP, Azure)"""
        provider = self.config.get("provider", "aws")
        
        if provider == "aws":
            source = AWSCloudWatchSource(self.config)
            self.log_sources.append(source)
        elif provider == "gcp":
            source = GCPLoggingSource(self.config)
            self.log_sources.append(source)
        else:
            raise ValueError(f"Unsupported cloud provider: {provider}")
    
    async def start_monitoring(self):
        """Start monitoring all configured log sources"""
        if self.monitoring:
            return
        
        self.monitoring = True
        self.collected_logs = []
        
        try:
            # Start all log sources
            tasks = []
            for source in self.log_sources:
                task = asyncio.create_task(self._monitor_source(source))
                tasks.append(task)
            
            self.logger.info(f"Started monitoring {len(self.log_sources)} log sources")
            
            # Let monitoring run (don't await tasks - they run continuously)
            
        except Exception as e:
            self.logger.error(f"Failed to start log monitoring: {e}")
            raise
    
    async def stop_monitoring(self) -> List[Dict]:
        """Stop monitoring and return collected logs"""
        if not self.monitoring:
            return []
        
        self.monitoring = False
        
        try:
            # Stop all sources
            for source in self.log_sources:
                if hasattr(source, 'stop'):
                    await source.stop()
            
            self.logger.info(f"Stopped monitoring. Collected {len(self.collected_logs)} log entries")
            return self.collected_logs.copy()
            
        except Exception as e:
            self.logger.error(f"Failed to stop log monitoring: {e}")
            return self.collected_logs.copy()
    
    async def _monitor_source(self, source):
        """Monitor a single log source"""
        try:
            # connect() returns bool, not awaitable - just call it
            connected = await source.connect()
            if not connected:
                self.logger.warning(f"Log source {source} failed to connect")
                return
            
            while self.monitoring:
                try:
                    # Get new log entries
                    entries = await source.get_new_entries()
                    
                    for entry in entries:
                        processed_entry = self._process_log_entry(entry, source)
                        self.collected_logs.append(processed_entry)
                    
                    # Brief pause to avoid overwhelming
                    await asyncio.sleep(0.1)
                    
                except AttributeError as e:
                    # Log source doesn't support get_new_entries (incompatible source type)
                    self.logger.debug(f"Log source {source} is incompatible: {e}")
                    break  # Stop monitoring this source
                except Exception as e:
                    self.logger.debug(f"Log source error: {e}")
                    await asyncio.sleep(1)  # Wait before retry
                    
        except Exception as e:
            self.logger.error(f"Log source monitoring failed: {e}")
        finally:
            try:
                await source.disconnect()
            except:
                pass
    
    def _process_log_entry(self, entry: str, source) -> Dict:
        """Process raw log entry into structured format"""
        timestamp = time.time()
        
        # Parse timestamp from log entry if present
        parsed_timestamp = self._extract_timestamp(entry)
        if parsed_timestamp:
            timestamp = parsed_timestamp
        
        # Classify log level
        level = self._classify_log_level(entry)
        
        # Extract relevant information
        processed = {
            "timestamp": timestamp,
            "source": getattr(source, 'name', str(source)),
            "source_type": self.source_type,
            "level": level,
            "content": entry.strip(),
            "raw": entry
        }
        
        # Add error classification if it's an error
        if level in ["error", "critical"]:
            processed["error_type"] = self._classify_error_type(entry)
        
        return processed
    
    def _extract_timestamp(self, entry: str) -> Optional[float]:
        """Extract timestamp from log entry"""
        # Common timestamp patterns
        patterns = [
            # Apache/Nginx: [Mon Dec 04 15:30:45 2023]
            r'\[([A-Za-z]{3} [A-Za-z]{3} \d{2} \d{2}:\d{2}:\d{2} \d{4})\]',
            # ISO format: 2023-12-04T15:30:45.123Z
            r'(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{3})?Z?)',
            # Simple format: 2023-12-04 15:30:45
            r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, entry)
            if match:
                try:
                    timestamp_str = match.group(1)
                    # Convert to Unix timestamp
                    if 'T' in timestamp_str:
                        dt = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                    else:
                        dt = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
                    return dt.timestamp()
                except:
                    continue
        
        return None
    
    def _classify_log_level(self, entry: str) -> str:
        """Classify log entry level"""
        entry_lower = entry.lower()
        
        if any(word in entry_lower for word in ['error', 'failed', 'exception', 'fatal']):
            return "error"
        elif any(word in entry_lower for word in ['warning', 'warn']):
            return "warning"
        elif any(word in entry_lower for word in ['info', 'information']):
            return "info"
        elif any(word in entry_lower for word in ['debug', 'trace']):
            return "debug"
        else:
            return "info"
    
    def _classify_error_type(self, entry: str) -> str:
        """Classify type of error for better correlation"""
        entry_lower = entry.lower()
        
        # Database errors
        if any(word in entry_lower for word in ['mysql', 'postgres', 'database', 'sql', 'dbd']):
            return "database"
        
        # Authentication errors
        elif any(word in entry_lower for word in ['auth', 'login', 'permission', 'unauthorized']):
            return "authentication"
        
        # Network errors
        elif any(word in entry_lower for word in ['connection', 'network', 'timeout', 'refused']):
            return "network"
        
        # File system errors
        elif any(word in entry_lower for word in ['file', 'permission', 'not found', 'locate']):
            return "filesystem"
        
        # Application errors
        elif any(word in entry_lower for word in ['can\'t', 'cannot', 'undefined', 'null']):
            return "application"
        
        else:
            return "general"
    
    def get_logs_in_timeframe(self, start_time: float, end_time: float) -> List[Dict]:
        """Get logs within specific timeframe for correlation"""
        matching_logs = []
        
        for log_entry in self.collected_logs:
            timestamp = log_entry.get("timestamp", 0)
            if start_time <= timestamp <= end_time:
                matching_logs.append(log_entry)
        
        return matching_logs
    
    def get_error_logs_since(self, since_time: float) -> List[Dict]:
        """Get error logs since specific time"""
        error_logs = []
        
        for log_entry in self.collected_logs:
            if (log_entry.get("timestamp", 0) >= since_time and 
                log_entry.get("level") in ["error", "critical"]):
                error_logs.append(log_entry)
        
        return error_logs


# Docker log source implementation
class DockerLogSource:
    """Log source for Docker containers"""
    
    def __init__(self, container_name: str):
        self.container_name = container_name
        self.name = f"docker:{container_name}"
        self.process = None
        
    async def connect(self):
        """Connect to Docker container logs"""
        try:
            import subprocess
            self.process = await asyncio.create_subprocess_exec(
                "docker", "logs", "-f", self.container_name,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT
            )
        except Exception as e:
            raise Exception(f"Failed to connect to Docker container {self.container_name}: {e}")
    
    async def get_new_entries(self) -> List[str]:
        """Get new log entries from Docker container"""
        if not self.process:
            return []
        
        try:
            # Read with timeout
            line = await asyncio.wait_for(
                self.process.stdout.readline(), 
                timeout=1.0
            )
            
            if line:
                return [line.decode('utf-8', errors='ignore')]
            else:
                return []
                
        except asyncio.TimeoutError:
            return []
        except Exception:
            return []
    
    async def disconnect(self):
        """Disconnect from Docker logs"""
        if self.process:
            try:
                self.process.terminate()
                await self.process.wait()
            except:
                pass


# AWS CloudWatch source implementation
class AWSCloudWatchSource:
    """Log source for AWS CloudWatch"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.name = f"aws:{config.get('log_group', 'unknown')}"
        
    async def connect(self):
        """Connect to AWS CloudWatch"""
        # Implementation would use boto3
        pass
    
    async def get_new_entries(self) -> List[str]:
        """Get new entries from CloudWatch"""
        # Implementation would query CloudWatch logs
        return []
    
    async def disconnect(self):
        """Disconnect from CloudWatch"""
        pass


# GCP Logging source implementation  
class GCPLoggingSource:
    """Log source for Google Cloud Logging"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.name = f"gcp:{config.get('project_id', 'unknown')}"
        
    async def connect(self):
        """Connect to GCP Logging"""
        # Implementation would use google-cloud-logging
        pass
    
    async def get_new_entries(self) -> List[str]:
        """Get new entries from GCP Logging"""
        # Implementation would query GCP logs
        return []
    
    async def disconnect(self):
        """Disconnect from GCP Logging"""
        pass
