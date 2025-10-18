"""
File Change Monitor for Hot Reload Synchronization

Monitors CSS and source file changes to synchronize with browser state,
enabling real-time feedback and improved hot reload detection.
"""

import asyncio
import hashlib
import time
from typing import Dict, List, Optional, Set, Callable, Any
from pathlib import Path
import logging
from dataclasses import dataclass
from enum import Enum


class ChangeType(Enum):
    """Types of file changes to monitor"""
    CSS_CHANGE = "css"
    JS_CHANGE = "javascript" 
    HTML_CHANGE = "html"
    CONFIG_CHANGE = "config"
    ASSET_CHANGE = "asset"


@dataclass
class FileChange:
    """Represents a detected file change"""
    file_path: Path
    change_type: ChangeType
    timestamp: float
    content_hash: str
    change_size: int = 0
    is_hot_reloadable: bool = False


class FileChangeMonitor:
    """
    Monitors file changes to synchronize with browser hot reload
    
    Detects changes in CSS, JS, and other files to:
    1. Predict when hot reload will trigger
    2. Synchronize browser state monitoring
    3. Optimize CSS iteration timing
    4. Provide feedback on hot reload effectiveness
    """
    
    def __init__(
        self, 
        project_root: Optional[Path] = None,
        watch_patterns: Optional[List[str]] = None
    ):
        """
        Initialize file change monitor
        
        Args:
            project_root: Root directory to monitor (defaults to current working directory)
            watch_patterns: File patterns to monitor (defaults to common web dev files)
        """
        self.project_root = project_root or Path.cwd()
        self.watch_patterns = watch_patterns or [
            "**/*.css", "**/*.scss", "**/*.sass", "**/*.less",  # Styles
            "**/*.js", "**/*.jsx", "**/*.ts", "**/*.tsx",      # JavaScript
            "**/*.html", "**/*.htm",                           # HTML
            "**/*.vue", "**/*.svelte",                         # Component files
            "**/package.json", "**/webpack.config.js",        # Config files
            "**/*.json"                                        # Config and data
        ]
        
        # State tracking
        self.file_hashes: Dict[str, str] = {}
        self.last_scan_time = 0
        self.change_history: List[FileChange] = []
        self.is_monitoring = False
        self.monitor_task: Optional[asyncio.Task] = None
        
        # Change callbacks
        self.change_callbacks: List[Callable[[FileChange], None]] = []
        self.hot_reload_callbacks: List[Callable[[List[FileChange]], None]] = []
        
        # Hot reload detection
        self.hot_reload_patterns = {
            ChangeType.CSS_CHANGE: [".css", ".scss", ".sass", ".less"],
            ChangeType.JS_CHANGE: [".js", ".jsx", ".ts", ".tsx"],
            ChangeType.HTML_CHANGE: [".html", ".htm"],
        }
        
        self.logger = logging.getLogger(__name__)
        
        # Exclude patterns to avoid monitoring noise
        self.exclude_patterns = [
            "**/node_modules/**",
            "**/.git/**",
            "**/.cursorflow/**",
            "**/dist/**",
            "**/build/**",
            "**/.next/**",
            "**/coverage/**"
        ]
    
    async def start_monitoring(self, poll_interval: float = 0.5) -> bool:
        """
        Start monitoring file changes
        
        Args:
            poll_interval: How often to check for changes (seconds)
            
        Returns:
            True if monitoring started successfully
        """
        try:
            if self.is_monitoring:
                self.logger.warning("File monitoring already active")
                return True
            
            # Initial scan to establish baseline
            await self._initial_scan()
            
            # Start monitoring task
            self.monitor_task = asyncio.create_task(
                self._monitor_loop(poll_interval)
            )
            
            self.is_monitoring = True
            self.logger.info(f"File change monitoring started for: {self.project_root}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to start file monitoring: {e}")
            return False
    
    async def stop_monitoring(self):
        """Stop monitoring file changes"""
        try:
            self.is_monitoring = False
            
            if self.monitor_task:
                self.monitor_task.cancel()
                try:
                    await self.monitor_task
                except asyncio.CancelledError:
                    pass
                self.monitor_task = None
            
            self.logger.info("File change monitoring stopped")
            
        except Exception as e:
            self.logger.error(f"Error stopping file monitoring: {e}")
    
    def add_change_callback(self, callback: Callable[[FileChange], None]):
        """Add callback for individual file changes"""
        self.change_callbacks.append(callback)
    
    def add_hot_reload_callback(self, callback: Callable[[List[FileChange]], None]):
        """Add callback for hot reload events (batch of related changes)"""
        self.hot_reload_callbacks.append(callback)
    
    async def _initial_scan(self):
        """Perform initial scan to establish file hash baseline"""
        self.logger.debug("Performing initial file scan...")
        
        files_scanned = 0
        for pattern in self.watch_patterns:
            for file_path in self.project_root.glob(pattern):
                if self._should_monitor_file(file_path):
                    try:
                        file_hash = await self._calculate_file_hash(file_path)
                        self.file_hashes[str(file_path)] = file_hash
                        files_scanned += 1
                    except Exception as e:
                        self.logger.debug(f"Error scanning {file_path}: {e}")
        
        self.last_scan_time = time.time()
        self.logger.info(f"Initial scan complete: {files_scanned} files monitored")
    
    async def _monitor_loop(self, poll_interval: float):
        """Main monitoring loop"""
        while self.is_monitoring:
            try:
                changes = await self._scan_for_changes()
                
                if changes:
                    await self._process_changes(changes)
                
                await asyncio.sleep(poll_interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(poll_interval)
    
    async def _scan_for_changes(self) -> List[FileChange]:
        """Scan for file changes since last check"""
        changes = []
        current_time = time.time()
        
        # Check existing files for changes
        for file_path_str, old_hash in list(self.file_hashes.items()):
            file_path = Path(file_path_str)
            
            if not file_path.exists():
                # File was deleted
                del self.file_hashes[file_path_str]
                continue
            
            try:
                new_hash = await self._calculate_file_hash(file_path)
                
                if new_hash != old_hash:
                    # File was modified
                    change = FileChange(
                        file_path=file_path,
                        change_type=self._determine_change_type(file_path),
                        timestamp=current_time,
                        content_hash=new_hash,
                        change_size=self._calculate_change_size(file_path),
                        is_hot_reloadable=self._is_hot_reloadable(file_path)
                    )
                    changes.append(change)
                    self.file_hashes[file_path_str] = new_hash
                    
            except Exception as e:
                self.logger.debug(f"Error checking {file_path}: {e}")
        
        # Check for new files
        for pattern in self.watch_patterns:
            for file_path in self.project_root.glob(pattern):
                if (self._should_monitor_file(file_path) and 
                    str(file_path) not in self.file_hashes):
                    
                    try:
                        file_hash = await self._calculate_file_hash(file_path)
                        self.file_hashes[str(file_path)] = file_hash
                        
                        # New file detected
                        change = FileChange(
                            file_path=file_path,
                            change_type=self._determine_change_type(file_path),
                            timestamp=current_time,
                            content_hash=file_hash,
                            change_size=0,  # New file
                            is_hot_reloadable=self._is_hot_reloadable(file_path)
                        )
                        changes.append(change)
                        
                    except Exception as e:
                        self.logger.debug(f"Error processing new file {file_path}: {e}")
        
        self.last_scan_time = current_time
        return changes
    
    async def _process_changes(self, changes: List[FileChange]):
        """Process detected changes and trigger callbacks"""
        # Add to change history
        self.change_history.extend(changes)
        
        # Keep only recent history (last 100 changes)
        if len(self.change_history) > 100:
            self.change_history = self.change_history[-100:]
        
        # Trigger individual change callbacks
        for change in changes:
            for callback in self.change_callbacks:
                try:
                    callback(change)
                except Exception as e:
                    self.logger.error(f"Error in change callback: {e}")
        
        # Check for hot reload events
        hot_reload_changes = [c for c in changes if c.is_hot_reloadable]
        if hot_reload_changes:
            for callback in self.hot_reload_callbacks:
                try:
                    callback(hot_reload_changes)
                except Exception as e:
                    self.logger.error(f"Error in hot reload callback: {e}")
        
        # Log changes
        for change in changes:
            reload_indicator = "🔥" if change.is_hot_reloadable else "📝"
            self.logger.info(f"{reload_indicator} File changed: {change.file_path.name} ({change.change_type.value})")
    
    async def _calculate_file_hash(self, file_path: Path) -> str:
        """Calculate hash of file content"""
        try:
            # For large files, just check size and mtime for performance
            stat = file_path.stat()
            if stat.st_size > 1024 * 1024:  # 1MB threshold
                return f"large_file_{stat.st_size}_{stat.st_mtime}"
            
            # For smaller files, calculate content hash
            content = file_path.read_bytes()
            return hashlib.md5(content).hexdigest()
            
        except Exception as e:
            self.logger.debug(f"Error calculating hash for {file_path}: {e}")
            return "error"
    
    def _calculate_change_size(self, file_path: Path) -> int:
        """Calculate approximate size of change"""
        try:
            return file_path.stat().st_size
        except Exception:
            return 0
    
    def _determine_change_type(self, file_path: Path) -> ChangeType:
        """Determine the type of change based on file extension"""
        suffix = file_path.suffix.lower()
        
        if suffix in [".css", ".scss", ".sass", ".less"]:
            return ChangeType.CSS_CHANGE
        elif suffix in [".js", ".jsx", ".ts", ".tsx"]:
            return ChangeType.JS_CHANGE
        elif suffix in [".html", ".htm"]:
            return ChangeType.HTML_CHANGE
        elif suffix in [".json"] and "config" in file_path.name.lower():
            return ChangeType.CONFIG_CHANGE
        else:
            return ChangeType.ASSET_CHANGE
    
    def _is_hot_reloadable(self, file_path: Path) -> bool:
        """Determine if file change is likely to trigger hot reload"""
        change_type = self._determine_change_type(file_path)
        
        # CSS files are typically hot reloadable
        if change_type == ChangeType.CSS_CHANGE:
            return True
        
        # JS files may be hot reloadable with HMR
        if change_type == ChangeType.JS_CHANGE:
            # Check for common HMR indicators in project
            return self._project_has_hmr()
        
        # HTML changes typically require full reload
        return False
    
    def _project_has_hmr(self) -> bool:
        """Check if project likely has HMR setup"""
        hmr_indicators = [
            "webpack.config.js",
            "vite.config.js",
            "next.config.js",
            "package.json"  # Check for hot reload dependencies
        ]
        
        for indicator in hmr_indicators:
            if (self.project_root / indicator).exists():
                return True
        
        return False
    
    def _should_monitor_file(self, file_path: Path) -> bool:
        """Check if file should be monitored"""
        if not file_path.is_file():
            return False
        
        # Check exclude patterns
        for pattern in self.exclude_patterns:
            if file_path.match(pattern):
                return False
        
        return True
    
    def get_recent_changes(self, since_seconds: float = 60) -> List[FileChange]:
        """Get changes from the last N seconds"""
        cutoff_time = time.time() - since_seconds
        return [c for c in self.change_history if c.timestamp >= cutoff_time]
    
    def get_hot_reload_changes(self, since_seconds: float = 10) -> List[FileChange]:
        """Get hot reloadable changes from the last N seconds"""
        recent_changes = self.get_recent_changes(since_seconds)
        return [c for c in recent_changes if c.is_hot_reloadable]
    
    def get_change_stats(self) -> Dict[str, Any]:
        """Get statistics about monitored changes"""
        total_changes = len(self.change_history)
        hot_reload_changes = len([c for c in self.change_history if c.is_hot_reloadable])
        
        change_types = {}
        for change in self.change_history:
            change_type = change.change_type.value
            change_types[change_type] = change_types.get(change_type, 0) + 1
        
        return {
            "total_files_monitored": len(self.file_hashes),
            "total_changes_detected": total_changes,
            "hot_reload_changes": hot_reload_changes,
            "hot_reload_percentage": (hot_reload_changes / total_changes * 100) if total_changes > 0 else 0,
            "change_types": change_types,
            "monitoring_duration": time.time() - self.last_scan_time if self.last_scan_time > 0 else 0
        }


class HotReloadSynchronizer:
    """
    Synchronizes file changes with browser hot reload events
    
    Coordinates between file monitoring and browser state to optimize
    CSS iteration timing and provide feedback on hot reload effectiveness.
    """
    
    def __init__(self, file_monitor: FileChangeMonitor):
        """
        Initialize hot reload synchronizer
        
        Args:
            file_monitor: FileChangeMonitor instance
        """
        self.file_monitor = file_monitor
        self.browser_sessions: Dict[str, Any] = {}  # Session ID -> PersistentSession
        self.sync_callbacks: List[Callable[[str, List[FileChange]], None]] = []
        
        self.logger = logging.getLogger(__name__)
        
        # Set up file change monitoring
        self.file_monitor.add_hot_reload_callback(self._on_hot_reload_changes)
    
    def register_browser_session(self, session_id: str, persistent_session):
        """Register a browser session for hot reload synchronization"""
        self.browser_sessions[session_id] = persistent_session
        self.logger.info(f"Registered browser session for hot reload sync: {session_id}")
    
    def unregister_browser_session(self, session_id: str):
        """Unregister a browser session"""
        if session_id in self.browser_sessions:
            del self.browser_sessions[session_id]
            self.logger.info(f"Unregistered browser session: {session_id}")
    
    def add_sync_callback(self, callback: Callable[[str, List[FileChange]], None]):
        """Add callback for synchronized hot reload events"""
        self.sync_callbacks.append(callback)
    
    async def _on_hot_reload_changes(self, changes: List[FileChange]):
        """Handle hot reload changes and sync with browser sessions"""
        if not changes:
            return
        
        self.logger.info(f"Hot reload changes detected: {len(changes)} files")
        
        # Notify all registered browser sessions
        for session_id, session in self.browser_sessions.items():
            try:
                await self._sync_session_with_changes(session_id, session, changes)
            except Exception as e:
                self.logger.error(f"Error syncing session {session_id}: {e}")
        
        # Trigger sync callbacks
        for session_id in self.browser_sessions.keys():
            for callback in self.sync_callbacks:
                try:
                    callback(session_id, changes)
                except Exception as e:
                    self.logger.error(f"Error in sync callback: {e}")
    
    async def _sync_session_with_changes(
        self, 
        session_id: str, 
        session, 
        changes: List[FileChange]
    ):
        """Synchronize a specific browser session with file changes"""
        
        # Check if session can benefit from these changes
        css_changes = [c for c in changes if c.change_type == ChangeType.CSS_CHANGE]
        
        if css_changes and hasattr(session, 'browser') and session.browser:
            # Wait a moment for hot reload to process
            await asyncio.sleep(0.2)
            
            # Check if hot reload is working by monitoring browser state
            try:
                hot_reload_detected = await session._check_hot_reload_capability()
                
                if hot_reload_detected:
                    self.logger.info(f"Hot reload confirmed for session {session_id}")
                    # Update session's hot reload tracking
                    session.last_reload_time = time.time()
                else:
                    self.logger.warning(f"Hot reload not detected for session {session_id}")
                    
            except Exception as e:
                self.logger.debug(f"Error checking hot reload for session {session_id}: {e}")
    
    async def wait_for_hot_reload(
        self, 
        timeout: float = 5.0,
        file_patterns: Optional[List[str]] = None
    ) -> bool:
        """
        Wait for hot reload changes matching specified patterns
        
        Args:
            timeout: Maximum time to wait for changes
            file_patterns: File patterns to wait for (e.g., ["*.css"])
            
        Returns:
            True if matching changes were detected
        """
        start_time = time.time()
        
        while (time.time() - start_time) < timeout:
            recent_changes = self.file_monitor.get_hot_reload_changes(since_seconds=1)
            
            if recent_changes:
                if not file_patterns:
                    return True
                
                # Check if changes match patterns
                for change in recent_changes:
                    for pattern in file_patterns:
                        if change.file_path.match(pattern):
                            return True
            
            await asyncio.sleep(0.1)
        
        return False
    
    def get_sync_stats(self) -> Dict[str, Any]:
        """Get statistics about hot reload synchronization"""
        return {
            "registered_sessions": len(self.browser_sessions),
            "active_sessions": [sid for sid, session in self.browser_sessions.items() 
                              if getattr(session, 'is_active', False)],
            "file_monitor_stats": self.file_monitor.get_change_stats()
        }


# Global instances for easy access
_file_monitor: Optional[FileChangeMonitor] = None
_hot_reload_sync: Optional[HotReloadSynchronizer] = None

def get_file_monitor(project_root: Optional[Path] = None) -> FileChangeMonitor:
    """Get or create global file monitor instance"""
    global _file_monitor
    if _file_monitor is None:
        _file_monitor = FileChangeMonitor(project_root)
    return _file_monitor

def get_hot_reload_synchronizer() -> HotReloadSynchronizer:
    """Get or create global hot reload synchronizer"""
    global _hot_reload_sync, _file_monitor
    if _hot_reload_sync is None:
        if _file_monitor is None:
            _file_monitor = get_file_monitor()
        _hot_reload_sync = HotReloadSynchronizer(_file_monitor)
    return _hot_reload_sync