"""
Universal Report Generator

Creates comprehensive, Cursor-friendly test reports with actionable debugging
information. Works across all web frameworks.
"""

import json
import os
from typing import Dict, List, Any, Optional
from datetime import datetime
from pathlib import Path
import logging

class ReportGenerator:
    """Universal test report generator"""
    
    def __init__(self, output_dir: str = "test_reports"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        self.logger = logging.getLogger(__name__)
    
    def create_markdown_report(self, results: Dict) -> str:
        """Create comprehensive markdown report for Cursor"""
        
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        framework = results.get('framework', 'unknown')
        component = results.get('component', 'unknown')
        success = results.get('success', False)
        
        # Build report content
        report = f"""# Test Report - {component} ({framework})

**Generated**: {timestamp}  
**Status**: {'✅ PASSED' if success else '❌ FAILED'}  
**Framework**: {framework}  
**Component**: {component}

## 🎯 **Test Summary**

"""
        
        # Add summary table
        correlations = results.get('correlations', {})
        summary = correlations.get('summary', {})
        
        report += f"""| Metric | Value |
|--------|-------|
| Browser Events | {summary.get('total_browser_events', 0)} |
| Server Log Entries | {summary.get('total_server_logs', 0)} |
| Correlations Found | {summary.get('correlations_found', 0)} |
| Critical Issues | {summary.get('critical_issues', 0)} |
| Errors | {summary.get('error_count', 0)} |
| Warnings | {summary.get('warning_count', 0)} |

"""
        
        # Critical Issues Section
        critical_issues = correlations.get('critical_issues', [])
        if critical_issues:
            report += f"""## 🚨 **Critical Issues ({len(critical_issues)})**

"""
            for i, issue in enumerate(critical_issues, 1):
                browser_event = issue['browser_event']
                server_logs = issue['server_logs']
                confidence = issue.get('correlation_confidence', 0)
                
                report += f"""### Issue {i}: {browser_event.get('action', 'Unknown Action')}
**Confidence**: {confidence:.1%}  
**Browser Action**: {browser_event.get('action', 'N/A')} at {datetime.fromtimestamp(browser_event['timestamp']).strftime('%H:%M:%S')}  
**Server Errors**: {len(server_logs)} related log entries

**Server Log Details**:
"""
                
                for log in server_logs[:3]:  # Show top 3 most relevant
                    report += f"""```
{log['content']}
```
**Error Type**: {log.get('error_type', 'Unknown')}  
**Suggested Fix**: {log.get('suggested_fix', 'No specific recommendation')}

"""
        
        # Recommendations Section
        recommendations = correlations.get('recommendations', [])
        if recommendations:
            report += f"""## 💡 **Recommendations ({len(recommendations)})**

"""
            for rec in recommendations:
                priority_emoji = {
                    'critical': '🚨',
                    'high': '⚠️',
                    'medium': '📋',
                    'low': '💭'
                }.get(rec.get('priority', 'medium'), '📋')
                
                report += f"""### {priority_emoji} {rec.get('title', 'Recommendation')}
**Priority**: {rec.get('priority', 'medium')}  
**Description**: {rec.get('description', 'No description')}  
**Action**: {rec.get('action', 'No specific action')}

"""
        
        # Browser Events Section
        browser_results = results.get('browser_results', {})
        workflows = browser_results.get('workflows', {})
        
        if workflows:
            report += f"""## 🔄 **Workflow Results**

"""
            for workflow_name, workflow_result in workflows.items():
                success_emoji = '✅' if workflow_result.get('success', False) else '❌'
                report += f"""### {success_emoji} {workflow_name}
**Duration**: {workflow_result.get('duration', 0):.2f}s  
**Actions**: {len(workflow_result.get('actions', []))}  
**Errors**: {len(workflow_result.get('errors', []))}

"""
        
        # Performance Metrics
        performance = browser_results.get('performance_metrics', {})
        if performance:
            report += f"""## ⚡ **Performance Metrics**

| Metric | Value |
|--------|-------|
| Page Load Time | {performance.get('page_load_time', 0)}ms |
| DOM Ready Time | {performance.get('dom_ready_time', 0)}ms |
| Resource Count | {performance.get('resource_count', 0)} |
| Memory Usage | {performance.get('memory_usage', {}).get('used', 0) / 1024 / 1024:.1f}MB |

"""
        
        # Console Errors
        console_errors = browser_results.get('console_errors', [])
        if console_errors:
            report += f"""## 🖥️ **Browser Console Errors ({len(console_errors)})**

"""
            for error in console_errors[:5]:  # Show top 5
                report += f"""**{error.get('level', 'error').upper()}**: {error.get('text', 'Unknown error')}  
**Location**: {error.get('location', {}).get('url', 'Unknown')}:{error.get('location', {}).get('lineNumber', '?')}

"""
        
        # Network Requests
        network_requests = browser_results.get('network_requests', [])
        failed_requests = [req for req in network_requests if req.get('type') == 'response' and req.get('status', 0) >= 400]
        
        if failed_requests:
            report += f"""## 🌐 **Failed Network Requests ({len(failed_requests)})**

"""
            for req in failed_requests[:5]:
                report += f"""**{req.get('status', '?')}**: {req.get('url', 'Unknown URL')}  
**Method**: {req.get('method', 'Unknown')}

"""
        
        # Raw Data Section (for debugging)
        report += f"""## 🔍 **Debug Information**

<details>
<summary>Click to expand raw test data</summary>

```json
{json.dumps(results, indent=2, default=str)}
```

</details>

---

**Generated by Cursor Testing Agent v1.0.0**  
**Framework Adapter**: {framework}  
**Report Time**: {timestamp}
"""
        
        return report
    
    def save_report(self, results: Dict, filename: Optional[str] = None) -> str:
        """Save report to file and return path"""
        
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            component = results.get('component', 'unknown')
            filename = f"test_report_{component}_{timestamp}.md"
        
        report_content = self.create_markdown_report(results)
        report_path = self.output_dir / filename
        
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(report_content)
        
        self.logger.info(f"Report saved to: {report_path}")
        return str(report_path)
    
    def create_summary_report(self, multiple_results: Dict[str, Dict]) -> str:
        """Create summary report for multiple test runs"""
        
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        total_tests = len(multiple_results)
        passed_tests = sum(1 for result in multiple_results.values() if result.get('success', False))
        
        report = f"""# Multi-Component Test Summary

**Generated**: {timestamp}  
**Total Tests**: {total_tests}  
**Passed**: {passed_tests}  
**Failed**: {total_tests - passed_tests}  
**Success Rate**: {(passed_tests / total_tests * 100):.1f}%

## 📊 **Test Results Overview**

| Component | Framework | Status | Errors | Warnings |
|-----------|-----------|--------|--------|----------|
"""
        
        for test_name, result in multiple_results.items():
            framework = result.get('framework', 'unknown')
            success = '✅ PASS' if result.get('success', False) else '❌ FAIL'
            
            correlations = result.get('correlations', {})
            summary = correlations.get('summary', {})
            errors = summary.get('error_count', 0)
            warnings = summary.get('warning_count', 0)
            
            report += f"| {test_name} | {framework} | {success} | {errors} | {warnings} |\n"
        
        # Critical Issues Across All Tests
        all_critical = []
        for result in multiple_results.values():
            critical = result.get('correlations', {}).get('critical_issues', [])
            all_critical.extend(critical)
        
        if all_critical:
            report += f"""
## 🚨 **Critical Issues Requiring Attention**

"""
            for i, issue in enumerate(all_critical[:5], 1):
                browser_event = issue['browser_event']
                report += f"{i}. **{browser_event.get('action', 'Unknown')}** - {len(issue['server_logs'])} server errors\n"
        
        # Overall Recommendations
        report += f"""
## 💡 **Overall Recommendations**

"""
        if passed_tests == total_tests:
            report += "🎉 All tests passed! No immediate action required.\n"
        elif passed_tests == 0:
            report += "🚨 All tests failed. Review critical issues and check basic connectivity.\n"
        else:
            report += f"⚠️ {total_tests - passed_tests} tests failed. Focus on critical issues first.\n"
        
        return report
    
    def create_json_report(self, results: Dict) -> str:
        """Create machine-readable JSON report"""
        
        # Clean up results for JSON serialization
        json_results = self._clean_for_json(results)
        
        return json.dumps(json_results, indent=2, default=str)
    
    def _clean_for_json(self, data: Any) -> Any:
        """Clean data for JSON serialization"""
        
        if isinstance(data, dict):
            return {k: self._clean_for_json(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [self._clean_for_json(item) for item in data]
        elif isinstance(data, datetime):
            return data.isoformat()
        else:
            return data
