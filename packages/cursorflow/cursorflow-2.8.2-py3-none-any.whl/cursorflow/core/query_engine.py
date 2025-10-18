"""
Query Engine - Fast Data Extraction from Test Results

Provides rapid filtering and extraction of test data without
manual JSON parsing. Pure data retrieval without analysis.
"""

import json
from pathlib import Path
from typing import Dict, Any, List, Optional
import csv
from io import StringIO


class QueryEngine:
    """
    Query interface for CursorFlow test results.
    
    Supports:
    - Filtering by data type (errors, network, console, performance)
    - Status code filtering for network requests
    - Export in multiple formats (json, markdown, csv)
    - Session comparison
    """
    
    def __init__(self, artifacts_dir: str = ".cursorflow/artifacts"):
        self.artifacts_dir = Path(artifacts_dir)
    
    def query_session(
        self,
        session_id: str,
        query_type: Optional[str] = None,
        filters: Optional[Dict] = None,
        export_format: str = "json"
    ) -> Any:
        """
        Query session data with optional filtering.
        
        Args:
            session_id: Session identifier
            query_type: Type of data to query (errors, network, console, performance, summary)
            filters: Additional filtering criteria
            export_format: Output format (json, markdown, csv)
            
        Returns:
            Filtered data in requested format
        """
        session_dir = self.artifacts_dir / "sessions" / session_id
        
        if not session_dir.exists():
            raise ValueError(f"Session not found: {session_id}")
        
        # Phase 3: Contextual queries
        if filters and 'context_for_error' in filters:
            return self._get_error_context(session_dir, filters, export_format)
        
        if filters and 'group_by_url' in filters:
            return self._group_by_url(session_dir, filters, export_format)
        
        if filters and 'group_by_selector' in filters:
            return self._group_by_selector(session_dir, filters, export_format)
        
        # Load requested data
        if query_type == "errors":
            data = self._query_errors(session_dir, filters)
        elif query_type == "network":
            data = self._query_network(session_dir, filters)
        elif query_type == "console":
            data = self._query_console(session_dir, filters)
        elif query_type == "performance":
            data = self._query_performance(session_dir, filters)
        elif query_type == "summary":
            data = self._query_summary(session_dir)
        elif query_type == "dom":
            data = self._query_dom(session_dir, filters)
        elif query_type == "server_logs":
            data = self._query_server_logs(session_dir, filters)
        elif query_type == "screenshots":
            data = self._query_screenshots(session_dir, filters)
        elif query_type == "mockup":
            data = self._query_mockup(session_dir, filters)
        elif query_type == "responsive":
            data = self._query_responsive(session_dir, filters)
        elif query_type == "css_iterations":
            data = self._query_css_iterations(session_dir, filters)
        elif query_type == "timeline":
            data = self._query_timeline(session_dir, filters)
        else:
            # Return all data references
            data = self._query_all(session_dir)
        
        # Export in requested format
        return self._export_data(data, export_format, query_type or "all")
    
    def compare_sessions(
        self,
        session_id_a: str,
        session_id_b: str,
        query_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Compare two sessions and identify differences.
        
        Args:
            session_id_a: First session ID
            session_id_b: Second session ID
            query_type: Optional specific data type to compare
            
        Returns:
            Comparison results showing differences
        """
        session_a = self.artifacts_dir / "sessions" / session_id_a
        session_b = self.artifacts_dir / "sessions" / session_id_b
        
        if not session_a.exists():
            raise ValueError(f"Session not found: {session_id_a}")
        if not session_b.exists():
            raise ValueError(f"Session not found: {session_id_b}")
        
        # Compare summaries
        summary_a = self._load_json(session_a / "summary.json")
        summary_b = self._load_json(session_b / "summary.json")
        
        comparison = {
            "session_a": session_id_a,
            "session_b": session_id_b,
            "summary_diff": self._compare_summaries(summary_a, summary_b)
        }
        
        # Compare specific data types if requested
        if query_type == "errors":
            errors_a = self._load_json(session_a / "errors.json")
            errors_b = self._load_json(session_b / "errors.json")
            comparison["errors_diff"] = self._compare_errors(errors_a, errors_b)
        
        elif query_type == "network":
            network_a = self._load_json(session_a / "network.json")
            network_b = self._load_json(session_b / "network.json")
            comparison["network_diff"] = self._compare_network(network_a, network_b)
        
        elif query_type == "performance":
            perf_a = self._load_json(session_a / "performance.json")
            perf_b = self._load_json(session_b / "performance.json")
            comparison["performance_diff"] = self._compare_performance(perf_a, perf_b)
        
        return comparison
    
    def list_sessions(self, limit: int = 10) -> List[Dict]:
        """List recent sessions with basic info"""
        sessions_dir = self.artifacts_dir / "sessions"
        
        if not sessions_dir.exists():
            return []
        
        sessions = []
        for session_dir in sorted(sessions_dir.iterdir(), key=lambda x: x.stat().st_mtime, reverse=True)[:limit]:
            if session_dir.is_dir():
                summary = self._load_json(session_dir / "summary.json")
                sessions.append({
                    "session_id": session_dir.name,
                    "timestamp": summary.get('timestamp', 'unknown'),
                    "success": summary.get('success', False),
                    "errors": summary.get('metrics', {}).get('total_errors', 0),
                    "network_failures": summary.get('metrics', {}).get('failed_network_requests', 0)
                })
        
        return sessions
    
    def _query_errors(self, session_dir: Path, filters: Optional[Dict]) -> Dict:
        """Query error data with optional filtering"""
        errors = self._load_json(session_dir / "errors.json")
        
        if not filters:
            return errors
        
        all_errors = errors.get('all_errors', [])
        filtered_errors = all_errors
        
        # Filter by error type
        if 'error_type' in filters:
            error_type = filters['error_type']
            filtered_errors = [
                err for err in filtered_errors
                if self._categorize_error_type(err.get('message', '')) == error_type
            ]
        
        # Filter by severity (critical = has errors)
        if 'severity' in filters:
            severity = filters['severity']
            if severity == 'critical':
                filtered_errors = all_errors
        
        # Phase 1: Enhanced filtering
        
        # Filter by source file/pattern
        if 'from_file' in filters:
            file_pattern = filters['from_file']
            filtered_errors = [
                err for err in filtered_errors
                if file_pattern in err.get('source', '')
            ]
        
        if 'from_pattern' in filters:
            import fnmatch
            pattern = filters['from_pattern']
            filtered_errors = [
                err for err in filtered_errors
                if fnmatch.fnmatch(err.get('source', ''), pattern)
            ]
        
        # Filter by message content
        if 'contains' in filters:
            search_term = filters['contains']
            filtered_errors = [
                err for err in filtered_errors
                if search_term.lower() in err.get('message', '').lower()
            ]
        
        if 'matches' in filters:
            import re
            regex = filters['matches']
            filtered_errors = [
                err for err in filtered_errors
                if re.search(regex, err.get('message', ''), re.IGNORECASE)
            ]
        
        # Filter by timestamp range
        if 'after' in filters:
            after_time = float(filters['after'])
            filtered_errors = [
                err for err in filtered_errors
                if err.get('timestamp', 0) >= after_time
            ]
        
        if 'before' in filters:
            before_time = float(filters['before'])
            filtered_errors = [
                err for err in filtered_errors
                if err.get('timestamp', 0) <= before_time
            ]
        
        if 'between' in filters:
            times = filters['between'].split(',')
            start_time = float(times[0].strip())
            end_time = float(times[1].strip())
            filtered_errors = [
                err for err in filtered_errors
                if start_time <= err.get('timestamp', 0) <= end_time
            ]
        
        # Phase 2: Cross-referencing
        if 'with_network' in filters and filters['with_network']:
            filtered_errors = self._add_related_network(session_dir, filtered_errors)
        
        if 'with_console' in filters and filters['with_console']:
            filtered_errors = self._add_related_console(session_dir, filtered_errors)
        
        if 'with_server_logs' in filters and filters['with_server_logs']:
            filtered_errors = self._add_related_server_logs(session_dir, filtered_errors)
        
        return {
            'total_errors': len(filtered_errors),
            'errors': filtered_errors
        }
    
    def _categorize_error_type(self, error_message: str) -> str:
        """Categorize error by type"""
        error_message_lower = error_message.lower()
        
        if 'syntaxerror' in error_message_lower or 'unexpected' in error_message_lower:
            return 'syntax_error'
        elif 'referenceerror' in error_message_lower or 'not defined' in error_message_lower:
            return 'reference_error'
        elif 'typeerror' in error_message_lower:
            return 'type_error'
        elif 'networkerror' in error_message_lower or 'failed to fetch' in error_message_lower:
            return 'network_error'
        elif 'load' in error_message_lower:
            return 'load_error'
        else:
            return 'other_error'
    
    def _query_network(self, session_dir: Path, filters: Optional[Dict]) -> Dict:
        """Query network data with optional filtering"""
        network = self._load_json(session_dir / "network.json")
        
        if not filters:
            return network
        
        all_requests = network.get('all_requests', [])
        filtered_requests = all_requests
        
        # Filter by status code
        if 'status' in filters:
            status_filter = filters['status']
            
            # Support ranges like "4xx", "5xx"
            if status_filter.endswith('xx'):
                prefix = int(status_filter[0])
                filtered_requests = [
                    req for req in filtered_requests 
                    if str(req.get('status_code', 0)).startswith(str(prefix))
                ]
            # Support specific codes like "404,500"
            elif ',' in status_filter:
                codes = [int(c.strip()) for c in status_filter.split(',')]
                filtered_requests = [
                    req for req in filtered_requests 
                    if req.get('status_code', 0) in codes
                ]
            else:
                code = int(status_filter)
                filtered_requests = [
                    req for req in filtered_requests 
                    if req.get('status_code', 0) == code
                ]
        
        # Filter failed requests only
        if 'failed' in filters and filters['failed']:
            # Use failed_requests array directly (already filtered)
            filtered_requests = network.get('failed_requests', [])
        
        # Phase 1: Enhanced network filtering
        
        # Filter by URL patterns
        if 'url_contains' in filters:
            pattern = filters['url_contains']
            filtered_requests = [
                req for req in filtered_requests
                if pattern in req.get('url', '')
            ]
        
        if 'url_matches' in filters:
            import re
            regex = filters['url_matches']
            filtered_requests = [
                req for req in filtered_requests
                if re.search(regex, req.get('url', ''), re.IGNORECASE)
            ]
        
        # Filter by timing thresholds
        if 'over' in filters:
            # Parse timing (could be "500ms" or just "500")
            threshold_str = str(filters['over']).replace('ms', '')
            threshold = float(threshold_str)
            filtered_requests = [
                req for req in filtered_requests
                if req.get('timing', {}).get('duration', 0) > threshold
            ]
        
        if 'between_timing' in filters:
            times = filters['between_timing'].replace('ms', '').split(',')
            min_time = float(times[0].strip())
            max_time = float(times[1].strip())
            filtered_requests = [
                req for req in filtered_requests
                if min_time <= req.get('timing', {}).get('duration', 0) <= max_time
            ]
        
        # Filter by HTTP method
        if 'method' in filters:
            methods = [m.strip().upper() for m in filters['method'].split(',')]
            filtered_requests = [
                req for req in filtered_requests
                if req.get('method', 'GET').upper() in methods
            ]
        
        # Phase 2: Cross-referencing
        if 'with_errors' in filters and filters['with_errors']:
            filtered_requests = self._add_related_errors_to_network(session_dir, filtered_requests)
        
        if 'with_console' in filters and filters['with_console']:
            filtered_requests = self._add_related_console_to_network(session_dir, filtered_requests)
        
        return {
            'total_requests': len(filtered_requests),
            'requests': filtered_requests
        }
    
    def _query_console(self, session_dir: Path, filters: Optional[Dict]) -> Dict:
        """Query console messages with optional filtering"""
        console = self._load_json(session_dir / "console.json")
        
        if not filters:
            return console
        
        # Filter by message type
        if 'type' in filters:
            msg_types = filters['type'].split(',')
            messages_by_type = console.get('messages_by_type', {})
            
            filtered_messages = []
            for msg_type in msg_types:
                filtered_messages.extend(messages_by_type.get(msg_type.strip(), []))
            
            return {
                'total_messages': len(filtered_messages),
                'messages': filtered_messages
            }
        
        return console
    
    def _query_performance(self, session_dir: Path, filters: Optional[Dict]) -> Dict:
        """Query performance data"""
        return self._load_json(session_dir / "performance.json")
    
    def _query_summary(self, session_dir: Path) -> Dict:
        """Query summary data"""
        return self._load_json(session_dir / "summary.json")
    
    def _query_dom(self, session_dir: Path, filters: Optional[Dict]) -> Dict:
        """Query DOM analysis data"""
        dom = self._load_json(session_dir / "dom_analysis.json")
        
        if not filters:
            return dom
        
        elements = dom.get('elements', [])
        filtered_elements = elements
        
        # Phase 1: Enhanced DOM filtering
        
        # Filter by selector (improved matching with correct field paths and priority)
        if 'selector' in filters or 'select' in filters:
            selector = filters.get('selector') or filters.get('select')
            
            # Detect selector type
            is_id_selector = selector.startswith('#')
            is_class_selector = selector.startswith('.')
            
            # Remove leading dot or hash if present (e.g., ".class" -> "class", "#id" -> "id")
            selector_clean = selector.lstrip('.#')
            
            # Determine if this looks like a simple tag name (no special characters)
            is_simple_tag = selector.isalpha() and not is_id_selector and not is_class_selector
            
            result_elements = []
            for el in filtered_elements:
                matched = False
                
                # Priority 1: ID selector (#id) - only check ID field
                if is_id_selector:
                    if selector_clean == el.get('id', ''):
                        result_elements.append(el)
                    continue
                
                # Priority 2: Class selector (.class) - only check className
                if is_class_selector:
                    if el.get('className'):
                        class_names = str(el.get('className')).split()
                        if selector_clean in class_names:
                            result_elements.append(el)
                    # Backward compatibility: Check classes array (old format)
                    elif selector_clean in el.get('classes', []):
                        result_elements.append(el)
                    continue
                
                # Priority 3: For simple alphanumeric selectors, check tagName, ID, and className
                # This handles ambiguous cases like "page" (could be tag or ID)
                if is_simple_tag:
                    # Check tag name match (exact, case insensitive)
                    if selector.lower() == el.get('tagName', '').lower():
                        result_elements.append(el)
                        continue
                    
                    # Check ID match (exact)
                    if selector_clean == el.get('id', ''):
                        result_elements.append(el)
                        continue
                    
                    # Class name match (whole word match to avoid "a" matching "navbar")
                    if el.get('className'):
                        class_names = str(el.get('className')).split()
                        if selector_clean in class_names:
                            result_elements.append(el)
                            continue
                    
                    # Backward compatibility: Check classes array (old format)
                    if selector_clean in el.get('classes', []):
                        result_elements.append(el)
                    
                    # Don't fall through to selector string checks for simple tags
                    continue
                
                # Priority 2: For complex selectors, check selector strings and attributes
                if (
                    # Check selectors.unique_css (current format)
                    (selector in el.get('selectors', {}).get('unique_css', '')) or
                    # Check selectors.css (current format)  
                    (selector in el.get('selectors', {}).get('css', '')) or
                    # Check selectors.xpath
                    (selector in el.get('selectors', {}).get('xpath', '')) or
                    # Check ID (exact match or contains for partial IDs)
                    (el.get('id') and selector_clean in str(el.get('id'))) or
                    # Check className (can be string or None)
                    (el.get('className') and selector_clean in str(el.get('className'))) or
                    # Backward compatibility: Check nested uniqueSelector (old format)
                    (selector in el.get('selectors', {}).get('uniqueSelector', '')) or
                    # Backward compatibility: Check top-level uniqueSelector (old format)
                    (selector in el.get('uniqueSelector', '')) or
                    # Backward compatibility: Check classes array (old format)
                    (selector_clean in el.get('classes', []))
                ):
                    result_elements.append(el)
            
            filtered_elements = result_elements
        
        # Filter by attributes
        if 'with_attr' in filters:
            attr_name = filters['with_attr']
            filtered_elements = [
                el for el in filtered_elements
                if attr_name in el.get('attributes', {})
            ]
        
        # Filter by ARIA role
        if 'role' in filters:
            role = filters['role']
            filtered_elements = [
                el for el in filtered_elements
                if el.get('accessibility', {}).get('role') == role
            ]
        
        # Filter by visibility (use correct nested path)
        if 'visible' in filters and filters['visible']:
            filtered_elements = [
                el for el in filtered_elements
                if el.get('visual_context', {}).get('visibility', {}).get('is_visible', False)
            ]
        
        # Filter by interactivity (use correct nested path)
        if 'interactive' in filters and filters['interactive']:
            filtered_elements = [
                el for el in filtered_elements
                if el.get('accessibility', {}).get('is_interactive', False)
            ]
        
        # Filter elements with errors (from console errors)
        if 'has_errors' in filters and filters['has_errors']:
            # This would need error context - skip for now or add cross-ref
            pass
        
        return {
            'total_elements': len(filtered_elements),
            'elements': filtered_elements
        }
    
    def _query_server_logs(self, session_dir: Path, filters: Optional[Dict]) -> Dict:
        """Query server logs with filtering"""
        server_logs = self._load_json(session_dir / "server_logs.json")
        
        if not filters:
            return server_logs
        
        all_logs = server_logs.get('all_logs', [])
        filtered_logs = all_logs
        
        # Filter by severity
        if 'severity' in filters or 'level' in filters:
            severity = filters.get('severity') or filters.get('level')
            severities = [s.strip() for s in severity.split(',')]
            filtered_logs = [
                log for log in filtered_logs
                if log.get('severity', 'info').lower() in [s.lower() for s in severities]
            ]
        
        # Filter by source (ssh, local, docker, systemd)
        if 'source' in filters:
            source = filters['source']
            filtered_logs = [
                log for log in filtered_logs
                if log.get('source', '').lower() == source.lower()
            ]
        
        # Filter by file path
        if 'file' in filters:
            file_filter = filters['file']
            filtered_logs = [
                log for log in filtered_logs
                if file_filter in log.get('file', '')
            ]
        
        # Filter by pattern (content search)
        if 'pattern' in filters or 'contains' in filters:
            pattern = filters.get('pattern') or filters.get('contains')
            filtered_logs = [
                log for log in filtered_logs
                if pattern.lower() in log.get('content', '').lower()
            ]
        
        # Filter by regex match
        if 'matches' in filters:
            import re
            regex = filters['matches']
            filtered_logs = [
                log for log in filtered_logs
                if re.search(regex, log.get('content', ''), re.IGNORECASE)
            ]
        
        # Filter by timestamp
        if 'after' in filters:
            after_time = float(filters['after'])
            filtered_logs = [
                log for log in filtered_logs
                if log.get('timestamp', 0) >= after_time
            ]
        
        if 'before' in filters:
            before_time = float(filters['before'])
            filtered_logs = [
                log for log in filtered_logs
                if log.get('timestamp', 0) <= before_time
            ]
        
        if 'between' in filters:
            times = filters['between'].split(',')
            start_time = float(times[0].strip())
            end_time = float(times[1].strip())
            filtered_logs = [
                log for log in filtered_logs
                if start_time <= log.get('timestamp', 0) <= end_time
            ]
        
        return {
            'total_logs': len(filtered_logs),
            'logs': filtered_logs
        }
    
    def _query_screenshots(self, session_dir: Path, filters: Optional[Dict]) -> Dict:
        """Query screenshot metadata"""
        screenshots = self._load_json(session_dir / "screenshots.json")
        
        if not filters:
            return screenshots
        
        screenshot_list = screenshots.get('screenshots', [])
        filtered_screenshots = screenshot_list
        
        # Filter by errors
        if 'with_errors' in filters and filters['with_errors']:
            filtered_screenshots = [s for s in filtered_screenshots if s.get('has_errors')]
        
        # Filter by network failures
        if 'with_network_failures' in filters and filters['with_network_failures']:
            filtered_screenshots = [s for s in filtered_screenshots if s.get('has_network_failures')]
        
        # Filter by timestamp
        if 'at_timestamp' in filters:
            timestamp = float(filters['at_timestamp'])
            # Find screenshot closest to timestamp
            filtered_screenshots = sorted(
                filtered_screenshots,
                key=lambda s: abs(s.get('timestamp', 0) - timestamp)
            )[:1]
        
        # Get specific screenshot by index
        if 'index' in filters:
            index = int(filters['index'])
            if 0 <= index < len(screenshot_list):
                filtered_screenshots = [screenshot_list[index]]
            else:
                filtered_screenshots = []
        
        return {
            'total_screenshots': len(filtered_screenshots),
            'screenshots': filtered_screenshots
        }
    
    def _query_mockup(self, session_dir: Path, filters: Optional[Dict]) -> Dict:
        """Query mockup comparison data"""
        mockup = self._load_json(session_dir / "mockup_comparison.json")
        
        if not filters:
            return mockup
        
        # Filter by similarity threshold
        if 'similarity_under' in filters:
            threshold = float(filters['similarity_under'])
            if mockup.get('similarity_score', 100) >= threshold:
                return {}
        
        if 'similarity_over' in filters:
            threshold = float(filters['similarity_over'])
            if mockup.get('similarity_score', 0) <= threshold:
                return {}
        
        # Show differences only
        if 'differences' in filters and filters['differences']:
            return {
                'similarity_score': mockup.get('similarity_score', 0),
                'differences': mockup.get('differences', [])
            }
        
        # Get specific iteration
        if 'iteration' in filters:
            iteration_idx = int(filters['iteration'])
            iterations = mockup.get('iterations', [])
            if 0 <= iteration_idx < len(iterations):
                return {
                    'iteration': iterations[iteration_idx],
                    'index': iteration_idx
                }
        
        return mockup
    
    def _query_responsive(self, session_dir: Path, filters: Optional[Dict]) -> Dict:
        """Query responsive testing results"""
        responsive = self._load_json(session_dir / "responsive_results.json")
        
        if not filters:
            return responsive
        
        # Get specific viewport
        if 'viewport' in filters:
            viewport_name = filters['viewport']
            viewports = responsive.get('viewports', {})
            if viewport_name in viewports:
                return {
                    'viewport': viewport_name,
                    'data': viewports[viewport_name]
                }
        
        # Show differences only
        if 'show_differences' in filters and filters['show_differences']:
            return {
                'comparison': responsive.get('comparison', {})
            }
        
        return responsive
    
    def _query_css_iterations(self, session_dir: Path, filters: Optional[Dict]) -> Dict:
        """Query CSS iteration results"""
        css_iterations = self._load_json(session_dir / "css_iterations.json")
        
        if not filters:
            return css_iterations
        
        iterations = css_iterations.get('iterations', [])
        
        # Get specific iteration
        if 'iteration' in filters:
            iteration_idx = int(filters['iteration']) - 1  # User provides 1-based
            if 0 <= iteration_idx < len(iterations):
                return {
                    'iteration': iterations[iteration_idx],
                    'index': iteration_idx + 1
                }
        
        # Filter iterations with errors
        if 'with_errors' in filters and filters['with_errors']:
            filtered = [
                it for it in iterations
                if it.get('console_errors') or it.get('has_errors')
            ]
            return {
                'total_iterations': len(filtered),
                'iterations': filtered
            }
        
        # Compare specific iterations
        if 'compare_iterations' in filters:
            indices = [int(i.strip()) - 1 for i in filters['compare_iterations'].split(',')]
            selected = [iterations[i] for i in indices if 0 <= i < len(iterations)]
            return {
                'compared_iterations': selected,
                'indices': [i + 1 for i in indices]
            }
        
        return css_iterations
    
    def _query_timeline(self, session_dir: Path, filters: Optional[Dict]) -> Dict:
        """Query timeline data with filtering"""
        timeline = self._load_json(session_dir / "timeline.json")
        
        if not filters:
            return timeline
        
        organized_timeline = timeline.get('organized_timeline', [])
        filtered_events = organized_timeline
        
        # Filter by event source
        if 'source' in filters:
            source = filters['source']
            filtered_events = [
                event for event in filtered_events
                if event.get('source') == source
            ]
        
        # Filter by timestamp window
        if 'around' in filters:
            timestamp = float(filters['around'])
            window = float(filters.get('window', 5))
            filtered_events = [
                event for event in filtered_events
                if abs(event.get('timestamp', 0) - timestamp) <= window
            ]
        
        # Filter events before timestamp
        if 'before' in filters:
            timestamp = float(filters['before'])
            filtered_events = [
                event for event in filtered_events
                if event.get('timestamp', 0) < timestamp
            ]
        
        # Filter events after timestamp
        if 'after' in filters:
            timestamp = float(filters['after'])
            filtered_events = [
                event for event in filtered_events
                if event.get('timestamp', 0) > timestamp
            ]
        
        return {
            'total_events': len(filtered_events),
            'events': filtered_events
        }
    
    def _query_all(self, session_dir: Path) -> Dict:
        """Get references to all data files"""
        return {
            "session_id": session_dir.name,
            "data_files": {
                "summary": str(session_dir / "summary.json"),
                "errors": str(session_dir / "errors.json"),
                "network": str(session_dir / "network.json"),
                "console": str(session_dir / "console.json"),
                "server_logs": str(session_dir / "server_logs.json"),
                "dom_analysis": str(session_dir / "dom_analysis.json"),
                "performance": str(session_dir / "performance.json"),
                "timeline": str(session_dir / "timeline.json"),
                "screenshots": str(session_dir / "screenshots.json")
            },
            "optional_files": {
                "mockup_comparison": str(session_dir / "mockup_comparison.json"),
                "responsive_results": str(session_dir / "responsive_results.json"),
                "css_iterations": str(session_dir / "css_iterations.json")
            },
            "artifact_dirs": {
                "screenshots": str(session_dir / "screenshots"),
                "traces": str(session_dir / "traces")
            },
            "data_digest": str(session_dir / "data_digest.md")
        }
    
    def _compare_summaries(self, summary_a: Dict, summary_b: Dict) -> Dict:
        """Compare summary metrics between sessions"""
        metrics_a = summary_a.get('metrics', {})
        metrics_b = summary_b.get('metrics', {})
        
        return {
            "errors": {
                "session_a": metrics_a.get('total_errors', 0),
                "session_b": metrics_b.get('total_errors', 0),
                "difference": metrics_b.get('total_errors', 0) - metrics_a.get('total_errors', 0)
            },
            "network_failures": {
                "session_a": metrics_a.get('failed_network_requests', 0),
                "session_b": metrics_b.get('failed_network_requests', 0),
                "difference": metrics_b.get('failed_network_requests', 0) - metrics_a.get('failed_network_requests', 0)
            },
            "execution_time": {
                "session_a": summary_a.get('execution_time', 0),
                "session_b": summary_b.get('execution_time', 0),
                "difference": summary_b.get('execution_time', 0) - summary_a.get('execution_time', 0)
            }
        }
    
    def _compare_errors(self, errors_a: Dict, errors_b: Dict) -> Dict:
        """Compare errors between sessions - Phase 4 message-level comparison"""
        all_errors_a = errors_a.get('all_errors', [])
        all_errors_b = errors_b.get('all_errors', [])
        
        # Get error messages for set operations
        messages_a = set(err.get('message', '') for err in all_errors_a)
        messages_b = set(err.get('message', '') for err in all_errors_b)
        
        # Set operations
        new_messages = messages_b - messages_a
        fixed_messages = messages_a - messages_b
        common_messages = messages_a & messages_b
        
        # Find actual error objects for new/fixed
        new_errors = [err for err in all_errors_b if err.get('message') in new_messages]
        fixed_errors = [err for err in all_errors_a if err.get('message') in fixed_messages]
        
        # Frequency changes for common errors
        frequency_changes = []
        for msg in common_messages:
            count_a = sum(1 for err in all_errors_a if err.get('message') == msg)
            count_b = sum(1 for err in all_errors_b if err.get('message') == msg)
            if count_a != count_b:
                frequency_changes.append({
                    "message": msg,
                    "count_a": count_a,
                    "count_b": count_b,
                    "change": count_b - count_a
                })
        
        return {
            "total_errors_a": len(all_errors_a),
            "total_errors_b": len(all_errors_b),
            "change": len(all_errors_b) - len(all_errors_a),
            "new_errors": {
                "count": len(new_errors),
                "errors": new_errors
            },
            "fixed_errors": {
                "count": len(fixed_errors),
                "errors": fixed_errors
            },
            "common_errors": {
                "count": len(common_messages),
                "messages": list(common_messages)
            },
            "frequency_changes": frequency_changes,
            "error_types_a": list(errors_a.get('errors_by_type', {}).keys()),
            "error_types_b": list(errors_b.get('errors_by_type', {}).keys())
        }
    
    def _compare_network(self, network_a: Dict, network_b: Dict) -> Dict:
        """Compare network requests between sessions - Phase 4 URL-level comparison"""
        all_requests_a = network_a.get('all_requests', [])
        all_requests_b = network_b.get('all_requests', [])
        
        # Get URLs for set operations
        urls_a = set(req.get('url', '') for req in all_requests_a)
        urls_b = set(req.get('url', '') for req in all_requests_b)
        
        # Set operations
        new_urls = urls_b - urls_a
        removed_urls = urls_a - urls_b
        common_urls = urls_a & urls_b
        
        # Find requests with status code changes
        status_changes = []
        for url in common_urls:
            reqs_a = [r for r in all_requests_a if r.get('url') == url]
            reqs_b = [r for r in all_requests_b if r.get('url') == url]
            
            if reqs_a and reqs_b:
                status_a = reqs_a[0].get('status_code', 0)
                status_b = reqs_b[0].get('status_code', 0)
                if status_a != status_b:
                    status_changes.append({
                        "url": url,
                        "status_a": status_a,
                        "status_b": status_b
                    })
        
        # Find requests with timing changes
        timing_changes = []
        for url in common_urls:
            reqs_a = [r for r in all_requests_a if r.get('url') == url]
            reqs_b = [r for r in all_requests_b if r.get('url') == url]
            
            if reqs_a and reqs_b:
                time_a = reqs_a[0].get('timing', {}).get('duration', 0)
                time_b = reqs_b[0].get('timing', {}).get('duration', 0)
                diff = abs(time_b - time_a)
                if diff > 100:  # Significant change threshold
                    timing_changes.append({
                        "url": url,
                        "timing_a": time_a,
                        "timing_b": time_b,
                        "difference": time_b - time_a
                    })
        
        return {
            "total_requests_a": len(all_requests_a),
            "total_requests_b": len(all_requests_b),
            "failed_requests_a": len(network_a.get('failed_requests', [])),
            "failed_requests_b": len(network_b.get('failed_requests', [])),
            "success_rate_a": network_a.get('summary', {}).get('success_rate', 100),
            "success_rate_b": network_b.get('summary', {}).get('success_rate', 100),
            "new_urls": {
                "count": len(new_urls),
                "urls": list(new_urls)
            },
            "removed_urls": {
                "count": len(removed_urls),
                "urls": list(removed_urls)
            },
            "status_changes": status_changes,
            "timing_changes": timing_changes
        }
    
    def _compare_performance(self, perf_a: Dict, perf_b: Dict) -> Dict:
        """Compare performance metrics between sessions"""
        summary_a = perf_a.get('summary', {})
        summary_b = perf_b.get('summary', {})
        
        return {
            "execution_time": {
                "session_a": perf_a.get('execution_time', 0),
                "session_b": perf_b.get('execution_time', 0),
                "difference": perf_b.get('execution_time', 0) - perf_a.get('execution_time', 0)
            },
            "avg_load_time": {
                "session_a": summary_a.get('average_page_load_time', 0),
                "session_b": summary_b.get('average_page_load_time', 0),
                "difference": summary_b.get('average_page_load_time', 0) - summary_a.get('average_page_load_time', 0)
            },
            "max_memory": {
                "session_a": summary_a.get('max_memory_usage', 0),
                "session_b": summary_b.get('max_memory_usage', 0),
                "difference": summary_b.get('max_memory_usage', 0) - summary_a.get('max_memory_usage', 0)
            }
        }
    
    def _export_data(self, data: Any, format: str, data_type: str) -> Any:
        """Export data in requested format"""
        if format == "json":
            return json.dumps(data, indent=2, default=str)
        
        elif format == "markdown":
            return self._to_markdown(data, data_type)
        
        elif format == "csv":
            return self._to_csv(data, data_type)
        
        elif format == "dict" or format == "raw":
            # Return raw dictionary (useful for programmatic access)
            return data
        
        else:
            return data
    
    def _to_markdown(self, data: Dict, data_type: str) -> str:
        """Convert data to markdown format - Phase 5 enhanced formatting"""
        md = f"# {data_type.replace('_', ' ').title()} Data\n\n"
        
        # Format based on data type and structure
        if data_type == "errors":
            # Check if has 'all_errors' key (from errors.json structure)
            if 'all_errors' in data:
                data = {'errors': data['all_errors']}
            md += self._format_errors_markdown(data)
        
        elif data_type == "network":
            # Check if has 'all_requests' key
            if 'all_requests' in data:
                data = {'requests': data['all_requests']}
            md += self._format_network_markdown(data)
        
        elif data_type == "server_logs":
            # Check if has 'all_logs' key
            if 'all_logs' in data:
                data = {'logs': data['all_logs']}
            md += self._format_server_logs_markdown(data)
        
        elif data_type == "error_context":
            md += self._format_error_context_markdown(data)
        
        else:
            # Fallback to JSON for unknown types
            md += "```json\n"
            md += json.dumps(data, indent=2, default=str)
            md += "\n```\n"
        
        return md
    
    def _format_errors_markdown(self, data: Dict) -> str:
        """Format errors as markdown tables"""
        errors = data.get('errors', [])
        md = f"**Total Errors:** {len(errors)}\n\n"
        
        if not errors:
            return md + "No errors found.\n"
        
        md += "| # | Error | Source | Line:Col | Message |\n"
        md += "|---|-------|--------|----------|----------|\n"
        
        for idx, err in enumerate(errors[:20], 1):  # Limit to 20
            message = err.get('message', 'Unknown')[:80]
            md += f"| {idx} | {err.get('type', 'Error')} | {err.get('source', 'Unknown')[:30]} | {err.get('line', '?')}:{err.get('column', '?')} | {message} |\n"
        
        if len(errors) > 20:
            md += f"\n*...and {len(errors) - 20} more errors*\n"
        
        # Show related data if present
        if errors and 'related_network_count' in errors[0]:
            md += f"\n**Note:** Errors include related network requests (±5s window)\n"
        
        return md + "\n"
    
    def _format_network_markdown(self, data: Dict) -> str:
        """Format network requests as markdown tables"""
        requests = data.get('requests', [])
        md = f"**Total Requests:** {len(requests)}\n\n"
        
        if not requests:
            return md + "No requests found.\n"
        
        md += "| # | Method | URL | Status | Timing |\n"
        md += "|---|--------|-----|--------|--------|\n"
        
        for idx, req in enumerate(requests[:20], 1):
            url = req.get('url', 'Unknown')[:60]
            timing = req.get('timing', {}).get('duration', 0)
            md += f"| {idx} | {req.get('method', 'GET')} | {url} | {req.get('status_code', '?')} | {timing}ms |\n"
        
        if len(requests) > 20:
            md += f"\n*...and {len(requests) - 20} more requests*\n"
        
        return md + "\n"
    
    def _format_server_logs_markdown(self, data: Dict) -> str:
        """Format server logs as markdown"""
        logs = data.get('logs', [])
        md = f"**Total Server Logs:** {len(logs)}\n\n"
        
        if not logs:
            return md + "No server logs found.\n"
        
        # Group by severity
        by_severity = {}
        for log in logs:
            sev = log.get('severity', 'info')
            if sev not in by_severity:
                by_severity[sev] = []
            by_severity[sev].append(log)
        
        for severity, severity_logs in by_severity.items():
            emoji = {
                'error': '🚨',
                'warning': '⚠️',
                'info': 'ℹ️',
                'debug': '🔍'
            }.get(severity.lower(), '📝')
            
            md += f"## {emoji} {severity.title()} ({len(severity_logs)})\n\n"
            
            for idx, log in enumerate(severity_logs[:10], 1):
                content = log.get('content', 'Unknown')[:150]
                md += f"**{idx}.** `{content}`\n"
                md += f"   - Source: {log.get('source', 'unknown')} | File: {log.get('file', 'unknown')}\n\n"
            
            if len(severity_logs) > 10:
                md += f"*...and {len(severity_logs) - 10} more {severity} logs*\n\n"
        
        return md
    
    def _format_error_context_markdown(self, data: Dict) -> str:
        """Format error context with related data"""
        error = data.get('error', {})
        
        md = f"## Error Context\n\n"
        md += f"**Error:** `{error.get('message', 'Unknown')}`\n"
        md += f"**Source:** {error.get('source', 'Unknown')} (Line {error.get('line', '?')})\n"
        md += f"**Time Window:** {data.get('time_window', '±5s')}\n\n"
        
        md += "### Related Network Requests\n\n"
        network = data.get('related_network', [])
        if network:
            for req in network[:5]:
                md += f"- {req.get('method', 'GET')} {req.get('url', 'Unknown')[:60]} → {req.get('status_code', '?')}\n"
        else:
            md += "*No related network requests*\n"
        
        md += "\n### Related Console Messages\n\n"
        console = data.get('related_console', [])
        if console:
            for msg in console[:5]:
                md += f"- [{msg.get('type', 'log')}] {msg.get('message', 'Unknown')[:80]}\n"
        else:
            md += "*No related console messages*\n"
        
        md += "\n### Related Server Logs\n\n"
        server_logs = data.get('related_server_logs', [])
        if server_logs:
            for log in server_logs[:5]:
                md += f"- [{log.get('severity', 'info')}] {log.get('content', 'Unknown')[:80]}\n"
        else:
            md += "*No related server logs*\n"
        
        return md + "\n"
    
    def _to_csv(self, data: Dict, data_type: str) -> str:
        """Convert data to CSV format"""
        output = StringIO()
        
        # Handle different data types
        if data_type == "errors" and 'errors' in data:
            writer = csv.DictWriter(output, fieldnames=['message', 'source', 'line', 'column', 'screenshot_name'])
            writer.writeheader()
            for error in data.get('errors', []):
                writer.writerow({
                    'message': error.get('message', ''),
                    'source': error.get('source', ''),
                    'line': error.get('line', 0),
                    'column': error.get('column', 0),
                    'screenshot_name': error.get('screenshot_name', '')
                })
        
        elif data_type == "network" and 'requests' in data:
            writer = csv.DictWriter(output, fieldnames=['url', 'method', 'status_code', 'screenshot_name'])
            writer.writeheader()
            for req in data.get('requests', []):
                writer.writerow({
                    'url': req.get('url', ''),
                    'method': req.get('method', ''),
                    'status_code': req.get('status_code', 0),
                    'screenshot_name': req.get('screenshot_name', '')
                })
        
        else:
            # Generic CSV for other types
            output.write("# Data export - see JSON format for complete details\n")
        
        return output.getvalue()
    
    def _add_related_network(self, session_dir: Path, errors: List[Dict], window: float = 5.0) -> List[Dict]:
        """Add related network requests to errors (time-based correlation)"""
        network = self._load_json(session_dir / "network.json")
        all_requests = network.get('all_requests', [])
        
        for error in errors:
            error_time = error.get('timestamp', 0)
            # Find network requests within time window
            related = [
                req for req in all_requests
                if abs(req.get('timestamp', 0) - error_time) <= window
            ]
            error['related_network'] = related
            error['related_network_count'] = len(related)
        
        return errors
    
    def _add_related_console(self, session_dir: Path, errors: List[Dict], window: float = 5.0) -> List[Dict]:
        """Add related console messages to errors (time-based correlation)"""
        console = self._load_json(session_dir / "console.json")
        all_messages = console.get('all_messages', [])
        
        for error in errors:
            error_time = error.get('timestamp', 0)
            # Find console messages within time window
            related = [
                msg for msg in all_messages
                if abs(msg.get('timestamp', 0) - error_time) <= window
                and msg.get('message') != error.get('message')  # Exclude self
            ]
            error['related_console'] = related
            error['related_console_count'] = len(related)
        
        return errors
    
    def _add_related_server_logs(self, session_dir: Path, errors: List[Dict], window: float = 5.0) -> List[Dict]:
        """Add related server logs to errors (time-based correlation)"""
        server_logs = self._load_json(session_dir / "server_logs.json")
        all_logs = server_logs.get('all_logs', [])
        
        for error in errors:
            error_time = error.get('timestamp', 0)
            # Find server logs within time window
            related = [
                log for log in all_logs
                if abs(log.get('timestamp', 0) - error_time) <= window
            ]
            error['related_server_logs'] = related
            error['related_server_logs_count'] = len(related)
        
        return errors
    
    def _add_related_errors_to_network(self, session_dir: Path, requests: List[Dict], window: float = 5.0) -> List[Dict]:
        """Add related errors to network requests (time-based correlation)"""
        errors = self._load_json(session_dir / "errors.json")
        all_errors = errors.get('all_errors', [])
        
        for req in requests:
            req_time = req.get('timestamp', 0)
            # Find errors within time window
            related = [
                err for err in all_errors
                if abs(err.get('timestamp', 0) - req_time) <= window
            ]
            req['related_errors'] = related
            req['related_errors_count'] = len(related)
        
        return requests
    
    def _add_related_console_to_network(self, session_dir: Path, requests: List[Dict], window: float = 5.0) -> List[Dict]:
        """Add related console messages to network requests (time-based correlation)"""
        console = self._load_json(session_dir / "console.json")
        all_messages = console.get('all_messages', [])
        
        for req in requests:
            req_time = req.get('timestamp', 0)
            # Find console messages within time window
            related = [
                msg for msg in all_messages
                if abs(msg.get('timestamp', 0) - req_time) <= window
            ]
            req['related_console'] = related
            req['related_console_count'] = len(related)
        
        return requests
    
    def _get_error_context(self, session_dir: Path, filters: Dict, export_format: str) -> Any:
        """Phase 3: Get full context around specific error"""
        error_index = int(filters['context_for_error'])
        window = float(filters.get('window', 5.0))
        
        # Load all data
        errors = self._load_json(session_dir / "errors.json")
        all_errors = errors.get('all_errors', [])
        
        if error_index >= len(all_errors):
            return self._export_data({"error": "Error index out of range"}, export_format, "error")
        
        target_error = all_errors[error_index]
        error_time = target_error.get('timestamp', 0)
        
        # Gather all data within time window
        network = self._load_json(session_dir / "network.json")
        console = self._load_json(session_dir / "console.json")
        server_logs = self._load_json(session_dir / "server_logs.json")
        timeline = self._load_json(session_dir / "timeline.json")
        
        context = {
            "error": target_error,
            "error_index": error_index,
            "time_window": f"±{window}s",
            "related_network": [
                req for req in network.get('all_requests', [])
                if abs(req.get('timestamp', 0) - error_time) <= window
            ],
            "related_console": [
                msg for msg in console.get('all_messages', [])
                if abs(msg.get('timestamp', 0) - error_time) <= window
                and msg.get('message') != target_error.get('message')
            ],
            "related_server_logs": [
                log for log in server_logs.get('all_logs', [])
                if abs(log.get('timestamp', 0) - error_time) <= window
            ],
            "timeline_events": [
                event for event in timeline.get('organized_timeline', [])
                if abs(event.get('timestamp', 0) - error_time) <= window
            ]
        }
        
        return self._export_data(context, export_format, "error_context")
    
    def _group_by_url(self, session_dir: Path, filters: Dict, export_format: str) -> Any:
        """Phase 3: Group all data by URL pattern"""
        url_pattern = filters['group_by_url']
        
        # Load all data
        network = self._load_json(session_dir / "network.json")
        errors = self._load_json(session_dir / "errors.json")
        console = self._load_json(session_dir / "console.json")
        server_logs = self._load_json(session_dir / "server_logs.json")
        
        # Filter by URL pattern
        matching_requests = [
            req for req in network.get('all_requests', [])
            if url_pattern in req.get('url', '')
        ]
        
        # Get timestamps for cross-referencing
        request_times = [req.get('timestamp', 0) for req in matching_requests]
        
        grouped = {
            "url_pattern": url_pattern,
            "matching_requests": matching_requests,
            "related_errors": [
                err for err in errors.get('all_errors', [])
                if any(abs(err.get('timestamp', 0) - t) <= 5.0 for t in request_times)
            ],
            "related_console": [
                msg for msg in console.get('all_messages', [])
                if any(abs(msg.get('timestamp', 0) - t) <= 5.0 for t in request_times)
            ],
            "related_server_logs": [
                log for log in server_logs.get('all_logs', [])
                if url_pattern in log.get('content', '')
            ]
        }
        
        return self._export_data(grouped, export_format, "grouped_by_url")
    
    def _group_by_selector(self, session_dir: Path, filters: Dict, export_format: str) -> Any:
        """Phase 3: Group all data by selector pattern"""
        selector = filters['group_by_selector']
        
        # Load all data
        dom = self._load_json(session_dir / "dom_analysis.json")
        errors = self._load_json(session_dir / "errors.json")
        timeline = self._load_json(session_dir / "timeline.json")
        
        # Find matching elements
        matching_elements = [
            el for el in dom.get('elements', [])
            if selector in el.get('uniqueSelector', '') or selector in el.get('tagName', '')
        ]
        
        # Find click/interaction events with this selector
        interaction_events = [
            event for event in timeline.get('organized_timeline', [])
            if event.get('source') == 'browser' and selector in str(event.get('data', {}))
        ]
        
        grouped = {
            "selector": selector,
            "matching_elements": matching_elements,
            "interaction_events": interaction_events,
            "related_errors": errors.get('all_errors', [])  # Could filter by proximity
        }
        
        return self._export_data(grouped, export_format, "grouped_by_selector")
    
    def _load_json(self, path: Path) -> Dict:
        """Load JSON file, return empty dict if not found"""
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}

