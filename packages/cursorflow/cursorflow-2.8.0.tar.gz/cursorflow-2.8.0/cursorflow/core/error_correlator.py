"""
Universal Error Correlator

Correlates browser events with server log entries to provide intelligent
debugging insights. Works across all web frameworks.
"""

import re
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
import logging

class ErrorCorrelator:
    """Universal error correlation engine"""
    
    def __init__(self, error_patterns: Dict[str, Dict]):
        """
        Initialize error correlator with framework-specific patterns
        
        Args:
            error_patterns: Framework-specific error patterns from adapter
        """
        self.error_patterns = error_patterns
        self.correlations = []
        
        self.logger = logging.getLogger(__name__)
    
    def correlate_events(
        self, 
        browser_events: List[Dict], 
        server_logs: List[Dict],
        time_window: int = 5
    ) -> Dict[str, Any]:
        """
        Correlate browser events with server log entries
        
        Args:
            browser_events: List of browser events (clicks, AJAX, errors)
            server_logs: List of server log entries
            time_window: Time window in seconds for correlation
            
        Returns:
            Correlation results with matched events and recommendations
        """
        
        self.logger.info(f"Correlating {len(browser_events)} browser events with {len(server_logs)} server logs")
        
        correlations = []
        critical_issues = []
        recommendations = []
        
        # Categorize server logs by error patterns
        categorized_logs = self._categorize_server_logs(server_logs)
        
        # Find correlations between browser events and server errors
        for browser_event in browser_events:
            if browser_event.get('type') in ['action_start', 'action_complete']:
                related_logs = self._find_related_logs(
                    browser_event, categorized_logs['errors'], time_window
                )
                
                if related_logs:
                    correlation = {
                        'browser_event': browser_event,
                        'server_logs': related_logs,
                        'correlation_confidence': self._calculate_confidence(browser_event, related_logs),
                        'time_window': time_window,
                        'recommended_fixes': self._generate_fix_recommendations(related_logs)
                    }
                    correlations.append(correlation)
                    
                    # Check for critical issues
                    if any(log.get('severity') == 'critical' for log in related_logs):
                        critical_issues.append(correlation)
        
        # Analyze standalone server errors (not correlated with browser events)
        standalone_errors = self._find_standalone_errors(categorized_logs['errors'], correlations)
        
        # Generate overall recommendations
        all_errors = categorized_logs['errors'] + categorized_logs['warnings']
        overall_recommendations = self._generate_overall_recommendations(all_errors)
        
        results = {
            'correlations': correlations,
            'critical_issues': critical_issues,
            'standalone_errors': standalone_errors,
            'categorized_logs': categorized_logs,
            'recommendations': overall_recommendations,
            'summary': {
                'total_browser_events': len(browser_events),
                'total_server_logs': len(server_logs),
                'correlations_found': len(correlations),
                'critical_issues': len(critical_issues),
                'error_count': len(categorized_logs['errors']),
                'warning_count': len(categorized_logs['warnings'])
            }
        }
        
        return results
    
    def _categorize_server_logs(self, server_logs: List[Dict]) -> Dict[str, List[Dict]]:
        """Categorize server logs using error patterns"""
        
        categorized = {
            'errors': [],
            'warnings': [],
            'info': [],
            'unknown': []
        }
        
        for log_entry in server_logs:
            content = log_entry['content']
            enhanced_entry = log_entry.copy()
            
            # Try to match against error patterns
            matched = False
            for pattern_name, pattern_config in self.error_patterns.items():
                if re.search(pattern_config['regex'], content, re.IGNORECASE):
                    enhanced_entry.update({
                        'error_type': pattern_name,
                        'severity': pattern_config['severity'],
                        'description': pattern_config['description'],
                        'suggested_fix': pattern_config['suggested_fix'],
                        'pattern_matched': pattern_name
                    })
                    
                    # Categorize by severity
                    if pattern_config['severity'] in ['critical', 'high']:
                        categorized['errors'].append(enhanced_entry)
                    elif pattern_config['severity'] == 'medium':
                        categorized['warnings'].append(enhanced_entry)
                    else:
                        categorized['info'].append(enhanced_entry)
                    
                    matched = True
                    break
            
            if not matched:
                # Basic heuristic categorization
                content_lower = content.lower()
                if any(word in content_lower for word in ['error', 'failed', 'exception', 'critical', 'fatal']):
                    enhanced_entry['severity'] = 'high'
                    categorized['errors'].append(enhanced_entry)
                elif any(word in content_lower for word in ['warning', 'warn']):
                    enhanced_entry['severity'] = 'medium'
                    categorized['warnings'].append(enhanced_entry)
                else:
                    enhanced_entry['severity'] = 'low'
                    categorized['info'].append(enhanced_entry)
        
        return categorized
    
    def _find_related_logs(
        self, 
        browser_event: Dict, 
        server_errors: List[Dict], 
        time_window: int
    ) -> List[Dict]:
        """Find server logs related to a browser event"""
        
        related = []
        browser_time = datetime.fromtimestamp(browser_event['timestamp'])
        
        for server_log in server_errors:
            server_time = server_log['timestamp']
            
            # Calculate time difference
            time_diff = abs((browser_time - server_time).total_seconds())
            
            if time_diff <= time_window:
                # Additional correlation logic based on event type
                correlation_strength = self._calculate_event_correlation(browser_event, server_log)
                
                if correlation_strength > 0.3:  # Threshold for correlation
                    server_log_enhanced = server_log.copy()
                    server_log_enhanced['correlation_strength'] = correlation_strength
                    server_log_enhanced['time_diff'] = time_diff
                    related.append(server_log_enhanced)
        
        # Sort by correlation strength
        related.sort(key=lambda x: x.get('correlation_strength', 0), reverse=True)
        
        return related
    
    def _calculate_event_correlation(self, browser_event: Dict, server_log: Dict) -> float:
        """Calculate correlation strength between browser event and server log"""
        
        correlation = 0.0
        
        # Time proximity (closer = higher correlation)
        browser_time = datetime.fromtimestamp(browser_event['timestamp'])
        server_time = server_log['timestamp']
        time_diff = abs((browser_time - server_time).total_seconds())
        
        if time_diff <= 1:
            correlation += 0.4
        elif time_diff <= 3:
            correlation += 0.2
        elif time_diff <= 5:
            correlation += 0.1
        
        # Event type correlation
        browser_action = browser_event.get('action', browser_event.get('type', ''))
        server_content = server_log['content'].lower()
        
        action_correlations = {
            'click': ['ajax', 'post', 'submit'],
            'ajax_call': ['ajax', 'perl', 'function'],
            'navigation': ['get', 'request', 'page'],
            'form_submit': ['post', 'form', 'submit']
        }
        
        if browser_action in action_correlations:
            for keyword in action_correlations[browser_action]:
                if keyword in server_content:
                    correlation += 0.2
                    break
        
        # URL/component correlation
        if 'url' in browser_event:
            browser_url = browser_event['url']
            if any(part in server_content for part in browser_url.split('/') if len(part) > 3):
                correlation += 0.3
        
        # AJAX function correlation (mod_perl specific)
        if browser_event.get('type') == 'ajax_call' and 'fn' in browser_event.get('data', {}):
            function_name = browser_event['data']['fn']
            if function_name in server_content:
                correlation += 0.5
        
        return min(correlation, 1.0)  # Cap at 1.0
    
    def _calculate_confidence(self, browser_event: Dict, related_logs: List[Dict]) -> float:
        """Calculate overall confidence in correlation"""
        
        if not related_logs:
            return 0.0
        
        # Average correlation strength
        avg_correlation = sum(log.get('correlation_strength', 0) for log in related_logs) / len(related_logs)
        
        # Boost confidence if multiple logs correlate
        multi_log_boost = min(len(related_logs) * 0.1, 0.3)
        
        # Boost confidence for critical errors
        critical_boost = 0.2 if any(log.get('severity') == 'critical' for log in related_logs) else 0
        
        confidence = avg_correlation + multi_log_boost + critical_boost
        
        return min(confidence, 1.0)
    
    def _generate_fix_recommendations(self, related_logs: List[Dict]) -> List[str]:
        """Generate fix recommendations based on correlated logs"""
        
        recommendations = []
        seen_fixes = set()
        
        for log in related_logs:
            suggested_fix = log.get('suggested_fix')
            if suggested_fix and suggested_fix not in seen_fixes:
                recommendations.append(suggested_fix)
                seen_fixes.add(suggested_fix)
        
        return recommendations
    
    def _find_standalone_errors(self, server_errors: List[Dict], correlations: List[Dict]) -> List[Dict]:
        """Find server errors that don't correlate with browser events"""
        
        # Get server logs that are already correlated
        correlated_log_ids = set()
        for correlation in correlations:
            for log in correlation['server_logs']:
                log_id = f"{log['timestamp']}_{log['content']}"
                correlated_log_ids.add(log_id)
        
        # Find standalone errors
        standalone = []
        for log in server_errors:
            log_id = f"{log['timestamp']}_{log['content']}"
            if log_id not in correlated_log_ids:
                standalone.append(log)
        
        return standalone
    
    def _generate_overall_recommendations(self, all_errors: List[Dict]) -> List[Dict]:
        """Generate overall recommendations based on all errors"""
        
        recommendations = []
        
        # Group errors by type
        error_types = {}
        for error in all_errors:
            error_type = error.get('error_type', 'unknown')
            if error_type not in error_types:
                error_types[error_type] = []
            error_types[error_type].append(error)
        
        # Generate recommendations for each error type
        for error_type, errors in error_types.items():
            if len(errors) > 1:
                recommendations.append({
                    'type': 'pattern',
                    'priority': 'high',
                    'title': f"Multiple {error_type} errors detected",
                    'description': f"Found {len(errors)} instances of {error_type}",
                    'action': f"Review and fix {error_type} pattern across the application",
                    'affected_areas': [error.get('source', 'unknown') for error in errors]
                })
        
        # Critical error recommendations
        critical_errors = [error for error in all_errors if error.get('severity') == 'critical']
        if critical_errors:
            recommendations.append({
                'type': 'critical',
                'priority': 'critical',
                'title': f"{len(critical_errors)} critical errors require immediate attention",
                'description': "These errors prevent normal application functionality",
                'action': "Fix critical errors before continuing development",
                'details': [error.get('description', error.get('content', '')) for error in critical_errors[:3]]
            })
        
        return recommendations
