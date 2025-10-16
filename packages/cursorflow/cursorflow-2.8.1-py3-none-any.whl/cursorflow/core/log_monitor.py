"""
Universal Log Monitor

Coordinates different log sources (SSH, local files, Docker, etc.)
and provides a unified interface for log collection and filtering.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta

class LogMonitor:
    """Universal log monitoring coordinator"""
    
    def __init__(self, log_source_type: str, config: Dict):
        """
        Initialize log monitor with specified source type
        
        Args:
            log_source_type: Type of log source ('ssh', 'local', 'docker', 'systemd')
            config: Configuration for the log source
        """
        self.log_source_type = log_source_type
        self.config = config
        self.log_source = None
        self.monitoring = False
        
        self.logger = logging.getLogger(__name__)
        
        # Load appropriate log source
        self._load_log_source()
    
    def _load_log_source(self):
        """Dynamically load the appropriate log source"""
        
        source_map = {
            'ssh': ('ssh_remote', 'SSHRemoteLogSource'),
            'local': ('local_file', 'LocalFileLogSource'),
            'docker': ('docker_logs', 'DockerLogSource'),
            'systemd': ('systemd_logs', 'SystemdLogSource')
        }
        
        if self.log_source_type not in source_map:
            raise ValueError(f"Unsupported log source type: {self.log_source_type}")
        
        module_name, class_name = source_map[self.log_source_type]
        
        try:
            # Dynamic import
            module = __import__(f"..log_sources.{module_name}", fromlist=[class_name], level=1)
            source_class = getattr(module, class_name)
            
            # Initialize with config
            if self.log_source_type == 'ssh':
                self.log_source = source_class(
                    self.config.get('ssh_config', {}),
                    self.config.get('log_paths', {})
                )
            elif self.log_source_type == 'local':
                self.log_source = source_class(
                    self.config.get('log_paths', {})
                )
            else:
                self.log_source = source_class(self.config)
                
        except ImportError as e:
            raise ImportError(f"Log source {self.log_source_type} not available: {e}")
    
    async def start_monitoring(self) -> bool:
        """Start log monitoring"""
        
        if self.monitoring:
            return True
            
        self.logger.info(f"Starting {self.log_source_type} log monitoring")
        
        success = await self.log_source.start_monitoring()
        self.monitoring = success
        
        return success
    
    async def stop_monitoring(self) -> List[Dict]:
        """Stop monitoring and return all collected logs"""
        
        if not self.monitoring:
            return []
            
        self.logger.info("Stopping log monitoring")
        
        logs = await self.log_source.stop_monitoring()
        self.monitoring = False
        
        return logs
    
    def get_recent_logs(self, seconds: int = 10) -> List[Dict]:
        """Get recent log entries without stopping monitoring"""
        
        if not self.monitoring or not self.log_source:
            return []
            
        return self.log_source.get_recent_logs(seconds)
    
    def filter_logs(self, logs: List[Dict], filters: Dict) -> List[Dict]:
        """Filter logs based on criteria"""
        
        filtered = logs
        
        # Filter by time range
        if 'since' in filters:
            since_time = filters['since']
            if isinstance(since_time, str):
                # Parse string to datetime
                since_time = datetime.fromisoformat(since_time)
            filtered = [log for log in filtered if log['timestamp'] >= since_time]
        
        # Filter by log source
        if 'source' in filters:
            source = filters['source']
            filtered = [log for log in filtered if log['source'] == source]
        
        # Filter by content pattern
        if 'pattern' in filters:
            import re
            pattern = filters['pattern']
            filtered = [log for log in filtered if re.search(pattern, log['content'], re.IGNORECASE)]
        
        # Filter by severity (if log source provides it)
        if 'severity' in filters:
            severity = filters['severity']
            filtered = [log for log in filtered if log.get('severity') == severity]
        
        return filtered
    
    def categorize_logs(self, logs: List[Dict], error_patterns: Dict) -> Dict[str, List[Dict]]:
        """Categorize logs by error patterns"""
        
        categorized = {
            'errors': [],
            'warnings': [],
            'info': [],
            'unknown': []
        }
        
        for log_entry in logs:
            content = log_entry['content']
            categorized_entry = log_entry.copy()
            
            # Try to match against error patterns
            matched = False
            for pattern_name, pattern_config in error_patterns.items():
                if re.search(pattern_config['regex'], content):
                    categorized_entry['error_type'] = pattern_name
                    categorized_entry['severity'] = pattern_config['severity']
                    categorized_entry['description'] = pattern_config['description']
                    categorized_entry['suggested_fix'] = pattern_config['suggested_fix']
                    
                    # Categorize by severity
                    if pattern_config['severity'] in ['critical', 'high']:
                        categorized['errors'].append(categorized_entry)
                    elif pattern_config['severity'] == 'medium':
                        categorized['warnings'].append(categorized_entry)
                    else:
                        categorized['info'].append(categorized_entry)
                    
                    matched = True
                    break
            
            if not matched:
                # Basic severity detection from log content
                content_lower = content.lower()
                if any(word in content_lower for word in ['error', 'failed', 'exception', 'critical']):
                    categorized['errors'].append(categorized_entry)
                elif any(word in content_lower for word in ['warning', 'warn']):
                    categorized['warnings'].append(categorized_entry)
                else:
                    categorized['info'].append(categorized_entry)
        
        return categorized
