"""
Cursor Integration Layer

Transforms CursorFlow raw data into actionable insights for Cursor.
Provides structured recommendations and decision frameworks.
"""

import time
import json
from typing import Dict, List, Optional, Any
from pathlib import Path
import logging


class CursorIntegration:
    """
    Bridge between CursorFlow data collection and Cursor decision-making
    
    Provides structured analysis frameworks and actionable recommendations
    without doing the thinking - just organizing data for Cursor to analyze.
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def format_css_iteration_results(
        self, 
        raw_results: Dict, 
        session_id: str,
        project_context: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Format CSS iteration results for Cursor analysis
        
        Args:
            raw_results: Raw CursorFlow css_iteration_session results
            session_id: Unique session identifier
            project_context: {"framework": "react", "component": "dashboard", ...}
            
        Returns:
            Structured data optimized for Cursor decision-making
        """
        
        # Create session-linked artifacts
        session_artifacts = self._organize_session_artifacts(raw_results, session_id)
        
        # Format for Cursor analysis
        cursor_results = {
            "session_id": session_id,
            "timestamp": time.time(),
            "test_type": "css_iteration",
            "project_context": project_context or {},
            
            # Visual comparison data
            "visual_analysis": {
                "baseline": {
                    "screenshot_path": session_artifacts["baseline_screenshot"],
                    "layout_metrics": raw_results.get("baseline", {}).get("layout_metrics", {}),
                    "computed_styles": raw_results.get("baseline", {}).get("computed_styles", {})
                },
                "iterations": self._format_iterations_for_cursor(
                    raw_results.get("iterations", []), 
                    session_artifacts
                ),
                "comparison_framework": self._get_comparison_framework()
            },
            
            # Decision support data
            "cursor_analysis_guide": {
                "evaluation_criteria": [
                    "visual_hierarchy_improvement",
                    "layout_stability", 
                    "responsive_behavior",
                    "accessibility_impact",
                    "performance_implications"
                ],
                "decision_questions": [
                    "Which iteration best improves visual hierarchy?",
                    "Are there any layout breaking changes?",
                    "Do any iterations introduce console errors?",
                    "Which approach aligns with design system patterns?"
                ],
                "implementation_readiness": self._assess_implementation_readiness(raw_results)
            },
            
            # File management
            "artifact_management": {
                "session_directory": session_artifacts["session_directory"],
                "cleanup_after_decision": session_artifacts["cleanup_paths"],
                "permanent_assets": session_artifacts["keep_paths"]
            },
            
            # Next steps framework
            "recommended_actions": self._generate_action_recommendations(raw_results, project_context)
        }
        
        # Save session data for Cursor reference
        self._save_session_data(cursor_results)
        
        return cursor_results
    
    def format_ui_test_results(
        self,
        raw_results: Dict,
        session_id: str, 
        test_intent: str,
        project_context: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Format UI test results for Cursor analysis
        
        Args:
            raw_results: Raw CursorFlow execute_and_collect results
            session_id: Unique session identifier
            test_intent: "debug_error", "validate_functionality", "explore_behavior"
            project_context: Project and component context
            
        Returns:
            Structured debugging data for Cursor analysis
        """
        
        cursor_results = {
            "session_id": session_id,
            "timestamp": time.time(),
            "test_type": "ui_testing",
            "test_intent": test_intent,
            "project_context": project_context or {},
            
            # Debugging analysis
            "debugging_analysis": {
                "timeline": self._format_timeline_for_cursor(raw_results.get("timeline", [])),
                "error_patterns": self._identify_error_patterns(raw_results),
                "correlation_insights": self._format_correlations_for_cursor(raw_results),
                "browser_diagnostics": self._format_browser_diagnostics(raw_results)
            },
            
            # Investigation framework
            "cursor_investigation_guide": {
                "primary_questions": self._generate_investigation_questions(raw_results, test_intent),
                "follow_up_tests": self._suggest_follow_up_tests(raw_results, test_intent),
                "code_areas_to_examine": self._identify_code_areas(raw_results, project_context)
            },
            
            # Action framework
            "recommended_actions": self._generate_debugging_actions(raw_results, test_intent)
        }
        
        self._save_session_data(cursor_results)
        return cursor_results
    
    def format_persistent_css_results(
        self, 
        raw_results: Dict, 
        project_context: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Format persistent CSS iteration results for Cursor analysis
        
        Enhances standard CSS iteration formatting with persistent session data,
        hot reload information, and session management recommendations.
        
        Args:
            raw_results: Raw CursorFlow css_iteration_persistent results
            project_context: {"framework": "react", "hot_reload": True, ...}
            
        Returns:
            Enhanced analysis data optimized for persistent session workflows
        """
        
        session_id = raw_results.get("session_id", "unknown")
        session_info = raw_results.get("session_info", {})
        
        # Start with standard CSS formatting
        base_results = self.format_css_iteration_results(
            raw_results, session_id, project_context
        )
        
        # Enhance with persistent session data
        enhanced_results = base_results.copy()
        enhanced_results.update({
            
            # Persistent session context
            "session_context": {
                "session_id": session_id,
                "session_persistent": True,
                "hot_reload_available": session_info.get("hot_reload_available", False),
                "hot_reload_used": raw_results.get("hot_reload_used", False),
                "session_age_seconds": session_info.get("age_seconds", 0),
                "iteration_count": session_info.get("iteration_count", 0),
                "session_reused": raw_results.get("summary", {}).get("session_reused", False)
            },
            
            # Enhanced iteration analysis for hot reload
            "persistent_analysis": {
                "hot_reload_effectiveness": self._analyze_hot_reload_effectiveness(raw_results),
                "session_state_consistency": self._assess_session_consistency(raw_results),
                "iteration_speed_metrics": self._calculate_iteration_metrics(raw_results),
                "session_optimization_opportunities": self._identify_optimization_opportunities(raw_results)
            },
            
            # Enhanced recommendations for persistent workflows
            "persistent_workflow_guide": {
                "continue_session_criteria": [
                    "hot_reload_working_effectively",
                    "no_session_state_corruption",
                    "development_server_stable",
                    "browser_memory_usage_acceptable"
                ],
                "restart_session_triggers": [
                    "hot_reload_failures_detected",
                    "significant_console_errors",
                    "session_state_inconsistency",
                    "browser_performance_degradation"
                ],
                "optimization_suggestions": self._identify_optimization_opportunities(raw_results)
            },
            
            # Session management recommendations
            "session_management": {
                "recommended_action": self._recommend_session_action(raw_results),
                "keep_session_alive": self._should_keep_session_alive(raw_results),
                "next_iteration_strategy": self._recommend_next_iteration_strategy(raw_results),
                "cleanup_recommendations": self._generate_cleanup_recommendations(raw_results)
            }
        })
        
        # Update action recommendations for persistent context
        enhanced_results["recommended_actions"] = self._generate_persistent_action_recommendations(
            raw_results, project_context
        )
        
        # Save enhanced session data
        self._save_persistent_session_data(enhanced_results)
        
        return enhanced_results
    
    def _analyze_hot_reload_effectiveness(self, raw_results: Dict) -> Dict[str, Any]:
        """Analyze how effectively hot reload was used"""
        
        iterations = raw_results.get("iterations", [])
        hot_reload_iterations = len([i for i in iterations if i.get("hot_reload_used", False)])
        total_iterations = len(iterations)
        
        return {
            "hot_reload_usage_rate": hot_reload_iterations / total_iterations if total_iterations > 0 else 0,
            "hot_reload_successful": hot_reload_iterations > 0,
            "potential_time_savings": self._estimate_time_savings(raw_results),
            "hot_reload_quality": "excellent" if hot_reload_iterations == total_iterations else "partial"
        }
    
    def _assess_session_consistency(self, raw_results: Dict) -> Dict[str, Any]:
        """Assess whether session state remained consistent"""
        
        session_info = raw_results.get("session_info", {})
        iterations = raw_results.get("iterations", [])
        
        # Check for consistency indicators
        console_error_trend = [len(i.get("console_errors", [])) for i in iterations]
        performance_stability = self._check_performance_stability(iterations)
        
        return {
            "state_consistent": len(set(console_error_trend)) <= 1,  # Error counts consistent
            "performance_stable": performance_stability,
            "session_age_impact": session_info.get("age_seconds", 0) < 1800,  # Under 30 minutes
            "navigation_stability": len(session_info.get("navigation_history", [])) < 10
        }
    
    def _calculate_iteration_metrics(self, raw_results: Dict) -> Dict[str, Any]:
        """Calculate metrics specific to iteration speed and efficiency"""
        
        execution_time = raw_results.get("execution_time", 0)
        total_iterations = len(raw_results.get("iterations", []))
        
        return {
            "total_execution_time": execution_time,
            "average_iteration_time": execution_time / total_iterations if total_iterations > 0 else 0,
            "iterations_per_minute": (total_iterations / execution_time) * 60 if execution_time > 0 else 0,
            "hot_reload_speed_advantage": raw_results.get("hot_reload_used", False)
        }
    
    def _identify_optimization_opportunities(self, raw_results: Dict) -> List[Dict]:
        """Identify opportunities to optimize the iteration process"""
        
        opportunities = []
        session_info = raw_results.get("session_info", {})
        
        # Hot reload not being used
        if not raw_results.get("hot_reload_used", False):
            opportunities.append({
                "optimization": "enable_hot_reload",
                "description": "Hot reload could speed up CSS iterations significantly",
                "potential_benefit": "3-5x faster iteration cycles",
                "implementation": "Configure webpack HMR or Vite hot reload"
            })
        
        # Session getting old
        if session_info.get("age_seconds", 0) > 1800:  # 30 minutes
            opportunities.append({
                "optimization": "session_refresh",
                "description": "Long-running sessions may accumulate performance issues",
                "potential_benefit": "Better memory usage and performance",
                "implementation": "Restart session for fresh environment"
            })
        
        # Too many navigation events
        if len(session_info.get("navigation_history", [])) > 10:
            opportunities.append({
                "optimization": "reduce_navigation",
                "description": "Multiple navigations may slow down iterations",
                "potential_benefit": "Faster CSS application and testing",
                "implementation": "Use component-specific testing when possible"
            })
        
        return opportunities
    
    def _recommend_session_action(self, raw_results: Dict) -> str:
        """Recommend what to do with the current session"""
        
        session_info = raw_results.get("session_info", {})
        summary = raw_results.get("summary", {})
        
        # Check for problems
        failed_iterations = summary.get("failed_iterations", 0)
        session_age = session_info.get("age_seconds", 0)
        hot_reload_available = session_info.get("hot_reload_available", False)
        
        if failed_iterations > 0:
            return "restart_session_due_to_errors"
        elif session_age > 3600:  # 1 hour
            return "restart_session_due_to_age"
        elif hot_reload_available and raw_results.get("hot_reload_used", False):
            return "continue_session_optimal"
        else:
            return "continue_session_standard"
    
    def _should_keep_session_alive(self, raw_results: Dict) -> bool:
        """Determine if session should be kept alive"""
        
        session_info = raw_results.get("session_info", {})
        summary = raw_results.get("summary", {})
        
        # Keep alive if:
        # - Hot reload is working
        # - No major errors
        # - Session is relatively fresh
        # - Performance is good
        
        return (
            session_info.get("hot_reload_available", False) and
            summary.get("failed_iterations", 0) == 0 and
            session_info.get("age_seconds", 0) < 3600 and
            summary.get("successful_iterations", 0) > 0
        )
    
    def _recommend_next_iteration_strategy(self, raw_results: Dict) -> Dict[str, Any]:
        """Recommend strategy for next iteration cycle"""
        
        session_info = raw_results.get("session_info", {})
        hot_reload_used = raw_results.get("hot_reload_used", False)
        
        if hot_reload_used and session_info.get("hot_reload_available", False):
            return {
                "strategy": "continue_with_hot_reload",
                "session_reuse": True,
                "expected_performance": "fast",
                "preparation_needed": "none"
            }
        elif session_info.get("hot_reload_available", False):
            return {
                "strategy": "optimize_for_hot_reload", 
                "session_reuse": True,
                "expected_performance": "improved",
                "preparation_needed": "verify_hot_reload_configuration"
            }
        else:
            return {
                "strategy": "standard_iteration",
                "session_reuse": False,
                "expected_performance": "standard",
                "preparation_needed": "fresh_session_recommended"
            }
    
    def _generate_cleanup_recommendations(self, raw_results: Dict) -> List[Dict]:
        """Generate cleanup recommendations for the session"""
        
        recommendations = []
        session_info = raw_results.get("session_info", {})
        
        # Session-specific cleanup
        if session_info.get("age_seconds", 0) > 3600:
            recommendations.append({
                "action": "restart_browser_session",
                "reason": "long_running_session",
                "priority": "medium"
            })
        
        if session_info.get("applied_css_count", 0) > 20:
            recommendations.append({
                "action": "clear_injected_css",
                "reason": "too_many_css_injections",
                "priority": "low"
            })
        
        return recommendations
    
    def _generate_persistent_action_recommendations(
        self, 
        raw_results: Dict, 
        project_context: Optional[Dict]
    ) -> List[Dict]:
        """Generate action recommendations enhanced for persistent sessions"""
        
        # Start with base recommendations
        base_recommendations = self._generate_action_recommendations(raw_results, project_context)
        
        # Add persistent session specific recommendations
        session_recommendations = []
        
        # Session management recommendations
        session_action = self._recommend_session_action(raw_results)
        if session_action == "continue_session_optimal":
            session_recommendations.append({
                "action": "continue_persistent_session",
                "priority": "high",
                "description": "Session is performing optimally with hot reload",
                "implementation": "Keep session alive for next iteration cycle",
                "benefits": ["Faster iterations", "Maintained application state", "Hot reload advantages"]
            })
        elif session_action.startswith("restart_session"):
            session_recommendations.append({
                "action": "restart_persistent_session",
                "priority": "medium",
                "description": f"Session restart recommended: {session_action}",
                "implementation": "Clean up current session and start fresh",
                "benefits": ["Clean environment", "Better performance", "Reduced memory usage"]
            })
        
        # Hot reload optimization
        if not raw_results.get("hot_reload_used", False):
            session_recommendations.append({
                "action": "configure_hot_reload",
                "priority": "high",
                "description": "Enable hot reload for faster CSS iterations",
                "implementation": "Set up webpack HMR, Vite HMR, or live reload",
                "benefits": ["3-5x faster iterations", "Maintained browser state", "Better development experience"]
            })
        
        return base_recommendations + session_recommendations
    
    def _estimate_time_savings(self, raw_results: Dict) -> Dict[str, Any]:
        """Estimate time savings from hot reload usage"""
        
        total_iterations = len(raw_results.get("iterations", []))
        hot_reload_iterations = len([i for i in raw_results.get("iterations", []) if i.get("hot_reload_used", False)])
        
        # Estimate: standard reload ~2-3 seconds, hot reload ~0.1-0.2 seconds
        standard_reload_time = total_iterations * 2.5  # seconds
        hot_reload_time = hot_reload_iterations * 0.15 + (total_iterations - hot_reload_iterations) * 2.5
        
        return {
            "estimated_standard_time": standard_reload_time,
            "actual_time_with_hot_reload": hot_reload_time, 
            "time_saved_seconds": max(0, standard_reload_time - hot_reload_time),
            "efficiency_improvement": hot_reload_iterations / total_iterations if total_iterations > 0 else 0
        }
    
    def _check_performance_stability(self, iterations: List[Dict]) -> bool:
        """Check if performance remained stable across iterations"""
        
        render_times = []
        for iteration in iterations:
            perf = iteration.get("performance_impact", {}) or iteration.get("performance_metrics", {})
            render_time = perf.get("renderTime", 0) or perf.get("render_time", 0)
            if render_time > 0:
                render_times.append(render_time)
        
        if len(render_times) < 2:
            return True  # Insufficient data, assume stable
        
        # Check if performance degraded significantly
        first_half = render_times[:len(render_times)//2]
        second_half = render_times[len(render_times)//2:]
        
        avg_first = sum(first_half) / len(first_half)
        avg_second = sum(second_half) / len(second_half)
        
        # Performance is stable if second half isn't significantly worse
        return avg_second <= avg_first * 1.5  # Allow 50% degradation threshold
    
    def _save_persistent_session_data(self, enhanced_results: Dict):
        """Save enhanced persistent session data"""
        
        session_id = enhanced_results["session_id"]
        artifacts_base = Path.cwd() / ".cursorflow" / "artifacts"
        session_file = artifacts_base / "sessions" / session_id / "persistent_analysis.json"
        session_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(session_file, 'w') as f:
            json.dump(enhanced_results, f, indent=2)
        
        self.logger.info(f"Enhanced persistent session data saved: {session_file}")
    
    def _organize_session_artifacts(self, raw_results: Dict, session_id: str) -> Dict[str, Any]:
        """Organize artifacts with clear session linking"""
        
        # Create session-specific directory in user's project
        artifacts_base = Path.cwd() / ".cursorflow" / "artifacts"
        session_dir = artifacts_base / "sessions" / session_id
        session_dir.mkdir(parents=True, exist_ok=True)
        
        artifacts = {
            "session_directory": str(session_dir),
            "baseline_screenshot": None,
            "iteration_screenshots": [],
            "cleanup_paths": [],
            "keep_paths": []
        }
        
        # Process baseline
        baseline = raw_results.get("baseline", {})
        if baseline.get("screenshot"):
            baseline_path = session_dir / "baseline.png"
            artifacts["baseline_screenshot"] = str(baseline_path)
            artifacts["keep_paths"].append(str(baseline_path))
        
        # Process iterations
        for i, iteration in enumerate(raw_results.get("iterations", [])):
            if iteration.get("screenshot"):
                iter_name = iteration.get("name", f"iteration_{i+1}")
                iter_path = session_dir / f"{iter_name}.png"
                artifacts["iteration_screenshots"].append({
                    "name": iter_name,
                    "path": str(iter_path),
                    "css_applied": iteration.get("css_applied", ""),
                    "has_errors": len(iteration.get("console_errors", [])) > 0
                })
                artifacts["keep_paths"].append(str(iter_path))
        
        return artifacts
    
    def _format_iterations_for_cursor(self, iterations: List[Dict], session_artifacts: Dict) -> List[Dict]:
        """Format iteration data for Cursor analysis"""
        
        formatted = []
        for i, iteration in enumerate(iterations):
            iteration_data = {
                "name": iteration.get("name", f"iteration_{i+1}"),
                "css_changes": iteration.get("css_applied", ""),
                "rationale": iteration.get("rationale", ""),
                "screenshot_path": session_artifacts["iteration_screenshots"][i]["path"] if i < len(session_artifacts["iteration_screenshots"]) else None,
                
                # Analysis-ready metrics
                "quality_indicators": {
                    "has_console_errors": len(iteration.get("console_errors", [])) > 0,
                    "error_count": len(iteration.get("console_errors", [])),
                    "layout_changes": bool(iteration.get("changes", {}).get("layout_differences")),
                    "style_changes": bool(iteration.get("changes", {}).get("style_differences"))
                },
                
                # Raw data for Cursor's detailed analysis
                "raw_console_errors": iteration.get("console_errors", []),
                "raw_layout_changes": iteration.get("changes", {}).get("layout_differences", {}),
                "raw_style_changes": iteration.get("changes", {}).get("style_differences", {}),
                "raw_performance_metrics": iteration.get("performance_metrics", {})
            }
            formatted.append(iteration_data)
        
        return formatted
    
    def _get_comparison_framework(self) -> Dict[str, Any]:
        """Provide framework for Cursor to compare iterations"""
        
        return {
            "evaluation_dimensions": {
                "visual_improvement": {
                    "description": "Does this iteration improve visual hierarchy and aesthetics?",
                    "data_sources": ["screenshot_comparison", "layout_metrics"],
                    "evaluation_method": "visual_inspection_and_metrics_comparison"
                },
                "technical_stability": {
                    "description": "Does this iteration introduce technical issues?",
                    "data_sources": ["console_errors", "performance_metrics"],
                    "evaluation_method": "error_count_and_performance_analysis"
                },
                "layout_integrity": {
                    "description": "Does this iteration maintain responsive layout integrity?",
                    "data_sources": ["layout_changes", "computed_styles"],
                    "evaluation_method": "layout_difference_analysis"
                }
            },
            
            "decision_process": [
                "1. Eliminate iterations with console errors",
                "2. Compare visual improvements via screenshots", 
                "3. Validate layout stability via metrics",
                "4. Choose iteration with best visual/technical balance",
                "5. Apply chosen CSS to codebase"
            ],
            
            "red_flags": [
                "console_errors_introduced",
                "layout_breaking_changes", 
                "significant_performance_degradation",
                "accessibility_violations"
            ]
        }
    
    def _assess_implementation_readiness(self, raw_results: Dict) -> Dict[str, Any]:
        """Assess which iterations are ready for implementation"""
        
        readiness = {
            "safe_to_implement": [],
            "needs_review": [],
            "not_recommended": []
        }
        
        for iteration in raw_results.get("iterations", []):
            name = iteration.get("name", "unknown")
            has_errors = len(iteration.get("console_errors", [])) > 0
            
            if has_errors:
                readiness["not_recommended"].append({
                    "name": name,
                    "reason": "introduces_console_errors",
                    "error_count": len(iteration.get("console_errors", []))
                })
            elif iteration.get("changes", {}).get("layout_differences"):
                readiness["needs_review"].append({
                    "name": name,
                    "reason": "significant_layout_changes",
                    "review_points": ["responsive_behavior", "cross_browser_compatibility"]
                })
            else:
                readiness["safe_to_implement"].append({
                    "name": name,
                    "reason": "no_issues_detected"
                })
        
        return readiness
    
    def _generate_action_recommendations(self, raw_results: Dict, project_context: Optional[Dict]) -> List[Dict]:
        """Generate specific action recommendations for Cursor"""
        
        recommendations = []
        
        # Analyze results and suggest actions
        safe_iterations = [
            iter for iter in raw_results.get("iterations", [])
            if len(iter.get("console_errors", [])) == 0
        ]
        
        if safe_iterations:
            best_iteration = safe_iterations[0]  # Cursor should choose based on visual analysis
            recommendations.append({
                "action": "implement_css_changes",
                "priority": "high",
                "iteration": best_iteration.get("name"),
                "css_to_apply": best_iteration.get("css_applied"),
                "target_files": self._identify_target_files(best_iteration, project_context),
                "implementation_notes": [
                    "Test across multiple browsers",
                    "Validate responsive behavior",
                    "Run accessibility audit"
                ]
            })
        
        if any(len(iter.get("console_errors", [])) > 0 for iter in raw_results.get("iterations", [])):
            recommendations.append({
                "action": "investigate_console_errors",
                "priority": "medium", 
                "affected_iterations": [
                    iter.get("name") for iter in raw_results.get("iterations", [])
                    if len(iter.get("console_errors", [])) > 0
                ],
                "next_steps": [
                    "Review CSS syntax and browser compatibility",
                    "Test iterations individually",
                    "Consider alternative CSS approaches"
                ]
            })
        
        return recommendations
    
    def _identify_target_files(self, iteration: Dict, project_context: Optional[Dict]) -> List[str]:
        """Identify which files should be modified for implementation"""
        
        if not project_context:
            return ["styles.css"]  # Generic fallback
        
        framework = project_context.get("framework", "")
        component = project_context.get("component", "")
        
        if framework == "react":
            return [f"{component}.css", f"{component}.module.css", "globals.css"]
        elif framework == "vue":
            return [f"{component}.vue", "main.css"]
        else:
            return ["main.css", "styles.css"]
    
    def _save_session_data(self, cursor_results: Dict):
        """Save session data for Cursor reference and debugging"""
        
        session_id = cursor_results["session_id"]
        artifacts_base = Path.cwd() / ".cursorflow" / "artifacts"
        session_file = artifacts_base / "sessions" / session_id / "cursor_analysis.json"
        session_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(session_file, 'w') as f:
            json.dump(cursor_results, f, indent=2)
        
        self.logger.info(f"Session data saved: {session_file}")
    
    # Additional methods for UI testing results formatting...
    def _format_timeline_for_cursor(self, timeline: List[Dict]) -> Dict:
        """Format timeline for Cursor analysis"""
        return {"formatted": True, "events": timeline}  # Placeholder
    
    def _identify_error_patterns(self, raw_results: Dict) -> Dict:
        """Identify error patterns for Cursor analysis"""
        return {"patterns": []}  # Placeholder
    
    def _format_correlations_for_cursor(self, raw_results: Dict) -> Dict:
        """Format correlations for Cursor analysis"""
        return {"correlations": []}  # Placeholder
    
    def _format_browser_diagnostics(self, raw_results: Dict) -> Dict:
        """Format browser diagnostics for Cursor analysis"""
        return {"diagnostics": {}}  # Placeholder
    
    def _generate_investigation_questions(self, raw_results: Dict, test_intent: str) -> List[str]:
        """Generate investigation questions for Cursor"""
        return []  # Placeholder
    
    def _suggest_follow_up_tests(self, raw_results: Dict, test_intent: str) -> List[Dict]:
        """Suggest follow-up tests for Cursor"""
        return []  # Placeholder
    
    def _identify_code_areas(self, raw_results: Dict, project_context: Optional[Dict]) -> List[str]:
        """Identify code areas for Cursor to examine"""
        return []  # Placeholder
    
    def _generate_debugging_actions(self, raw_results: Dict, test_intent: str) -> List[Dict]:
        """Generate debugging actions for Cursor"""
        return []  # Placeholder
    
    def format_mockup_comparison_results(
        self,
        raw_results: Dict,
        session_id: str,
        project_context: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Format mockup comparison results for Cursor analysis
        
        Args:
            raw_results: Raw MockupComparator comparison results
            session_id: Unique session identifier
            project_context: {"framework": "react", "component": "dashboard", ...}
            
        Returns:
            Structured comparison data optimized for Cursor decision-making
        """
        
        cursor_results = {
            "session_id": session_id,
            "timestamp": time.time(),
            "test_type": "mockup_comparison",
            "project_context": project_context or {},
            
            # Comparison overview
            "comparison_overview": {
                "mockup_url": raw_results.get("mockup_url"),
                "implementation_url": raw_results.get("implementation_url"),
                "comparison_id": raw_results.get("comparison_id"),
                "viewports_tested": raw_results.get("viewports_tested", 0),
                "overall_similarity": raw_results.get("summary", {}).get("average_similarity", 0),
                "needs_improvement": raw_results.get("summary", {}).get("needs_improvement", True)
            },
            
            # Viewport analysis
            "viewport_analysis": self._format_viewport_results_for_cursor(raw_results.get("results", [])),
            
            # Visual difference analysis
            "visual_analysis": {
                "similarity_breakdown": self._analyze_similarity_breakdown(raw_results),
                "major_differences": self._extract_major_differences(raw_results),
                "layout_discrepancies": self._analyze_layout_discrepancies(raw_results),
                "element_mismatches": self._analyze_element_mismatches(raw_results)
            },
            
            # Decision support framework
            "cursor_analysis_guide": {
                "evaluation_criteria": [
                    "visual_similarity_score",
                    "layout_structure_match",
                    "element_positioning_accuracy",
                    "color_and_typography_consistency",
                    "responsive_behavior_alignment"
                ],
                "decision_questions": [
                    "Which viewport has the best mockup match?",
                    "What are the most critical visual differences to address?",
                    "Are there layout structure issues or just styling differences?",
                    "Which differences impact user experience most?",
                    "What's the priority order for fixing discrepancies?"
                ],
                "improvement_strategy": self._generate_improvement_strategy(raw_results)
            },
            
            # Actionable recommendations
            "recommended_actions": self._generate_mockup_comparison_actions(raw_results, project_context),
            
            # Artifact management
            "artifact_management": {
                "visual_diffs": self._organize_visual_diff_artifacts(raw_results),
                "screenshots": self._organize_screenshot_artifacts(raw_results),
                "comparison_reports": self._organize_comparison_artifacts(raw_results)
            }
        }
        
        # Save session data
        self._save_session_data(cursor_results)
        
        return cursor_results
    
    def format_iterative_mockup_results(
        self,
        raw_results: Dict,
        session_id: str,
        project_context: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Format iterative mockup matching results for Cursor analysis
        
        Args:
            raw_results: Raw MockupComparator iterative_ui_matching results
            session_id: Unique session identifier
            project_context: Project context information
            
        Returns:
            Structured iteration data optimized for Cursor decision-making
        """
        
        cursor_results = {
            "session_id": session_id,
            "timestamp": time.time(),
            "test_type": "iterative_mockup_matching",
            "project_context": project_context or {},
            
            # Iteration overview
            "iteration_overview": {
                "mockup_url": raw_results.get("mockup_url"),
                "implementation_url": raw_results.get("implementation_url"),
                "total_iterations": raw_results.get("total_iterations", 0),
                "successful_iterations": raw_results.get("summary", {}).get("successful_iterations", 0),
                "total_improvement": raw_results.get("summary", {}).get("total_improvement", 0),
                "best_similarity_achieved": self._get_best_similarity(raw_results)
            },
            
            # Baseline comparison
            "baseline_analysis": {
                "initial_similarity": self._get_baseline_similarity(raw_results),
                "major_issues_identified": self._extract_baseline_issues(raw_results),
                "improvement_potential": self._assess_improvement_potential(raw_results)
            },
            
            # Iteration progression analysis
            "iteration_analysis": {
                "progression": self._analyze_iteration_progression(raw_results),
                "successful_changes": self._extract_successful_changes(raw_results),
                "failed_attempts": self._extract_failed_attempts(raw_results),
                "best_iteration": self._format_best_iteration_for_cursor(raw_results)
            },
            
            # Implementation guidance
            "implementation_guidance": {
                "css_changes_to_apply": self._extract_css_changes_to_apply(raw_results),
                "implementation_order": self._recommend_implementation_order(raw_results),
                "testing_requirements": self._generate_testing_requirements(raw_results),
                "rollback_strategy": self._generate_rollback_strategy(raw_results)
            },
            
            # Decision support framework
            "cursor_analysis_guide": {
                "evaluation_criteria": [
                    "improvement_magnitude",
                    "css_change_complexity",
                    "risk_of_breaking_changes",
                    "alignment_with_design_system",
                    "cross_browser_compatibility"
                ],
                "decision_questions": [
                    "Which CSS changes provide the most visual improvement?",
                    "Are there any changes that might break existing functionality?",
                    "What's the optimal order for implementing changes?",
                    "Which changes should be tested most thoroughly?",
                    "Are there alternative approaches for failed iterations?"
                ],
                "next_steps": self._generate_next_steps(raw_results)
            },
            
            # Actionable recommendations
            "recommended_actions": self._generate_iterative_mockup_actions(raw_results, project_context)
        }
        
        # Save session data
        self._save_session_data(cursor_results)
        
        return cursor_results
    
    def _format_viewport_results_for_cursor(self, viewport_results: List[Dict]) -> List[Dict]:
        """Format viewport comparison results for Cursor analysis"""
        
        formatted_results = []
        for result in viewport_results:
            viewport = result.get("viewport", {})
            visual_diff = result.get("visual_diff", {})
            layout_analysis = result.get("layout_analysis", {})
            
            formatted_result = {
                "viewport_name": viewport.get("name", "unknown"),
                "viewport_size": f"{viewport.get('width', 0)}x{viewport.get('height', 0)}",
                "similarity_score": visual_diff.get("similarity_score", 0),
                "similarity_grade": self._grade_similarity(visual_diff.get("similarity_score", 0)),
                "major_differences": visual_diff.get("major_differences", []),
                "layout_issues": len(layout_analysis.get("differences", [])),
                "visual_diff_path": visual_diff.get("highlighted_diff"),
                "mockup_screenshot": result.get("mockup_screenshot"),
                "implementation_screenshot": result.get("implementation_screenshot"),
                "needs_attention": visual_diff.get("similarity_score", 0) < 75
            }
            formatted_results.append(formatted_result)
        
        return formatted_results
    
    def _grade_similarity(self, similarity_score: float) -> str:
        """Grade similarity score for easier interpretation"""
        if similarity_score >= 90:
            return "excellent"
        elif similarity_score >= 80:
            return "good"
        elif similarity_score >= 70:
            return "fair"
        elif similarity_score >= 60:
            return "poor"
        else:
            return "critical"
    
    def _analyze_similarity_breakdown(self, raw_results: Dict) -> Dict[str, Any]:
        """Analyze similarity scores across viewports"""
        
        results = raw_results.get("results", [])
        if not results:
            return {"error": "No viewport results available"}
        
        similarities = [r.get("visual_diff", {}).get("similarity_score", 0) for r in results]
        
        return {
            "best_similarity": max(similarities) if similarities else 0,
            "worst_similarity": min(similarities) if similarities else 0,
            "average_similarity": sum(similarities) / len(similarities) if similarities else 0,
            "similarity_range": max(similarities) - min(similarities) if similarities else 0,
            "consistent_across_viewports": (max(similarities) - min(similarities)) < 10 if similarities else False
        }
    
    def _extract_major_differences(self, raw_results: Dict) -> List[Dict]:
        """Extract major visual differences across all viewports"""
        
        major_differences = []
        for result in raw_results.get("results", []):
            viewport = result.get("viewport", {})
            visual_diff = result.get("visual_diff", {})
            
            for diff in visual_diff.get("major_differences", []):
                major_differences.append({
                    "viewport": viewport.get("name", "unknown"),
                    "region": diff,
                    "severity": "high" if diff.get("area", 0) > 10000 else "medium"
                })
        
        return major_differences
    
    def _analyze_layout_discrepancies(self, raw_results: Dict) -> Dict[str, Any]:
        """Analyze layout structure discrepancies"""
        
        layout_issues = []
        for result in raw_results.get("results", []):
            layout_analysis = result.get("layout_analysis", {})
            viewport = result.get("viewport", {})
            
            for diff in layout_analysis.get("differences", []):
                layout_issues.append({
                    "viewport": viewport.get("name", "unknown"),
                    "type": diff.get("type"),
                    "element": diff.get("selector"),
                    "issue": diff
                })
        
        # Categorize issues
        missing_elements = [issue for issue in layout_issues if issue["type"] == "missing_in_implementation"]
        extra_elements = [issue for issue in layout_issues if issue["type"] == "missing_in_mockup"]
        property_differences = [issue for issue in layout_issues if issue["type"] == "property_differences"]
        
        return {
            "missing_elements": len(missing_elements),
            "extra_elements": len(extra_elements),
            "property_differences": len(property_differences),
            "total_issues": len(layout_issues),
            "critical_missing": [issue for issue in missing_elements if issue["element"] in ["nav", "header", "main", "footer"]],
            "detailed_issues": layout_issues
        }
    
    def _analyze_element_mismatches(self, raw_results: Dict) -> Dict[str, Any]:
        """Analyze element-level mismatches"""
        
        # This could be enhanced with more detailed element analysis
        return {
            "analysis": "Element mismatch analysis placeholder",
            "common_issues": ["positioning", "sizing", "styling"],
            "recommendations": ["Review CSS selectors", "Check responsive breakpoints", "Validate design tokens"]
        }
    
    def _generate_improvement_strategy(self, raw_results: Dict) -> Dict[str, Any]:
        """Generate improvement strategy based on comparison results"""
        
        summary = raw_results.get("summary", {})
        avg_similarity = summary.get("average_similarity", 0)
        
        if avg_similarity >= 85:
            strategy = "fine_tuning"
            priority = "low"
            approach = "Minor adjustments to achieve pixel-perfect match"
        elif avg_similarity >= 70:
            strategy = "targeted_improvements"
            priority = "medium"
            approach = "Focus on major visual differences and layout issues"
        else:
            strategy = "comprehensive_redesign"
            priority = "high"
            approach = "Significant changes needed to match mockup design"
        
        return {
            "strategy": strategy,
            "priority": priority,
            "approach": approach,
            "estimated_effort": self._estimate_improvement_effort(avg_similarity),
            "recommended_phases": self._recommend_improvement_phases(raw_results)
        }
    
    def _estimate_improvement_effort(self, similarity: float) -> str:
        """Estimate effort required for improvement"""
        if similarity >= 85:
            return "low"
        elif similarity >= 70:
            return "medium"
        elif similarity >= 50:
            return "high"
        else:
            return "very_high"
    
    def _recommend_improvement_phases(self, raw_results: Dict) -> List[Dict]:
        """Recommend phases for improvement implementation"""
        
        phases = []
        
        # Phase 1: Critical layout issues
        layout_issues = self._analyze_layout_discrepancies(raw_results)
        if layout_issues["missing_elements"] > 0 or layout_issues["critical_missing"]:
            phases.append({
                "phase": 1,
                "name": "Fix Critical Layout Issues",
                "description": "Address missing elements and major layout structure problems",
                "priority": "high",
                "estimated_time": "2-4 hours"
            })
        
        # Phase 2: Visual styling improvements
        major_diffs = self._extract_major_differences(raw_results)
        if major_diffs:
            phases.append({
                "phase": 2,
                "name": "Visual Styling Improvements",
                "description": "Address major visual differences in colors, typography, spacing",
                "priority": "medium",
                "estimated_time": "1-3 hours"
            })
        
        # Phase 3: Fine-tuning
        phases.append({
            "phase": 3,
            "name": "Fine-tuning and Polish",
            "description": "Minor adjustments for pixel-perfect match",
            "priority": "low",
            "estimated_time": "1-2 hours"
        })
        
        return phases
    
    def _generate_mockup_comparison_actions(self, raw_results: Dict, project_context: Optional[Dict]) -> List[Dict]:
        """Generate specific actions for mockup comparison results"""
        
        actions = []
        summary = raw_results.get("summary", {})
        
        # High-priority actions based on similarity
        if summary.get("average_similarity", 0) < 70:
            actions.append({
                "action": "address_critical_differences",
                "priority": "high",
                "description": "Significant visual differences detected - major improvements needed",
                "implementation": "Review layout structure and major styling differences",
                "estimated_time": "3-6 hours"
            })
        
        # Layout-specific actions
        layout_issues = self._analyze_layout_discrepancies(raw_results)
        if layout_issues["missing_elements"] > 0:
            actions.append({
                "action": "add_missing_elements",
                "priority": "high",
                "description": f"Add {layout_issues['missing_elements']} missing elements to match mockup",
                "implementation": "Review mockup for missing components and add to implementation",
                "affected_elements": [issue["element"] for issue in layout_issues["detailed_issues"] if issue["type"] == "missing_in_implementation"]
            })
        
        # Viewport-specific actions
        viewport_results = raw_results.get("results", [])
        poor_viewports = [r for r in viewport_results if r.get("visual_diff", {}).get("similarity_score", 0) < 60]
        if poor_viewports:
            actions.append({
                "action": "fix_responsive_issues",
                "priority": "medium",
                "description": f"Poor similarity on {len(poor_viewports)} viewport(s) - responsive design issues",
                "implementation": "Review CSS media queries and responsive design patterns",
                "affected_viewports": [r.get("viewport", {}).get("name", "unknown") for r in poor_viewports]
            })
        
        return actions
    
    def _get_best_similarity(self, raw_results: Dict) -> float:
        """Get the best similarity score achieved across all iterations"""
        
        best_similarity = 0
        for iteration in raw_results.get("iterations", []):
            similarity = iteration.get("improvement_metrics", {}).get("improved_similarity", 0)
            best_similarity = max(best_similarity, similarity)
        
        return best_similarity
    
    def _get_baseline_similarity(self, raw_results: Dict) -> float:
        """Get baseline similarity before iterations"""
        
        baseline_comparison = raw_results.get("baseline_comparison", {})
        if "results" in baseline_comparison and baseline_comparison["results"]:
            return baseline_comparison["results"][0].get("visual_diff", {}).get("similarity_score", 0)
        return 0
    
    def _extract_baseline_issues(self, raw_results: Dict) -> List[Dict]:
        """Extract major issues identified in baseline comparison"""
        
        baseline_comparison = raw_results.get("baseline_comparison", {})
        recommendations = baseline_comparison.get("recommendations", [])
        
        return [
            {
                "type": rec.get("type", "unknown"),
                "description": rec.get("description", ""),
                "priority": rec.get("priority", "medium")
            }
            for rec in recommendations
        ]
    
    def _assess_improvement_potential(self, raw_results: Dict) -> Dict[str, Any]:
        """Assess potential for improvement based on baseline"""
        
        baseline_similarity = self._get_baseline_similarity(raw_results)
        
        if baseline_similarity >= 80:
            potential = "low"
            description = "Already close to mockup - minor improvements possible"
        elif baseline_similarity >= 60:
            potential = "medium"
            description = "Good foundation - moderate improvements achievable"
        else:
            potential = "high"
            description = "Significant room for improvement"
        
        return {
            "potential": potential,
            "description": description,
            "baseline_similarity": baseline_similarity,
            "target_similarity": min(95, baseline_similarity + 20)  # Realistic target
        }
    
    def _analyze_iteration_progression(self, raw_results: Dict) -> Dict[str, Any]:
        """Analyze how similarity improved across iterations"""
        
        iterations = raw_results.get("iterations", [])
        progression = []
        
        for i, iteration in enumerate(iterations):
            metrics = iteration.get("improvement_metrics", {})
            progression.append({
                "iteration": i + 1,
                "name": iteration.get("css_change", {}).get("name", "unnamed"),
                "similarity": metrics.get("improved_similarity", 0),
                "improvement": metrics.get("improvement", 0),
                "is_improvement": metrics.get("is_improvement", False)
            })
        
        # Calculate trends
        improvements = [p["improvement"] for p in progression]
        total_improvement = sum(improvements)
        positive_iterations = len([p for p in progression if p["is_improvement"]])
        
        return {
            "progression_data": progression,
            "total_improvement": total_improvement,
            "positive_iterations": positive_iterations,
            "success_rate": positive_iterations / len(progression) if progression else 0,
            "trend": "improving" if total_improvement > 0 else "declining"
        }
    
    def _extract_successful_changes(self, raw_results: Dict) -> List[Dict]:
        """Extract CSS changes that improved similarity"""
        
        successful_changes = []
        for iteration in raw_results.get("iterations", []):
            if iteration.get("improvement_metrics", {}).get("is_improvement", False):
                css_change = iteration.get("css_change", {})
                successful_changes.append({
                    "name": css_change.get("name", "unnamed"),
                    "css": css_change.get("css", ""),
                    "rationale": css_change.get("rationale", ""),
                    "improvement": iteration.get("improvement_metrics", {}).get("improvement", 0),
                    "final_similarity": iteration.get("improvement_metrics", {}).get("improved_similarity", 0)
                })
        
        return successful_changes
    
    def _extract_failed_attempts(self, raw_results: Dict) -> List[Dict]:
        """Extract CSS changes that didn't improve similarity"""
        
        failed_attempts = []
        for iteration in raw_results.get("iterations", []):
            if not iteration.get("improvement_metrics", {}).get("is_improvement", False):
                css_change = iteration.get("css_change", {})
                failed_attempts.append({
                    "name": css_change.get("name", "unnamed"),
                    "css": css_change.get("css", ""),
                    "rationale": css_change.get("rationale", ""),
                    "impact": iteration.get("improvement_metrics", {}).get("improvement", 0),
                    "reason_for_failure": self._analyze_failure_reason(iteration)
                })
        
        return failed_attempts
    
    def _analyze_failure_reason(self, iteration: Dict) -> str:
        """Analyze why an iteration failed to improve similarity"""
        
        # Check for console errors
        css_result = iteration.get("css_result", {})
        if css_result.get("console_errors"):
            return "introduced_console_errors"
        
        # Check for negative impact
        improvement = iteration.get("improvement_metrics", {}).get("improvement", 0)
        if improvement < -5:
            return "significantly_worsened_appearance"
        elif improvement < 0:
            return "minor_negative_impact"
        else:
            return "no_measurable_improvement"
    
    def _format_best_iteration_for_cursor(self, raw_results: Dict) -> Optional[Dict]:
        """Format the best iteration for Cursor analysis"""
        
        best_iteration_data = raw_results.get("best_iteration")
        if not best_iteration_data:
            return None
        
        return {
            "iteration_number": best_iteration_data.get("iteration_number"),
            "name": best_iteration_data.get("css_change", {}).get("name", "unnamed"),
            "css_changes": best_iteration_data.get("css_change", {}).get("css", ""),
            "rationale": best_iteration_data.get("css_change", {}).get("rationale", ""),
            "similarity_achieved": best_iteration_data.get("similarity_achieved", 0),
            "improvement_amount": best_iteration_data.get("improvement", 0),
            "implementation_ready": True,  # Best iteration is typically safe to implement
            "testing_notes": [
                "Validate across all target browsers",
                "Test responsive behavior",
                "Check for accessibility impact"
            ]
        }
    
    def _extract_css_changes_to_apply(self, raw_results: Dict) -> List[Dict]:
        """Extract CSS changes that should be applied to the codebase"""
        
        # Get successful changes and the best iteration
        successful_changes = self._extract_successful_changes(raw_results)
        best_iteration = raw_results.get("best_iteration")
        
        changes_to_apply = []
        
        # Always include the best iteration if it exists
        if best_iteration:
            css_change = best_iteration.get("css_change", {})
            changes_to_apply.append({
                "name": css_change.get("name", "best_iteration"),
                "css": css_change.get("css", ""),
                "rationale": css_change.get("rationale", ""),
                "priority": "high",
                "reason": "best_overall_improvement"
            })
        
        # Include other successful changes that don't conflict
        for change in successful_changes:
            if not any(c["name"] == change["name"] for c in changes_to_apply):
                changes_to_apply.append({
                    **change,
                    "priority": "medium",
                    "reason": "positive_improvement"
                })
        
        return changes_to_apply
    
    def _recommend_implementation_order(self, raw_results: Dict) -> List[Dict]:
        """Recommend order for implementing CSS changes"""
        
        changes = self._extract_css_changes_to_apply(raw_results)
        
        # Sort by improvement amount (highest first)
        changes.sort(key=lambda x: x.get("improvement", 0), reverse=True)
        
        implementation_order = []
        for i, change in enumerate(changes):
            implementation_order.append({
                "order": i + 1,
                "name": change["name"],
                "css": change["css"],
                "rationale": f"Implement {change['name']} - provides {change.get('improvement', 0):.1f}% improvement",
                "validation_steps": [
                    "Apply CSS changes",
                    "Test visual appearance",
                    "Validate responsive behavior",
                    "Run mockup comparison again"
                ]
            })
        
        return implementation_order
    
    def _generate_testing_requirements(self, raw_results: Dict) -> List[Dict]:
        """Generate testing requirements for implementation"""
        
        requirements = []
        
        # Viewport testing
        viewports_tested = raw_results.get("viewports_tested", 0)
        if viewports_tested > 1:
            requirements.append({
                "type": "responsive_testing",
                "description": f"Test across {viewports_tested} viewport sizes",
                "priority": "high",
                "tools": ["Browser dev tools", "Responsive design mode"]
            })
        
        # Visual regression testing
        requirements.append({
            "type": "visual_regression",
            "description": "Compare implementation to mockup after changes",
            "priority": "high",
            "tools": ["CursorFlow mockup comparison", "Visual diff tools"]
        })
        
        # Cross-browser testing
        requirements.append({
            "type": "cross_browser",
            "description": "Validate appearance across major browsers",
            "priority": "medium",
            "tools": ["Chrome", "Firefox", "Safari", "Edge"]
        })
        
        return requirements
    
    def _generate_rollback_strategy(self, raw_results: Dict) -> Dict[str, Any]:
        """Generate rollback strategy in case of issues"""
        
        return {
            "backup_recommendation": "Create git branch before implementing changes",
            "rollback_triggers": [
                "Visual regression in production",
                "Responsive layout breaks",
                "Accessibility issues introduced",
                "Performance degradation"
            ],
            "rollback_steps": [
                "Revert CSS changes",
                "Clear browser cache",
                "Test original functionality",
                "Run mockup comparison to confirm baseline"
            ],
            "monitoring": "Monitor user feedback and analytics for visual issues"
        }
    
    def _generate_next_steps(self, raw_results: Dict) -> List[Dict]:
        """Generate next steps based on iteration results"""
        
        next_steps = []
        
        # Implementation steps
        successful_changes = self._extract_successful_changes(raw_results)
        if successful_changes:
            next_steps.append({
                "step": "implement_successful_changes",
                "description": f"Apply {len(successful_changes)} successful CSS changes to codebase",
                "priority": "high",
                "estimated_time": "1-2 hours"
            })
        
        # Further iteration if needed
        best_similarity = self._get_best_similarity(raw_results)
        if best_similarity < 85:
            next_steps.append({
                "step": "additional_iterations",
                "description": f"Current best similarity: {best_similarity}% - consider additional improvements",
                "priority": "medium",
                "estimated_time": "2-4 hours"
            })
        
        # Validation steps
        next_steps.append({
            "step": "validate_implementation",
            "description": "Test implementation across browsers and devices",
            "priority": "high",
            "estimated_time": "1 hour"
        })
        
        return next_steps
    
    def _generate_iterative_mockup_actions(self, raw_results: Dict, project_context: Optional[Dict]) -> List[Dict]:
        """Generate specific actions for iterative mockup matching results"""
        
        actions = []
        
        # Implementation actions
        changes_to_apply = self._extract_css_changes_to_apply(raw_results)
        if changes_to_apply:
            actions.append({
                "action": "apply_successful_css_changes",
                "priority": "high",
                "description": f"Apply {len(changes_to_apply)} successful CSS changes",
                "implementation": "Follow recommended implementation order",
                "changes": changes_to_apply,
                "estimated_time": "1-3 hours"
            })
        
        # Further improvement actions
        best_similarity = self._get_best_similarity(raw_results)
        if best_similarity < 90:
            actions.append({
                "action": "continue_improvement_iterations",
                "priority": "medium",
                "description": f"Best similarity achieved: {best_similarity}% - room for improvement",
                "implementation": "Design additional CSS improvements and run another iteration cycle",
                "target_similarity": "90%+",
                "estimated_time": "2-4 hours"
            })
        
        # Validation actions
        actions.append({
            "action": "comprehensive_testing",
            "priority": "high",
            "description": "Validate implementation across browsers and devices",
            "implementation": "Follow generated testing requirements",
            "testing_requirements": self._generate_testing_requirements(raw_results),
            "estimated_time": "1-2 hours"
        })
        
        return actions
    
    def _organize_visual_diff_artifacts(self, raw_results: Dict) -> List[Dict]:
        """Organize visual diff artifacts for easy access"""
        
        artifacts = []
        for result in raw_results.get("results", []):
            viewport = result.get("viewport", {})
            visual_diff = result.get("visual_diff", {})
            
            if visual_diff.get("highlighted_diff"):
                artifacts.append({
                    "type": "visual_diff",
                    "viewport": viewport.get("name", "unknown"),
                    "path": visual_diff.get("highlighted_diff"),
                    "similarity_score": visual_diff.get("similarity_score", 0)
                })
        
        return artifacts
    
    def _organize_screenshot_artifacts(self, raw_results: Dict) -> List[Dict]:
        """Organize screenshot artifacts for easy access"""
        
        artifacts = []
        for result in raw_results.get("results", []):
            viewport = result.get("viewport", {})
            
            # Mockup screenshot
            if result.get("mockup_screenshot"):
                artifacts.append({
                    "type": "mockup_screenshot",
                    "viewport": viewport.get("name", "unknown"),
                    "path": result.get("mockup_screenshot")
                })
            
            # Implementation screenshot
            if result.get("implementation_screenshot"):
                artifacts.append({
                    "type": "implementation_screenshot",
                    "viewport": viewport.get("name", "unknown"),
                    "path": result.get("implementation_screenshot")
                })
        
        return artifacts
    
    def _organize_comparison_artifacts(self, raw_results: Dict) -> List[Dict]:
        """Organize comparison report artifacts"""
        
        return [{
            "type": "comparison_report",
            "comparison_id": raw_results.get("comparison_id"),
            "path": f".cursorflow/artifacts/mockup_comparisons/{raw_results.get('comparison_id')}.json"
        }]