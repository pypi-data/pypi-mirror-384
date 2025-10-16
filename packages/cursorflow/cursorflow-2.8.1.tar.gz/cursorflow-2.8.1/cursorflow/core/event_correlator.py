"""
Universal Event Correlator

Simple data organizer that timestamps and structures browser events 
and server logs for Cursor's analysis. NO PROCESSING - just organization.
"""

import time
from typing import Dict, List, Optional, Any
import logging


class EventCorrelator:
    """
    Simple data organizer - NO ANALYSIS, just clean data for Cursor
    
    Organizes browser events and server logs in chronological timeline
    format for Cursor to analyze. Does NOT process or interpret data.
    """
    
    def __init__(self):
        """Initialize simple data organizer"""
        self.logger = logging.getLogger(__name__)
    
    async def correlate_events(
        self, 
        browser_timeline: List[Dict], 
        server_logs: List[Dict]
    ) -> Dict[str, Any]:
        """
        Organize browser events and server logs for Cursor's analysis
        
        Args:
            browser_timeline: List of browser events with timestamps
            server_logs: List of server log entries with timestamps
            
        Returns:
            Simple organized data structure for Cursor to analyze:
            {
                "timeline": [events sorted by timestamp],
                "browser_events": [structured browser events],
                "server_events": [structured server logs],
                "summary": {basic counts}
            }
        """
        try:
            # Just organize the data - NO ANALYSIS
            organized_data = {
                "timeline": self._create_chronological_timeline(browser_timeline, server_logs),
                "browser_events": self._structure_browser_events(browser_timeline),
                "server_events": self._structure_server_events(server_logs),
                "summary": self._create_basic_summary(browser_timeline, server_logs)
            }
            
            self.logger.info(f"Organized {len(browser_timeline)} browser events and {len(server_logs)} server logs")
            return organized_data
            
        except Exception as e:
            self.logger.error(f"Data organization failed: {e}")
            return {
                "timeline": [],
                "browser_events": [],
                "server_events": [],
                "summary": {"error": str(e)}
            }
    
    def _create_chronological_timeline(self, browser_events: List[Dict], server_logs: List[Dict]) -> List[Dict]:
        """Create chronological timeline of all events - NO ANALYSIS"""
        all_events = []
        
        # Add browser events to timeline
        for event in browser_events:
            all_events.append({
                "timestamp": event.get("timestamp", 0),
                "source": "browser",
                "event_type": event.get("event", "unknown"),
                "data": event.get("data", {}),
                "raw_event": event
            })
        
        # Add server logs to timeline
        for log in server_logs:
            all_events.append({
                "timestamp": log.get("timestamp", 0),
                "source": "server",
                "event_type": "log_entry",
                "level": log.get("level", "info"),
                "content": log.get("content", ""),
                "raw_log": log
            })
        
        # Sort chronologically - that's it, no analysis
        all_events.sort(key=lambda x: x.get("timestamp", 0))
        
        return all_events
    
    def _structure_browser_events(self, browser_timeline: List[Dict]) -> List[Dict]:
        """Structure browser events for easy Cursor analysis - NO PROCESSING"""
        structured = []
        
        for event in browser_timeline:
            structured_event = {
                "timestamp": event.get("timestamp", 0),
                "type": event.get("event", "unknown"),
                "data": event.get("data", {}),
                "duration": event.get("duration", 0),
                "raw": event
            }
            structured.append(structured_event)
        
        return structured
    
    def _structure_server_events(self, server_logs: List[Dict]) -> List[Dict]:
        """Structure server logs for easy Cursor analysis - NO PROCESSING"""
        structured = []
        
        for log in server_logs:
            structured_log = {
                "timestamp": log.get("timestamp", 0),
                "level": log.get("level", "info"),
                "content": log.get("content", ""),
                "source": log.get("source", "unknown"),
                "source_type": log.get("source_type", "local"),
                "error_type": log.get("error_type", None),  # From log collector classification
                "raw": log
            }
            structured.append(structured_log)
        
        return structured
    
    def _create_basic_summary(self, browser_events: List[Dict], server_logs: List[Dict]) -> Dict[str, Any]:
        """Create basic counts for Cursor - NO ANALYSIS"""
        
        # Basic counts only
        browser_counts = {}
        server_counts = {}
        
        # Count browser event types
        for event in browser_events:
            event_type = event.get("event", "unknown")
            browser_counts[event_type] = browser_counts.get(event_type, 0) + 1
        
        # Count server log levels
        for log in server_logs:
            level = log.get("level", "info")
            server_counts[level] = server_counts.get(level, 0) + 1
        
        # Time range
        all_timestamps = []
        all_timestamps.extend([e.get("timestamp", 0) for e in browser_events])
        all_timestamps.extend([l.get("timestamp", 0) for l in server_logs])
        
        time_range = {}
        if all_timestamps:
            all_timestamps.sort()
            time_range = {
                "start": all_timestamps[0],
                "end": all_timestamps[-1], 
                "duration": all_timestamps[-1] - all_timestamps[0]
            }
        
        return {
            "total_browser_events": len(browser_events),
            "total_server_logs": len(server_logs),
            "browser_event_types": browser_counts,
            "server_log_levels": server_counts,
            "time_range": time_range
        }
    
    def organize_timeline(self, browser_events: List[Dict], server_logs: List[Dict]) -> List[Dict]:
        """
        Organize browser events and server logs into chronological timeline
        
        This is the method called by CursorFlow.execute_and_collect()
        """
        return self._create_chronological_timeline(browser_events, server_logs)
    
    def get_summary(self, timeline: List[Dict]) -> Dict[str, Any]:
        """
        Get basic summary from organized timeline
        
        This is the method called by CursorFlow.execute_and_collect()
        """
        # Extract browser events and server logs from timeline
        browser_events = [event["raw_event"] for event in timeline if event.get("source") == "browser" and "raw_event" in event]
        server_logs = [event["raw_log"] for event in timeline if event.get("source") == "server" and "raw_log" in event]
        
        return self._create_basic_summary(browser_events, server_logs)
    
    def organize_for_time_window(self, timeline: List[Dict], start_time: float, end_time: float) -> List[Dict]:
        """Get events within specific time window - simple filtering"""
        return [
            event for event in timeline 
            if start_time <= event.get("timestamp", 0) <= end_time
        ]
    
    def get_events_by_source(self, timeline: List[Dict], source: str) -> List[Dict]:
        """Filter events by source - simple filtering"""
        return [
            event for event in timeline 
            if event.get("source") == source
        ]