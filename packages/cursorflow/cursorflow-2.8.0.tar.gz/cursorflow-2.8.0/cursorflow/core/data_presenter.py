"""
Data Presenter - AI-Optimized Data Organization

Presents test data in structured markdown format optimized for AI consumption.
Pure data organization without analysis or recommendations.
"""

from pathlib import Path
from typing import Dict, Any
import json
from datetime import datetime


class DataPresenter:
    """
    Generates AI-optimized markdown presentation of test data.
    
    Philosophy: Organize and present raw data clearly for AI analysis.
    No subjective recommendations, no analysis - just structured information.
    """
    
    def generate_data_digest(
        self, 
        session_dir: Path,
        results: Dict[str, Any]
    ) -> str:
        """
        Generate AI-optimized data digest from test results.
        
        Args:
            session_dir: Path to session directory with split data files
            results: Original complete results dictionary
            
        Returns:
            Markdown string with organized data presentation
        """
        # Load split data files
        summary = self._load_json(session_dir / "summary.json")
        errors = self._load_json(session_dir / "errors.json")
        network = self._load_json(session_dir / "network.json")
        console = self._load_json(session_dir / "console.json")
        performance = self._load_json(session_dir / "performance.json")
        server_logs = self._load_json(session_dir / "server_logs.json")
        screenshots = self._load_json(session_dir / "screenshots.json")
        
        # Optional data files
        mockup = self._load_json(session_dir / "mockup_comparison.json")
        responsive = self._load_json(session_dir / "responsive_results.json")
        css_iterations = self._load_json(session_dir / "css_iterations.json")
        
        # Build markdown digest
        digest = self._build_header(summary)
        digest += self._build_quick_stats(summary, errors, network, console, server_logs)
        digest += self._build_errors_section(errors, session_dir)
        digest += self._build_network_section(network, session_dir)
        digest += self._build_console_section(console, session_dir)
        digest += self._build_server_logs_section(server_logs, session_dir)
        digest += self._build_screenshots_section(screenshots, session_dir)
        
        # Optional sections
        if mockup:
            digest += self._build_mockup_section(mockup, session_dir)
        if responsive:
            digest += self._build_responsive_section(responsive, session_dir)
        if css_iterations and css_iterations.get('total_iterations', 0) > 0:
            digest += self._build_css_iterations_section(css_iterations, session_dir)
        
        digest += self._build_performance_section(performance, session_dir)
        digest += self._build_data_references(session_dir)
        digest += self._build_metadata(summary)
        
        return digest
    
    def _build_header(self, summary: Dict) -> str:
        """Build document header with basic info"""
        session_id = summary.get('session_id', 'unknown')
        timestamp = summary.get('timestamp', '')
        success = summary.get('success', False)
        
        status_emoji = "✅" if success else "⚠️"
        status_text = "Completed" if success else "Needs Attention"
        
        return f"""# CursorFlow Test Data Digest

**Session**: `{session_id}`  
**Timestamp**: {timestamp}  
**Status**: {status_emoji} {status_text}  
**Execution Time**: {summary.get('execution_time', 0):.2f}s

---

"""
    
    def _build_quick_stats(
        self, 
        summary: Dict, 
        errors: Dict, 
        network: Dict, 
        console: Dict,
        server_logs: Dict
    ) -> str:
        """Build quick statistics table"""
        metrics = summary.get('metrics', {})
        
        return f"""## Quick Statistics

| Metric | Value | Status |
|--------|-------|--------|
| DOM Elements | {metrics.get('total_dom_elements', 0)} | ℹ️ Data |
| Network Requests | {metrics.get('total_network_requests', 0)} | ℹ️ Data |
| Failed Requests | {metrics.get('failed_network_requests', 0)} | {"⚠️ Review" if metrics.get('failed_network_requests', 0) > 0 else "✅ OK"} |
| Console Errors | {metrics.get('total_errors', 0)} | {"🚨 Review" if metrics.get('total_errors', 0) > 0 else "✅ OK"} |
| Console Warnings | {metrics.get('total_warnings', 0)} | {"⚠️ Review" if metrics.get('total_warnings', 0) > 0 else "✅ OK"} |
| Server Logs | {server_logs.get('total_logs', 0)} | ℹ️ Data |
| Server Errors | {len(server_logs.get('logs_by_severity', {}).get('error', []))} | {"🚨 Review" if len(server_logs.get('logs_by_severity', {}).get('error', [])) > 0 else "✅ OK"} |
| Total Messages | {console.get('total_messages', 0)} | ℹ️ Data |
| Screenshots | {metrics.get('total_screenshots', 0)} | ℹ️ Data |
| Timeline Events | {metrics.get('total_timeline_events', 0)} | ℹ️ Data |

---

"""
    
    def _build_errors_section(self, errors: Dict, session_dir: Path) -> str:
        """Build errors section with categorization"""
        total_errors = errors.get('total_errors', 0)
        
        if total_errors == 0:
            return """## Console Errors

✅ **No console errors detected**

---

"""
        
        section = f"""## Console Errors

**Total Errors**: {total_errors}  
**Unique Error Types**: {errors.get('summary', {}).get('unique_error_types', 0)}

### Errors by Type

"""
        
        # Organize by error type
        errors_by_type = errors.get('errors_by_type', {})
        for error_type, error_list in errors_by_type.items():
            section += f"""#### {error_type.replace('_', ' ').title()} ({len(error_list)})\n\n"""
            
            # Show first 3 errors of each type
            for i, error in enumerate(error_list[:3], 1):
                section += f"""**Error #{i}**  
- **Message**: `{error.get('message', 'Unknown')[:200]}`  
- **Source**: `{error.get('source', 'Unknown')}`  
- **Location**: Line {error.get('line', '?')}, Column {error.get('column', '?')}  
- **Screenshot**: `{error.get('screenshot_name', 'unknown')}`  
- **URL**: `{error.get('url', '')[:100]}`

"""
            
            if len(error_list) > 3:
                section += f"*...and {len(error_list) - 3} more errors of this type*\n\n"
        
        section += f"""**Full Error Data**: See `{session_dir.name}/errors.json` for complete error details and stack traces.

---

"""
        return section
    
    def _build_network_section(self, network: Dict, session_dir: Path) -> str:
        """Build network requests section"""
        total_requests = network.get('total_requests', 0)
        failed_requests = network.get('failed_requests', [])
        
        section = f"""## Network Activity

**Total Requests**: {total_requests}  
**Failed Requests**: {len(failed_requests)}  
**Success Rate**: {network.get('summary', {}).get('success_rate', 100):.1f}%

"""
        
        if failed_requests:
            section += f"""### Failed Requests ({len(failed_requests)})

"""
            # Group by status code
            by_status = {}
            for req in failed_requests:
                status = req.get('status_code', 0)
                if status not in by_status:
                    by_status[status] = []
                by_status[status].append(req)
            
            for status_code in sorted(by_status.keys()):
                requests = by_status[status_code]
                section += f"""#### HTTP {status_code} ({len(requests)} requests)

"""
                for i, req in enumerate(requests[:5], 1):
                    section += f"""**Request #{i}**  
- **URL**: `{req.get('url', 'Unknown')[:100]}`  
- **Method**: {req.get('method', 'GET')}  
- **Status**: {req.get('status_code', 0)}  
- **Screenshot**: `{req.get('screenshot_name', 'unknown')}`

"""
                
                if len(requests) > 5:
                    section += f"*...and {len(requests) - 5} more {status_code} errors*\n\n"
        else:
            section += "✅ **All network requests successful**\n\n"
        
        section += f"""**Full Network Data**: See `{session_dir.name}/network.json` for complete request/response details.

---

"""
        return section
    
    def _build_console_section(self, console: Dict, session_dir: Path) -> str:
        """Build console messages section"""
        total_messages = console.get('total_messages', 0)
        messages_by_type = console.get('messages_by_type', {})
        
        section = f"""## Console Messages

**Total Messages**: {total_messages}

"""
        
        if total_messages == 0:
            return section + "No console messages captured.\n\n---\n\n"
        
        # Show counts by type
        section += "### Message Breakdown\n\n"
        for msg_type, messages in messages_by_type.items():
            emoji = {
                'errors': '🚨',
                'warnings': '⚠️',
                'logs': '📝',
                'info': 'ℹ️'
            }.get(msg_type, '📋')
            
            section += f"- {emoji} **{msg_type.title()}**: {len(messages)}\n"
        
        section += f"""\n**Full Console Data**: See `{session_dir.name}/console.json` for all console messages.

---

"""
        return section
    
    def _build_performance_section(self, performance: Dict, session_dir: Path) -> str:
        """Build performance metrics section"""
        summary = performance.get('summary', {})
        execution_time = performance.get('execution_time', 0)
        
        section = f"""## Performance Metrics

**Test Execution Time**: {execution_time:.2f}s

"""
        
        if summary:
            avg_load = summary.get('average_page_load_time', 0)
            max_memory = summary.get('max_memory_usage', 0)
            
            section += f"""### Page Performance

- **Average Load Time**: {avg_load:.1f}ms
- **Max Memory Usage**: {max_memory:.1f}MB
- **Min Memory Usage**: {summary.get('min_memory_usage', 0):.1f}MB

"""
        
        section += f"""**Full Performance Data**: See `{session_dir.name}/performance.json` for detailed metrics.

---

"""
        return section
    
    def _build_data_references(self, session_dir: Path) -> str:
        """Build section with references to all data files"""
        return f"""## Complete Data Files

All comprehensive data available in: `{session_dir.name}/`

### Structured Data Files

| File | Description | Use Case |
|------|-------------|----------|
| `summary.json` | High-level metrics and counts | Quick overview, status checking |
| `errors.json` | All console errors with context | Error analysis, debugging |
| `network.json` | Complete network request/response data | API debugging, performance analysis |
| `console.json` | All console messages (errors, warnings, logs) | Application flow analysis |
| `server_logs.json` | Server-side logs (SSH/local/Docker) | Backend correlation, server debugging |
| `dom_analysis.json` | Complete DOM structure and elements | UI analysis, element inspection |
| `performance.json` | Performance metrics and timing | Performance optimization |
| `timeline.json` | Chronological event timeline | Understanding test flow, correlation |
| `screenshots.json` | Screenshot metadata and index | Screenshot navigation, filtering |

### Optional Data Files

| File | Description | When Present |
|------|-------------|--------------|
| `mockup_comparison.json` | Mockup vs implementation comparison | When using `compare-mockup` |
| `responsive_results.json` | Multi-viewport testing results | When using `--responsive` flag |
| `css_iterations.json` | CSS iteration history | When using `css_iteration_session()` |

### Artifact Directories

| Directory | Contents |
|-----------|----------|
| `screenshots/` | Visual captures at key moments |
| `traces/` | Playwright trace files (open with: `playwright show-trace`) |

---

"""
    
    def _build_metadata(self, summary: Dict) -> str:
        """Build metadata section"""
        return f"""## Metadata

```json
{{
  "session_id": "{summary.get('session_id', 'unknown')}",
  "timestamp": "{summary.get('timestamp', '')}",
  "success": {str(summary.get('success', False)).lower()},
  "execution_time": {summary.get('execution_time', 0)},
  "has_errors": {str(summary.get('status', {}).get('has_errors', False)).lower()},
  "has_network_failures": {str(summary.get('status', {}).get('has_network_failures', False)).lower()},
  "has_warnings": {str(summary.get('status', {}).get('has_warnings', False)).lower()}
}}
```

---

**Generated by CursorFlow v2.7.0** - AI-Optimized Data Collection  
**Format**: Multi-file structured output for AI consumption  
**Philosophy**: Pure data organization, no analysis - AI does the thinking
"""
    
    def _build_server_logs_section(self, server_logs: Dict, session_dir: Path) -> str:
        """Build server logs section"""
        total_logs = server_logs.get('total_logs', 0)
        
        if total_logs == 0:
            return """## Server Logs

✅ **No server logs captured** (log monitoring may not be configured)

---

"""
        
        section = f"""## Server Logs

**Total Server Logs**: {total_logs}

### Server Logs by Severity

"""
        
        logs_by_severity = server_logs.get('logs_by_severity', {})
        for severity, logs in logs_by_severity.items():
            emoji = {
                'error': '🚨',
                'warning': '⚠️',
                'info': 'ℹ️',
                'debug': '🔍'
            }.get(severity.lower(), '📝')
            
            section += f"- {emoji} **{severity.title()}**: {len(logs)}\n"
        
        # Show error logs if present
        error_logs = logs_by_severity.get('error', [])
        if error_logs:
            section += f"""\n### Server Error Logs ({len(error_logs)})

"""
            for i, log in enumerate(error_logs[:5], 1):
                section += f"""**Log #{i}**  
- **Content**: `{log.get('content', 'Unknown')[:150]}`  
- **Source**: {log.get('source', 'unknown')}  
- **File**: `{log.get('file', 'unknown')}`  
- **Timestamp**: {log.get('timestamp', 0)}

"""
            
            if len(error_logs) > 5:
                section += f"*...and {len(error_logs) - 5} more server errors*\n\n"
        
        section += f"""**Full Server Log Data**: See `{session_dir.name}/server_logs.json` for all server logs.

---

"""
        return section
    
    def _build_screenshots_section(self, screenshots: Dict, session_dir: Path) -> str:
        """Build screenshots section"""
        total = screenshots.get('total_screenshots', 0)
        
        if total == 0:
            return ""
        
        section = f"""## Screenshots

**Total Screenshots**: {total}

"""
        
        screenshot_list = screenshots.get('screenshots', [])
        screenshots_with_errors = [s for s in screenshot_list if s.get('has_errors')]
        screenshots_with_network_failures = [s for s in screenshot_list if s.get('has_network_failures')]
        
        if screenshots_with_errors:
            section += f"- 🚨 **With Console Errors**: {len(screenshots_with_errors)}\n"
        if screenshots_with_network_failures:
            section += f"- ⚠️ **With Network Failures**: {len(screenshots_with_network_failures)}\n"
        
        section += f"""\n**Screenshot Index**: See `{session_dir.name}/screenshots.json` for complete metadata.  
**Screenshot Files**: See `{session_dir.name}/screenshots/` directory.

---

"""
        return section
    
    def _build_mockup_section(self, mockup: Dict, session_dir: Path) -> str:
        """Build mockup comparison section"""
        similarity = mockup.get('similarity_score', 0)
        
        section = f"""## Mockup Comparison

**Mockup URL**: `{mockup.get('mockup_url', 'N/A')}`  
**Implementation URL**: `{mockup.get('implementation_url', 'N/A')}`  
**Similarity Score**: {similarity:.1f}%

"""
        
        differences = mockup.get('differences', [])
        if differences:
            section += f"**Differences Detected**: {len(differences)}\n\n"
        
        section += f"""**Full Mockup Data**: See `{session_dir.name}/mockup_comparison.json` for detailed comparison.

---

"""
        return section
    
    def _build_responsive_section(self, responsive: Dict, session_dir: Path) -> str:
        """Build responsive testing section"""
        viewports = responsive.get('viewports', {})
        
        section = f"""## Responsive Testing

**Viewports Tested**: {len(viewports)}

"""
        
        for viewport_name, viewport_data in viewports.items():
            errors = viewport_data.get('errors', 0)
            network_failures = viewport_data.get('network_failures', 0)
            
            section += f"- **{viewport_name.title()}**: "
            if errors > 0 or network_failures > 0:
                section += f"{errors} errors, {network_failures} network failures\n"
            else:
                section += "✅ OK\n"
        
        section += f"""\n**Full Responsive Data**: See `{session_dir.name}/responsive_results.json` for all viewport results.

---

"""
        return section
    
    def _build_css_iterations_section(self, css_iterations: Dict, session_dir: Path) -> str:
        """Build CSS iterations section"""
        total = css_iterations.get('total_iterations', 0)
        
        section = f"""## CSS Iterations

**Total Iterations**: {total}

"""
        
        iterations = css_iterations.get('iterations', [])
        for i, iteration in enumerate(iterations[:5], 1):
            section += f"- **Iteration {i}**: {iteration.get('name', 'unnamed')}\n"
        
        if len(iterations) > 5:
            section += f"*...and {len(iterations) - 5} more iterations*\n"
        
        section += f"""\n**Full CSS Iteration Data**: See `{session_dir.name}/css_iterations.json` for all iterations.

---

"""
        return section
    
    def _load_json(self, path: Path) -> Dict:
        """Load JSON file, return empty dict if not found"""
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            return {}
        except json.JSONDecodeError:
            return {}

