"""
Trace Manager for CursorFlow v2.0

Manages Playwright trace file recording for complete interaction history.
Pure observation - records everything without modifying application behavior.
"""

import asyncio
import time
import logging
from typing import Optional, Dict, Any
from pathlib import Path
from playwright.async_api import BrowserContext


class TraceManager:
    """
    Manages Playwright trace recording for comprehensive debugging data
    
    Provides complete interaction history, screenshots, and network activity
    in Playwright's native trace format for maximum debugging capability.
    """
    
    def __init__(self, artifacts_base: Path):
        """
        Initialize trace manager
        
        Args:
            artifacts_base: Base directory for storing trace files
        """
        self.artifacts_base = artifacts_base
        self.traces_dir = artifacts_base / "traces"
        self.traces_dir.mkdir(parents=True, exist_ok=True)
        
        self.current_trace_path: Optional[Path] = None
        self.is_recording = False
        self.session_id: Optional[str] = None
        
        self.logger = logging.getLogger(__name__)
    
    async def start_trace(self, context: BrowserContext, session_id: str) -> str:
        """
        Start Playwright trace recording
        
        Args:
            context: Browser context to record
            session_id: Unique session identifier
            
        Returns:
            Path where trace will be saved
        """
        try:
            self.session_id = session_id
            self.current_trace_path = self.traces_dir / f"{session_id}.zip"
            
            # Start comprehensive trace recording
            await context.tracing.start(
                screenshots=True,      # Capture screenshots at each action
                snapshots=True,        # Capture DOM snapshots
                sources=True,          # Include source code context
                title=f"CursorFlow Session {session_id}"
            )
            
            self.is_recording = True
            self.logger.info(f"Started trace recording: {self.current_trace_path}")
            
            return str(self.current_trace_path)
            
        except Exception as e:
            self.logger.error(f"Failed to start trace recording: {e}")
            self.is_recording = False
            raise
    
    async def stop_trace(self, context: BrowserContext) -> Optional[str]:
        """
        Stop trace recording and save file
        
        Args:
            context: Browser context being recorded
            
        Returns:
            Path to saved trace file, or None if recording wasn't active
        """
        if not self.is_recording or not self.current_trace_path:
            return None
        
        try:
            await context.tracing.stop(path=str(self.current_trace_path))
            
            trace_path = str(self.current_trace_path)
            file_size = self.current_trace_path.stat().st_size if self.current_trace_path.exists() else 0
            
            self.logger.info(f"Trace recording saved: {trace_path} ({file_size:,} bytes)")
            
            # Reset state
            self.is_recording = False
            self.current_trace_path = None
            self.session_id = None
            
            return trace_path
            
        except Exception as e:
            self.logger.error(f"Failed to stop trace recording: {e}")
            self.is_recording = False
            return None
    
    async def stop_trace_on_error(self, context: BrowserContext, error: Exception) -> Optional[str]:
        """
        Stop trace recording when an error occurs, with error context
        
        Args:
            context: Browser context being recorded
            error: The error that occurred
            
        Returns:
            Path to saved trace file with error context
        """
        if not self.is_recording or not self.current_trace_path:
            return None
        
        try:
            # Add error context to trace filename
            error_trace_path = self.traces_dir / f"{self.session_id}_ERROR_{type(error).__name__}.zip"
            
            await context.tracing.stop(path=str(error_trace_path))
            
            file_size = error_trace_path.stat().st_size if error_trace_path.exists() else 0
            
            self.logger.info(f"Error trace saved: {error_trace_path} ({file_size:,} bytes)")
            self.logger.info(f"View trace: playwright show-trace {error_trace_path}")
            
            # Reset state
            self.is_recording = False
            self.current_trace_path = None
            self.session_id = None
            
            return str(error_trace_path)
            
        except Exception as trace_error:
            self.logger.error(f"Failed to save error trace: {trace_error}")
            self.is_recording = False
            return None
    
    def get_trace_info(self) -> Dict[str, Any]:
        """
        Get current trace recording information
        
        Returns:
            Dictionary with trace status and metadata
        """
        return {
            "is_recording": self.is_recording,
            "session_id": self.session_id,
            "trace_path": str(self.current_trace_path) if self.current_trace_path else None,
            "traces_directory": str(self.traces_dir),
            "total_traces": len(list(self.traces_dir.glob("*.zip")))
        }
    
    def cleanup_old_traces(self, max_traces: int = 50) -> int:
        """
        Clean up old trace files to prevent disk space issues
        
        Args:
            max_traces: Maximum number of trace files to keep
            
        Returns:
            Number of traces deleted
        """
        try:
            trace_files = sorted(
                self.traces_dir.glob("*.zip"),
                key=lambda p: p.stat().st_mtime,
                reverse=True  # Newest first
            )
            
            if len(trace_files) <= max_traces:
                return 0
            
            # Delete oldest traces
            traces_to_delete = trace_files[max_traces:]
            deleted_count = 0
            
            for trace_file in traces_to_delete:
                try:
                    trace_file.unlink()
                    deleted_count += 1
                except Exception as e:
                    self.logger.warning(f"Failed to delete old trace {trace_file}: {e}")
            
            if deleted_count > 0:
                self.logger.info(f"Cleaned up {deleted_count} old trace files")
            
            return deleted_count
            
        except Exception as e:
            self.logger.error(f"Trace cleanup failed: {e}")
            return 0
    
    def get_viewing_instructions(self, trace_path: str) -> str:
        """
        Get instructions for viewing a trace file
        
        Args:
            trace_path: Path to the trace file
            
        Returns:
            Command to view the trace
        """
        return f"playwright show-trace {trace_path}"
