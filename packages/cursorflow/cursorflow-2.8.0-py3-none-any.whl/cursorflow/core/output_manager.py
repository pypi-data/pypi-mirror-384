"""
Output Manager - Multi-File Result Organization

Transforms monolithic JSON results into organized multi-file structure
optimized for AI consumption. Pure data organization without analysis.
"""

import json
import shutil
from pathlib import Path
from typing import Dict, Any, Optional
import logging
from datetime import datetime


class OutputManager:
    """
    Manages structured output generation for CursorFlow test results.
    
    Splits comprehensive test data into organized files:
    - summary.json: Core metrics and counts
    - errors.json: Console errors with context
    - network.json: Network requests/responses
    - console.json: All console messages
    - dom_analysis.json: Complete DOM and element data
    - performance.json: Performance and timing metrics
    - data_digest.md: AI-optimized data presentation
    """
    
    def __init__(self, artifacts_base_dir: str = ".cursorflow/artifacts"):
        self.artifacts_base_dir = Path(artifacts_base_dir)
        self.logger = logging.getLogger(__name__)
    
    def save_structured_results(
        self, 
        results: Dict[str, Any],
        session_id: str,
        test_description: str = "test"
    ) -> Dict[str, str]:
        """
        Save test results in structured multi-file format.
        
        Args:
            results: Complete test results dictionary
            session_id: Unique session identifier
            test_description: Brief description of test
            
        Returns:
            Dictionary mapping file types to their paths
        """
        # Create session directory
        session_dir = self.artifacts_base_dir / "sessions" / session_id
        session_dir.mkdir(parents=True, exist_ok=True)
        
        file_paths = {}
        
        # 1. Summary - Core metrics and counts
        summary_data = self._extract_summary(results)
        summary_path = session_dir / "summary.json"
        self._write_json(summary_path, summary_data)
        file_paths['summary'] = str(summary_path)
        
        # 2. Errors - Console errors with context
        errors_data = self._extract_errors(results)
        errors_path = session_dir / "errors.json"
        self._write_json(errors_path, errors_data)
        file_paths['errors'] = str(errors_path)
        
        # 3. Network - Requests and responses
        network_data = self._extract_network(results)
        network_path = session_dir / "network.json"
        self._write_json(network_path, network_data)
        file_paths['network'] = str(network_path)
        
        # 4. Console - All console messages
        console_data = self._extract_console(results)
        console_path = session_dir / "console.json"
        self._write_json(console_path, console_data)
        file_paths['console'] = str(console_path)
        
        # 5. DOM Analysis - Complete DOM and element data
        dom_data = self._extract_dom_analysis(results)
        dom_path = session_dir / "dom_analysis.json"
        self._write_json(dom_path, dom_data)
        file_paths['dom_analysis'] = str(dom_path)
        
        # 6. Performance - Performance and timing metrics
        performance_data = self._extract_performance(results)
        performance_path = session_dir / "performance.json"
        self._write_json(performance_path, performance_data)
        file_paths['performance'] = str(performance_path)
        
        # 7. Timeline - Complete event timeline
        timeline_data = self._extract_timeline(results)
        timeline_path = session_dir / "timeline.json"
        self._write_json(timeline_path, timeline_data)
        file_paths['timeline'] = str(timeline_path)
        
        # 8. Server Logs - Dedicated server log file
        server_logs_data = self._extract_server_logs(results)
        server_logs_path = session_dir / "server_logs.json"
        self._write_json(server_logs_path, server_logs_data)
        file_paths['server_logs'] = str(server_logs_path)
        
        # 9. Screenshots - Screenshot metadata index
        screenshots_data = self._extract_screenshots_metadata(results)
        screenshots_meta_path = session_dir / "screenshots.json"
        self._write_json(screenshots_meta_path, screenshots_data)
        file_paths['screenshots_metadata'] = str(screenshots_meta_path)
        
        # 10. Mockup Comparison - If present
        if 'mockup_comparison' in results:
            mockup_data = self._extract_mockup_comparison(results)
            mockup_path = session_dir / "mockup_comparison.json"
            self._write_json(mockup_path, mockup_data)
            file_paths['mockup_comparison'] = str(mockup_path)
        
        # 11. Responsive Results - If present
        if 'responsive_results' in results:
            responsive_data = self._extract_responsive_results(results)
            responsive_path = session_dir / "responsive_results.json"
            self._write_json(responsive_path, responsive_data)
            file_paths['responsive_results'] = str(responsive_path)
        
        # 12. CSS Iterations - If present
        if 'css_iterations' in results or 'iterations' in results:
            css_data = self._extract_css_iterations(results)
            css_path = session_dir / "css_iterations.json"
            self._write_json(css_path, css_data)
            file_paths['css_iterations'] = str(css_path)
        
        # 13. Move screenshot files to session directory if they exist
        screenshots_dir = session_dir / "screenshots"
        screenshots_dir.mkdir(exist_ok=True)
        self._organize_screenshots(results, screenshots_dir)
        file_paths['screenshots'] = str(screenshots_dir)
        
        # 14. Move traces to session directory if they exist
        traces_dir = session_dir / "traces"
        traces_dir.mkdir(exist_ok=True)
        self._organize_traces(results, traces_dir)
        file_paths['traces'] = str(traces_dir)
        
        self.logger.info(f"Structured results saved to: {session_dir}")
        return file_paths
    
    def _extract_summary(self, results: Dict) -> Dict:
        """Extract high-level summary data"""
        # Load comprehensive data from disk if available
        comprehensive = self._load_comprehensive_data(results)
        artifacts = results.get('artifacts', {})
        
        # Count errors from comprehensive_data
        error_count = 0
        warning_count = 0
        if comprehensive:
            console_data = comprehensive.get('console_data', {})
            all_console_logs = console_data.get('all_console_logs', [])
            error_count = len([log for log in all_console_logs if log.get('type') == 'error'])
            warning_count = len([log for log in all_console_logs if log.get('type') == 'warning'])
        
        # Count network requests from comprehensive_data
        network_count = 0
        failed_network_count = 0
        if comprehensive:
            network_data = comprehensive.get('network_data', {})
            all_network_events = network_data.get('all_network_events', [])
            network_count = len(all_network_events)
            # Count failures (4xx, 5xx)
            failed_network_count = len([req for req in all_network_events if req.get('status', 0) >= 400])
        
        # Count DOM elements
        dom_element_count = 0
        if comprehensive:
            dom_analysis = comprehensive.get('dom_analysis', {})
            dom_element_count = len(dom_analysis.get('elements', []))
        
        return {
            "session_id": results.get('session_id', 'unknown'),
            "timestamp": datetime.now().isoformat(),
            "success": results.get('success', False),
            "execution_time": results.get('execution_time', 0),
            "test_description": results.get('test_description', 'test'),
            "metrics": {
                "total_errors": error_count,
                "total_warnings": warning_count,
                "total_network_requests": network_count,
                "failed_network_requests": failed_network_count,
                "total_dom_elements": dom_element_count,
                "total_screenshots": len(artifacts.get('screenshots', [])),
                "total_timeline_events": len(results.get('timeline', []))
            },
            "status": {
                "has_errors": error_count > 0,
                "has_network_failures": failed_network_count > 0,
                "has_warnings": warning_count > 0
            }
        }
    
    def _extract_errors(self, results: Dict) -> Dict:
        """Extract all error data with context"""
        errors = []
        
        # Load comprehensive data from disk if available
        comprehensive_data = self._load_comprehensive_data(results)
        
        if comprehensive_data:
            console_data = comprehensive_data.get('console_data', {})
            all_console_logs = console_data.get('all_console_logs', [])
            
            # Filter for errors
            for log in all_console_logs:
                if log.get('type') == 'error':
                    # Extract location info if present
                    location = log.get('location', {})
                    errors.append({
                        "message": log.get('text', ''),
                        "source": location.get('url', ''),
                        "line": location.get('lineNumber', 0),
                        "column": location.get('columnNumber', 0),
                        "stack_trace": log.get('stackTrace', {}).get('callFrames', []),
                        "timestamp": log.get('timestamp', 0),
                        "screenshot_name": 'comprehensive',
                        "url": location.get('url', '')
                    })
        else:
            # Fallback: Collect errors from screenshot artifacts (old structure)
            # Only if comprehensive_data not available
            artifacts = results.get('artifacts', {})
            for screenshot in artifacts.get('screenshots', []):
                if isinstance(screenshot, dict):
                    console_data = screenshot.get('console_data', {})
                    error_logs = console_data.get('errors', {}).get('logs', [])
                    
                    for error in error_logs:
                        errors.append({
                            "message": error.get('message', ''),
                            "source": error.get('source', ''),
                            "line": error.get('line', 0),
                            "column": error.get('column', 0),
                            "stack_trace": error.get('stack_trace', ''),
                            "timestamp": screenshot.get('timestamp', 0),
                            "screenshot_name": screenshot.get('name', 'unknown'),
                            "url": screenshot.get('url', '')
                        })
        
        # Organize by error type
        error_types = {}
        for error in errors:
            error_type = self._categorize_error_type(error['message'])
            if error_type not in error_types:
                error_types[error_type] = []
            error_types[error_type].append(error)
        
        return {
            "total_errors": len(errors),
            "errors_by_type": error_types,
            "all_errors": errors,
            "summary": {
                "has_critical_errors": len(errors) > 0,
                "unique_error_types": len(error_types)
            }
        }
    
    def _extract_network(self, results: Dict) -> Dict:
        """Extract network request/response data"""
        all_requests = []
        failed_requests = []
        
        # Load comprehensive data from disk if available
        comprehensive_data = self._load_comprehensive_data(results)
        
        if comprehensive_data:
            network_data = comprehensive_data.get('network_data', {})
            all_network_events = network_data.get('all_network_events', [])
            
            # Add all network events and identify failures
            for event in all_network_events:
                request_data = {
                    "url": event.get('url', ''),
                    "method": event.get('method', 'GET'),
                    "status_code": event.get('status', 0),
                    "timestamp": event.get('timestamp', 0),
                    "timing": event.get('timing', {}),
                    "screenshot_name": 'comprehensive'
                }
                all_requests.append(request_data)
                
                # Identify failed requests (4xx, 5xx status codes)
                status = event.get('status', 0)
                if status >= 400:
                    failed_requests.append(request_data)
        else:
            # Fallback: Collect from screenshot artifacts (old structure)
            # Only if comprehensive_data not available
            artifacts = results.get('artifacts', {})
            for screenshot in artifacts.get('screenshots', []):
                if isinstance(screenshot, dict):
                    network_data = screenshot.get('network_data', {})
                    requests = network_data.get('requests', [])
                    
                    for request in requests:
                        all_requests.append({
                            **request,
                            "screenshot_name": screenshot.get('name', 'unknown'),
                            "timestamp": screenshot.get('timestamp', 0)
                        })
                    
                    failed = network_data.get('failed_requests', {}).get('requests', [])
                    for request in failed:
                        failed_requests.append({
                            **request,
                            "screenshot_name": screenshot.get('name', 'unknown'),
                            "timestamp": screenshot.get('timestamp', 0)
                        })
        
        # Organize by status code
        by_status_code = {}
        for request in all_requests:
            status = request.get('status_code', 0)
            if status not in by_status_code:
                by_status_code[status] = []
            by_status_code[status].append(request)
        
        return {
            "total_requests": len(all_requests),
            "failed_requests": failed_requests,
            "requests_by_status_code": by_status_code,
            "all_requests": all_requests,
            "summary": {
                "total_failed": len(failed_requests),
                "success_rate": (len(all_requests) - len(failed_requests)) / len(all_requests) * 100 if all_requests else 100
            }
        }
    
    def _extract_console(self, results: Dict) -> Dict:
        """Extract all console messages"""
        all_messages = []
        
        # Load comprehensive data from disk if available
        comprehensive_data = self._load_comprehensive_data(results)
        
        if comprehensive_data:
            console_data = comprehensive_data.get('console_data', {})
            all_console_logs = console_data.get('all_console_logs', [])
            
            for log in all_console_logs:
                all_messages.append({
                    "type": log.get('type', 'log'),
                    "message": log.get('text', ''),
                    "source": log.get('location', {}).get('url', ''),
                    "timestamp": log.get('timestamp', 0),
                    "screenshot_name": 'comprehensive'
                })
        else:
            # Fallback: Collect from screenshot artifacts (old structure)
            # Only if comprehensive_data not available
            artifacts = results.get('artifacts', {})
            for screenshot in artifacts.get('screenshots', []):
                if isinstance(screenshot, dict):
                    console_data = screenshot.get('console_data', {})
                    
                    # Collect all message types
                    for msg_type in ['errors', 'warnings', 'logs', 'info']:
                        messages = console_data.get(msg_type, {}).get('logs', [])
                        for msg in messages:
                            all_messages.append({
                                "type": msg_type,
                                "message": msg.get('message', ''),
                                "source": msg.get('source', ''),
                                "timestamp": screenshot.get('timestamp', 0),
                                "screenshot_name": screenshot.get('name', 'unknown')
                            })
        
        # Organize by type
        by_type = {}
        for msg in all_messages:
            msg_type = msg['type']
            if msg_type not in by_type:
                by_type[msg_type] = []
            by_type[msg_type].append(msg)
        
        return {
            "total_messages": len(all_messages),
            "messages_by_type": by_type,
            "all_messages": all_messages
        }
    
    def _extract_dom_analysis(self, results: Dict) -> Dict:
        """Extract DOM and element data"""
        comprehensive = results.get('comprehensive_data', {})
        dom_analysis = comprehensive.get('dom_analysis', {})
        
        return {
            "total_elements": len(dom_analysis.get('elements', [])),
            "elements": dom_analysis.get('elements', []),
            "page_structure": dom_analysis.get('page_structure', {}),
            "accessibility": comprehensive.get('accessibility', {})
        }
    
    def _extract_performance(self, results: Dict) -> Dict:
        """Extract performance metrics"""
        performance_data = []
        
        # Load comprehensive data from disk if available
        comprehensive = self._load_comprehensive_data(results)
        
        if comprehensive and 'performance_data' in comprehensive:
            perf = comprehensive.get('performance_data', {})
            if perf:
                performance_data.append({
                    "screenshot_name": 'comprehensive',
                    "timestamp": results.get('execution_time', 0),
                    "metrics": perf
                })
        
        # Fallback: from screenshot artifacts
        artifacts = results.get('artifacts', {})
        for screenshot in artifacts.get('screenshots', []):
            if isinstance(screenshot, dict):
                perf = screenshot.get('performance_data', {})
                if perf:
                    performance_data.append({
                        "screenshot_name": screenshot.get('name', 'unknown'),
                        "timestamp": screenshot.get('timestamp', 0),
                        "metrics": perf
                    })
        
        return {
            "execution_time": results.get('execution_time', 0),
            "performance_snapshots": performance_data,
            "summary": self._calculate_performance_summary(performance_data)
        }
    
    def _extract_timeline(self, results: Dict) -> Dict:
        """Extract complete timeline data"""
        return {
            "organized_timeline": results.get('timeline', []),
            "browser_events": results.get('browser_events', []),
            "server_logs": results.get('server_logs', [])
        }
    
    def _extract_server_logs(self, results: Dict) -> Dict:
        """Extract server logs with categorization"""
        server_logs = results.get('server_logs', [])
        
        # Organize by severity
        by_severity = {}
        by_source = {}
        
        for log in server_logs:
            # Group by severity
            severity = log.get('severity', 'info')
            if severity not in by_severity:
                by_severity[severity] = []
            by_severity[severity].append(log)
            
            # Group by source
            source = log.get('source', 'unknown')
            if source not in by_source:
                by_source[source] = []
            by_source[source].append(log)
        
        return {
            "total_logs": len(server_logs),
            "logs_by_severity": by_severity,
            "logs_by_source": by_source,
            "all_logs": server_logs
        }
    
    def _extract_screenshots_metadata(self, results: Dict) -> Dict:
        """Extract screenshot metadata and index"""
        artifacts = results.get('artifacts', {})
        screenshots = artifacts.get('screenshots', [])
        
        metadata = []
        for idx, screenshot in enumerate(screenshots):
            if isinstance(screenshot, dict):
                metadata.append({
                    "index": idx,
                    "name": screenshot.get('name', f'screenshot_{idx}'),
                    "timestamp": screenshot.get('timestamp', 0),
                    "url": screenshot.get('url', ''),
                    "path": screenshot.get('path', ''),
                    "has_errors": len(screenshot.get('console_data', {}).get('errors', {}).get('logs', [])) > 0,
                    "has_network_failures": len(screenshot.get('network_data', {}).get('failed_requests', {}).get('requests', [])) > 0,
                    "element_count": len(screenshot.get('dom_analysis', {}).get('elements', [])) if 'dom_analysis' in screenshot else 0
                })
        
        return {
            "total_screenshots": len(metadata),
            "screenshots": metadata
        }
    
    def _extract_mockup_comparison(self, results: Dict) -> Dict:
        """Extract mockup comparison results"""
        mockup_data = results.get('mockup_comparison', {})
        
        return {
            "mockup_url": mockup_data.get('mockup_url', ''),
            "implementation_url": mockup_data.get('implementation_url', ''),
            "similarity_score": mockup_data.get('similarity_score', 0),
            "differences": mockup_data.get('differences', []),
            "iterations": mockup_data.get('iterations', [])
        }
    
    def _extract_responsive_results(self, results: Dict) -> Dict:
        """Extract responsive testing results"""
        responsive_data = results.get('responsive_results', {})
        
        viewports = responsive_data.get('viewports', {})
        comparison = responsive_data.get('comparison', {})
        
        return {
            "viewports": viewports,
            "comparison": comparison,
            "performance_by_viewport": responsive_data.get('performance', {})
        }
    
    def _extract_css_iterations(self, results: Dict) -> Dict:
        """Extract CSS iteration results"""
        iterations = results.get('iterations', results.get('css_iterations', []))
        
        return {
            "total_iterations": len(iterations) if isinstance(iterations, list) else 0,
            "iterations": iterations,
            "session_context": results.get('session_context', {})
        }
    
    def _organize_screenshots(self, results: Dict, screenshots_dir: Path):
        """Move screenshots to organized directory"""
        artifacts = results.get('artifacts', {})
        screenshots = artifacts.get('screenshots', [])
        
        for screenshot in screenshots:
            if isinstance(screenshot, dict):
                screenshot_path = screenshot.get('path')
                if screenshot_path and Path(screenshot_path).exists():
                    dest = screenshots_dir / Path(screenshot_path).name
                    shutil.copy2(screenshot_path, dest)
    
    def _organize_traces(self, results: Dict, traces_dir: Path):
        """Move traces to organized directory"""
        artifacts = results.get('artifacts', {})
        traces = artifacts.get('traces', [])
        
        for trace_path in traces:
            if Path(trace_path).exists():
                dest = traces_dir / Path(trace_path).name
                shutil.copy2(trace_path, dest)
    
    def _categorize_error_type(self, error_message: str) -> str:
        """Categorize error by type based on message content"""
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
    
    def _calculate_performance_summary(self, performance_data: list) -> Dict:
        """Calculate aggregate performance metrics"""
        if not performance_data:
            return {}
        
        # Extract metrics from snapshots
        load_times = []
        memory_usage = []
        
        for snapshot in performance_data:
            metrics = snapshot.get('metrics', {})
            summary = metrics.get('performance_summary', {})
            
            if 'page_load_time' in summary:
                load_times.append(summary['page_load_time'])
            if 'memory_usage_mb' in summary:
                memory_usage.append(summary['memory_usage_mb'])
        
        return {
            "average_page_load_time": sum(load_times) / len(load_times) if load_times else 0,
            "max_memory_usage": max(memory_usage) if memory_usage else 0,
            "min_memory_usage": min(memory_usage) if memory_usage else 0
        }
    
    def _load_comprehensive_data(self, results: Dict) -> Dict:
        """Load comprehensive data from disk or from results dict"""
        # First try to get from results (if already loaded)
        comprehensive = results.get('comprehensive_data', {})
        if comprehensive:
            return comprehensive
        
        # Try to load from disk via screenshot artifacts
        artifacts = results.get('artifacts', {})
        screenshots = artifacts.get('screenshots', [])
        
        if screenshots:
            last_screenshot = screenshots[-1]
            # Check if comprehensive_data_path is set
            if isinstance(last_screenshot, dict) and 'comprehensive_data_path' in last_screenshot:
                comp_path = Path(last_screenshot['comprehensive_data_path'])
                if comp_path.exists():
                    try:
                        with open(comp_path, 'r', encoding='utf-8') as f:
                            return json.load(f)
                    except Exception as e:
                        self.logger.warning(f"Could not load comprehensive data from {comp_path}: {e}")
            
            # Try to find comprehensive data file by naming convention
            if isinstance(last_screenshot, dict) and 'path' in last_screenshot:
                screenshot_path = Path(last_screenshot['path'])
                if screenshot_path.exists():
                    # Look for companion comprehensive data file
                    comp_path = screenshot_path.parent / f"{screenshot_path.stem}_comprehensive_data.json"
                    if comp_path.exists():
                        try:
                            with open(comp_path, 'r', encoding='utf-8') as f:
                                return json.load(f)
                        except Exception as e:
                            self.logger.warning(f"Could not load comprehensive data from {comp_path}: {e}")
        
        return {}
    
    def _write_json(self, path: Path, data: Dict):
        """Write JSON data to file with proper formatting"""
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, default=str, ensure_ascii=False)
    
    def get_session_path(self, session_id: str) -> Path:
        """Get path to session directory"""
        return self.artifacts_base_dir / "sessions" / session_id

