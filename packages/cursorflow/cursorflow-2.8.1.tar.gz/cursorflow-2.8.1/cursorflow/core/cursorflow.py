"""
CursorFlow - Main API Class

Simple, fast data collection engine that enables Cursor to autonomously test UI 
and iterate on designs with immediate visual feedback.

Design Philosophy: Declarative Actions | Batch Execution | Universal Correlation
"""

import asyncio
import time
import logging
from typing import Dict, List, Optional, Any
from pathlib import Path

from .browser_controller import BrowserController
from .log_collector import LogCollector  
from .event_correlator import EventCorrelator
from .auth_handler import AuthHandler
from .css_iterator import CSSIterator
from .cursor_integration import CursorIntegration
from .persistent_session import PersistentSession, get_session_manager
from .mockup_comparator import MockupComparator
from .output_manager import OutputManager
from .data_presenter import DataPresenter


class CursorFlow:
    """
    Main CursorFlow interface - Simple data collection for Cursor analysis
    
    Usage:
        flow = CursorFlow("http://localhost:3000", {"source": "local", "paths": ["logs/app.log"]})
        
        # Test UI flow
        results = await flow.execute_and_collect([
            {"navigate": "/dashboard"},
            {"click": "#refresh"},
            {"screenshot": "refreshed"}
        ])
        
        # CSS iteration
        visual_results = await flow.css_iteration_session(
            base_actions=[{"navigate": "/page"}],
            css_changes=[{"name": "fix", "css": ".item { margin: 1rem; }"}]
        )
    """
    
    def __init__(
        self, 
        base_url: str, 
        log_config: Dict, 
        auth_config: Optional[Dict] = None,
        browser_config: Optional[Dict] = None
    ):
        """
        Initialize CursorFlow with environment configuration
        
        Args:
            base_url: "http://localhost:3000" or "https://staging.example.com"
            log_config: {"source": "ssh|local|docker", "host": "...", "paths": [...]}
            auth_config: {"method": "form", "username_selector": "#user", ...}
            browser_config: {"headless": True, "debug_mode": False}
        """
        self.base_url = base_url
        self.log_config = log_config
        self.auth_config = auth_config or {}
        self.browser_config = browser_config or {"headless": True}
        
        # Initialize core components
        self.browser = BrowserController(base_url, self.browser_config)
        self.log_collector = LogCollector(log_config)
        self.correlator = EventCorrelator()
        self.auth_handler = AuthHandler(auth_config) if auth_config else None
        self.css_iterator = CSSIterator()
        self.cursor_integration = CursorIntegration()
        self.mockup_comparator = MockupComparator()
        
        # Initialize output manager and data presenter
        self.output_manager = OutputManager()
        self.data_presenter = DataPresenter()
        
        # Session tracking
        self.session_id = None
        self.timeline = []
        self.artifacts = {"screenshots": [], "console_logs": [], "server_logs": []}
        
        # Persistent session support for hot reload
        self.persistent_session: Optional[PersistentSession] = None
        self.session_manager = get_session_manager()
        
        self.logger = logging.getLogger(__name__)
        
        # Check for updates on initialization (background task)
        self._check_for_updates_async()
        
    async def execute_and_collect(
        self, 
        actions: List[Dict], 
        session_options: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Execute UI actions and collect all correlated data
        
        Args:
            actions: [
                {"navigate": "/dashboard"},
                {"click": "#refresh-button"},
                {"screenshot": "after-click"}
            ]
            session_options: {
                "reuse_session": True,
                "save_session": True, 
                "fresh_session": False
            }
            
        Returns:
            {
                "success": bool,
                "session_id": str,
                "timeline": [{"time": timestamp, "type": "browser|server", "event": "...", ...}],
                "correlations": [{"browser_event": "...", "server_event": "...", "confidence": 0.95}],
                "artifacts": {
                    "screenshots": ["before.png", "after.png"],
                    "console_logs": [...],
                    "server_logs": [...]
                }
            }
        """
        session_options = session_options or {}
        start_time = time.time()
        
        try:
            # Initialize session
            await self._initialize_session(session_options)
            
            # Start monitoring
            await self.log_collector.start_monitoring()
            
            # Execute actions
            success = await self._execute_actions(actions)
            
            # Stop monitoring and collect data
            server_logs = await self.log_collector.stop_monitoring()
            
            # Organize timeline (NO analysis - just data organization)
            organized_timeline = self.correlator.organize_timeline(
                self.timeline, server_logs
            )
            summary = self.correlator.get_summary(organized_timeline)
            
            # Capture comprehensive data if screenshots were taken
            comprehensive_data = {}
            if self.artifacts.get("screenshots"):
                # Get comprehensive data from last screenshot
                last_screenshot = self.artifacts["screenshots"][-1]
                if "comprehensive_data_path" in last_screenshot:
                    import json
                    try:
                        with open(last_screenshot["comprehensive_data_path"], 'r') as f:
                            comprehensive_data = json.load(f)
                    except Exception as e:
                        self.logger.warning(f"Could not load comprehensive data: {e}")
            
            # Package results
            results = {
                "success": success,
                "session_id": self.session_id,
                "execution_time": time.time() - start_time,
                "timeline": organized_timeline,  # Organized chronological data
                "browser_events": self.timeline,  # Raw browser events
                "server_logs": server_logs,       # Raw server logs
                "summary": summary,               # Basic counts
                "artifacts": self.artifacts,
                "comprehensive_data": comprehensive_data,  # Complete page intelligence
                "test_description": session_options.get('test_description', 'test') if session_options else 'test'
            }
            
            self.logger.info(f"Test execution completed: {success}, timeline events: {len(organized_timeline)}")
            return results
            
        except Exception as e:
            self.logger.error(f"Test execution failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "timeline": self.timeline,
                "artifacts": self.artifacts
            }
        finally:
            await self._cleanup_session(session_options)
    
    async def css_iteration_session(
        self, 
        base_actions: List[Dict], 
        css_changes: List[Dict],
        viewport_configs: Optional[List[Dict]] = None
    ) -> Dict[str, Any]:
        """
        Rapid CSS iteration with visual feedback
        
        Args:
            base_actions: [
                {"navigate": "/page"},
                {"wait_for": "#main-content"},
                {"screenshot": "baseline"}
            ]
            css_changes: [
                {
                    "name": "flex-spacing-fix",
                    "css": ".container { display: flex; gap: 1rem; }",
                    "rationale": "Fix spacing between items"
                }
            ]
            viewport_configs: [
                {"width": 1440, "height": 900, "name": "desktop"},
                {"width": 768, "height": 1024, "name": "tablet"}
            ]
            
        Returns:
            {
                "baseline": {
                    "screenshot": "baseline.png",
                    "computed_styles": {...},
                    "layout_metrics": {...}
                },
                "iterations": [
                    {
                        "name": "flex-spacing-fix",
                        "screenshot": "iteration_1.png",
                        "diff_image": "diff_1.png", 
                        "layout_changes": [...],
                        "console_errors": [...],
                        "performance_impact": {...}
                    }
                ]
            }
        """
        try:
            # Initialize for CSS iteration
            await self.browser.initialize()
            
            # Execute base actions and capture baseline
            await self._execute_actions(base_actions)
            baseline = await self.css_iterator.capture_baseline(self.browser.page)
            
            # Iterate through CSS changes
            iterations = []
            for i, css_change in enumerate(css_changes):
                iteration_result = await self.css_iterator.apply_css_and_capture(
                    self.browser.page, css_change, baseline
                )
                iterations.append(iteration_result)
                
            # Test across viewports if specified
            if viewport_configs:
                for viewport in viewport_configs:
                    await self.browser.set_viewport(viewport["width"], viewport["height"])
                    viewport_baseline = await self.css_iterator.capture_baseline(self.browser.page)
                    
                    for css_change in css_changes:
                        viewport_iteration = await self.css_iterator.apply_css_and_capture(
                            self.browser.page, css_change, viewport_baseline, 
                            suffix=f"_{viewport['name']}"
                        )
                        iterations.append(viewport_iteration)
            
            # Create raw results
            raw_results = {
                "baseline": baseline,
                "iterations": iterations,
                "summary": {
                    "total_changes": len(css_changes),
                    "viewports_tested": len(viewport_configs) if viewport_configs else 1,
                    "recommended_iteration": self._recommend_best_iteration(iterations)
                }
            }
            
            # Format for Cursor with session management and actionable insights
            cursor_results = self.cursor_integration.format_css_iteration_results(
                raw_results=raw_results,
                session_id=self.session_id,
                project_context={
                    "framework": "auto-detected",  # Could be enhanced with real detection
                    "base_url": self.base_url,
                    "test_type": "css_iteration"
                }
            )
            
            return cursor_results
            
        except Exception as e:
            self.logger.error(f"CSS iteration failed: {e}")
            return {"success": False, "error": str(e)}
        finally:
            await self.browser.cleanup()
    
    async def css_iteration_persistent(
        self,
        base_actions: List[Dict],
        css_changes: List[Dict],
        session_options: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        CSS iteration using persistent sessions for hot reload environments
        
        Maintains browser state between iterations, taking advantage of hot reload
        capabilities for faster CSS iteration cycles.
        
        Args:
            base_actions: Initial actions to set up the page
            css_changes: List of CSS changes to test
            session_options: {
                "session_id": "optional-custom-id",
                "reuse_session": True,
                "hot_reload": True,
                "keep_session_alive": True
            }
            
        Returns:
            Enhanced results with session information and hot reload data
        """
        session_options = session_options or {}
        start_time = time.time()
        
        try:
            # Get or create persistent session
            session_id = session_options.get("session_id", f"css_session_{int(time.time())}")
            self.persistent_session = await self.session_manager.get_or_create_session(
                session_id=session_id,
                base_url=self.base_url,
                config={
                    **self.browser_config,
                    "hot_reload_enabled": session_options.get("hot_reload", True),
                    "keep_alive": session_options.get("keep_session_alive", True)
                }
            )
            
            # Initialize persistent session
            session_initialized = await self.persistent_session.initialize()
            if not session_initialized:
                return {"success": False, "error": "Failed to initialize persistent session"}
            
            # Execute base actions if this is a new session or explicitly requested
            if (not session_options.get("reuse_session", True) or 
                not self.persistent_session.baseline_captured):
                
                self.logger.info("Executing base actions for CSS iteration setup")
                await self._execute_persistent_actions(base_actions)
                self.persistent_session.baseline_captured = True
            
            # Capture baseline state
            baseline = await self._capture_persistent_baseline()
            
            # Perform CSS iterations with persistent session
            iterations = []
            
            for i, css_change in enumerate(css_changes):
                self.logger.info(f"Applying CSS iteration {i+1}/{len(css_changes)}: {css_change.get('name', 'unnamed')}")
                
                # Apply CSS using persistent session (with hot reload when available)
                iteration_result = await self.persistent_session.apply_css_persistent(
                    css=css_change.get("css", ""),
                    name=css_change.get("name", f"iteration_{i+1}"),
                    replace_previous=css_change.get("replace_previous", False)
                )
                
                # Enhance with CursorFlow iteration data
                if iteration_result.get("success"):
                    enhanced_result = await self._enhance_iteration_result(
                        iteration_result, css_change, baseline
                    )
                    iterations.append(enhanced_result)
                else:
                    iterations.append(iteration_result)
                
                # Small delay to let changes settle
                await asyncio.sleep(0.1)
            
            # Get session information
            session_info = await self.persistent_session.get_session_info()
            
            # Create results
            results = {
                "success": True,
                "session_id": session_id,
                "execution_time": time.time() - start_time,
                "baseline": baseline,
                "iterations": iterations,
                "session_info": session_info,
                "hot_reload_used": session_info.get("hot_reload_available", False),
                "total_iterations": len(iterations),
                "summary": {
                    "successful_iterations": len([i for i in iterations if i.get("success", False)]),
                    "failed_iterations": len([i for i in iterations if not i.get("success", True)]),
                    "hot_reload_available": session_info.get("hot_reload_available", False),
                    "session_reused": session_options.get("reuse_session", True),
                    "recommended_iteration": self._recommend_best_iteration(iterations)
                }
            }
            
            # Format for Cursor integration
            cursor_results = self.cursor_integration.format_persistent_css_results(
                results, 
                {"framework": "auto-detected", "hot_reload": True}
            )
            
            # Keep session alive if requested
            if not session_options.get("keep_session_alive", True):
                await self.persistent_session.cleanup(save_state=True)
                self.persistent_session = None
            
            return cursor_results
            
        except Exception as e:
            self.logger.error(f"Persistent CSS iteration failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "session_id": session_id if 'session_id' in locals() else None
            }
    
    async def _execute_persistent_actions(self, actions: List[Dict]) -> bool:
        """Execute actions using persistent session"""
        try:
            for action in actions:
                if "navigate" in action:
                    path = action["navigate"]
                    if isinstance(path, dict):
                        path = path["url"]
                    await self.persistent_session.navigate_persistent(path)
                    
                elif "wait_for" in action:
                    selector = action["wait_for"]
                    if isinstance(selector, dict):
                        selector = selector["selector"]
                    await self.persistent_session.browser.wait_for_element(selector)
                    
                elif "screenshot" in action:
                    name = action["screenshot"]
                    await self.persistent_session.browser.screenshot(name)
                    
                # Add other actions as needed
            return True
            
        except Exception as e:
            self.logger.error(f"Persistent action execution failed: {e}")
            return False
    
    async def _capture_persistent_baseline(self) -> Dict[str, Any]:
        """Capture baseline using persistent session"""
        if not self.persistent_session or not self.persistent_session.browser:
            return {}
        
        try:
            # Use CSS iterator for baseline capture
            baseline = await self.css_iterator.capture_baseline(self.persistent_session.browser.page)
            
            # Enhance with persistent session data
            session_state = await self.persistent_session._capture_session_state("baseline")
            baseline.update({
                "session_state": session_state,
                "hot_reload_detected": await self.persistent_session._check_hot_reload_capability(),
                "iteration_context": {
                    "session_id": self.persistent_session.session_id,
                    "previous_iterations": self.persistent_session.iteration_count
                }
            })
            
            return baseline
            
        except Exception as e:
            self.logger.error(f"Persistent baseline capture failed: {e}")
            return {"error": str(e)}
    
    async def _enhance_iteration_result(
        self, 
        iteration_result: Dict, 
        css_change: Dict, 
        baseline: Dict
    ) -> Dict[str, Any]:
        """Enhance iteration result with CursorFlow analysis data"""
        try:
            enhanced = iteration_result.copy()
            
            # Add CSS iterator analysis
            if self.persistent_session and self.persistent_session.browser:
                css_analysis = await self.css_iterator.apply_css_and_capture(
                    page=self.persistent_session.browser.page,
                    css_change=css_change,
                    baseline=baseline,
                    suffix="_persistent"
                )
                
                # Merge analysis data
                enhanced.update({
                    "css_analysis": css_analysis,
                    "visual_comparison": css_analysis.get("changes", {}),
                    "performance_impact": css_analysis.get("performance_metrics", {}),
                    "console_errors": css_analysis.get("console_errors", [])
                })
            
            # Add persistent session context
            enhanced.update({
                "iteration_method": iteration_result.get("method", "standard"),
                "hot_reload_used": iteration_result.get("method") == "hot_reload",
                "session_persistent": True
            })
            
            return enhanced
            
        except Exception as e:
            self.logger.error(f"Failed to enhance iteration result: {e}")
            return iteration_result
    
    async def get_persistent_session_info(self) -> Optional[Dict[str, Any]]:
        """Get information about current persistent session"""
        if self.persistent_session:
            return await self.persistent_session.get_session_info()
        return None
    
    async def cleanup_persistent_session(self, save_state: bool = True):
        """Clean up current persistent session"""
        if self.persistent_session:
            await self.persistent_session.cleanup(save_state=save_state)
            self.persistent_session = None
    
    async def compare_mockup_to_implementation(
        self,
        mockup_url: str,
        mockup_actions: Optional[List[Dict]] = None,
        implementation_actions: Optional[List[Dict]] = None,
        comparison_config: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Compare mockup design to current implementation
        
        Args:
            mockup_url: URL of the design mockup/reference
            mockup_actions: Optional actions to perform on mockup (clicks, scrolls, etc.)
            implementation_actions: Optional actions to perform on implementation
            comparison_config: {
                "viewports": [{"width": 1440, "height": 900, "name": "desktop"}],
                "diff_threshold": 0.1,
                "ignore_regions": [{"x": 0, "y": 0, "width": 100, "height": 50}]
            }
            
        Returns:
            {
                "comparison_id": "mockup_comparison_123456",
                "mockup_url": "https://mockup.example.com",
                "implementation_url": "http://localhost:3000",
                "results": [
                    {
                        "viewport": {"width": 1440, "height": 900, "name": "desktop"},
                        "visual_diff": {
                            "similarity_score": 85.2,
                            "diff_image": "path/to/diff.png",
                            "major_differences": [...]
                        },
                        "layout_analysis": {...},
                        "element_analysis": {...}
                    }
                ],
                "summary": {
                    "average_similarity": 85.2,
                    "needs_improvement": false
                },
                "recommendations": [...]
            }
        """
        try:
            # Execute raw comparison
            raw_results = await self.mockup_comparator.compare_mockup_to_implementation(
                mockup_url=mockup_url,
                implementation_url=self.base_url,
                mockup_actions=mockup_actions,
                implementation_actions=implementation_actions,
                comparison_config=comparison_config
            )
            
            if "error" in raw_results:
                return raw_results
            
            # Return raw measurement data directly (pure observation)
            # No interpretation, no analysis - Cursor makes decisions based on data
            return raw_results
            
        except Exception as e:
            self.logger.error(f"Mockup comparison failed: {e}")
            return {"error": str(e)}
    
    async def iterative_mockup_matching(
        self,
        mockup_url: str,
        css_improvements: List[Dict],
        base_actions: Optional[List[Dict]] = None,
        comparison_config: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Iteratively improve implementation to match mockup design
        
        Args:
            mockup_url: Reference mockup URL
            css_improvements: [
                {
                    "name": "fix-header-spacing",
                    "css": ".header { padding: 2rem 0; }",
                    "rationale": "Match mockup header spacing"
                }
            ]
            base_actions: Actions to perform before each comparison
            comparison_config: Configuration for comparison sensitivity
            
        Returns:
            {
                "session_id": "ui_matching_123456",
                "baseline_comparison": {...},
                "iterations": [
                    {
                        "iteration_number": 1,
                        "css_change": {...},
                        "mockup_comparison": {...},
                        "improvement_metrics": {
                            "baseline_similarity": 75.0,
                            "improved_similarity": 82.5,
                            "improvement": 7.5,
                            "is_improvement": true
                        }
                    }
                ],
                "best_iteration": {...},
                "final_recommendations": [...]
            }
        """
        try:
            # Execute raw iterative matching
            raw_results = await self.mockup_comparator.iterative_ui_matching(
                mockup_url=mockup_url,
                implementation_url=self.base_url,
                css_improvements=css_improvements,
                base_actions=base_actions,
                comparison_config=comparison_config
            )
            
            if "error" in raw_results:
                return raw_results
            
            # Format results for Cursor analysis
            session_id = f"iterative_mockup_{int(time.time())}"
            cursor_results = self.cursor_integration.format_iterative_mockup_results(
                raw_results=raw_results,
                session_id=session_id,
                project_context={
                    "framework": "auto-detected",
                    "base_url": self.base_url,
                    "test_type": "iterative_mockup_matching"
                }
            )
            
            return cursor_results
            
        except Exception as e:
            self.logger.error(f"Iterative mockup matching failed: {e}")
            return {"error": str(e)}
    
    async def _initialize_session(self, session_options: Dict):
        """Initialize browser and authentication session"""
        self.session_id = f"session_{int(time.time())}"
        
        # Initialize browser
        await self.browser.initialize()
        
        # Handle authentication with proper session option mapping
        if self.auth_handler and not session_options.get("skip_auth", False):
            # Map CLI options to AuthHandler expectations
            mapped_options = self._map_session_options(session_options)
            await self.auth_handler.authenticate(
                self.browser.page, 
                mapped_options
            )
    
    def _map_session_options(self, session_options: Dict) -> Dict:
        """
        Map CLI session options to AuthHandler expectations
        
        CLI uses: --use-session "name" → use_session: "name"
        CLI uses: --save-session "name" → save_session: "name"
        
        AuthHandler expects: reuse_session: True, session_name: "name"
        AuthHandler expects: save_session: True, session_name: "name"
        """
        mapped = session_options.copy()
        
        # Map --use-session to reuse_session + session_name
        if "use_session" in session_options:
            mapped["reuse_session"] = True
            mapped["session_name"] = session_options["use_session"]
            # Remove the original key
            del mapped["use_session"]
        
        # Map --save-session to save_session + session_name
        if "save_session" in session_options:
            # save_session value is the session name
            session_name = session_options["save_session"]
            mapped["save_session"] = True
            mapped["session_name"] = session_name
        
        # Add debug flag if present
        if session_options.get("debug_session"):
            mapped["debug"] = True
        
        return mapped
    
    async def _execute_actions(self, actions: List[Dict]) -> bool:
        """Execute list of declarative actions"""
        # Validate all actions before execution
        from .action_validator import ActionValidator, ActionValidationError
        
        try:
            actions = ActionValidator.validate_list(actions)
        except ActionValidationError as e:
            self.logger.error(f"Action validation failed: {e}")
            return False
        
        try:
            for action in actions:
                await self._execute_single_action(action)
            return True
        except Exception as e:
            self.logger.error(f"Action execution failed: {e}")
            return False
    
    async def _execute_single_action(self, action: Dict):
        """
        Execute a single declarative action and track it
        
        Pass-through architecture: CursorFlow handles a few special actions,
        then passes everything else directly to Playwright Page API.
        """
        action_start = time.time()
        
        try:
            # Extract action type
            action_type = action.get('type') or list(action.keys())[0]
            
            # CursorFlow-specific actions (not direct Playwright methods)
            if action_type == "navigate":
                url = action["navigate"]
                if isinstance(url, dict):
                    url = url["url"]
                await self.browser.navigate(url)
                
            elif action_type == "screenshot":
                screenshot_config = action["screenshot"]
                
                # Handle both string and dict formats
                if isinstance(screenshot_config, str):
                    # Simple format: {"screenshot": "name"}
                    name = screenshot_config
                    options = None
                elif isinstance(screenshot_config, dict):
                    # Enhanced format: {"screenshot": {"name": "test", "options": {...}}}
                    name = screenshot_config.get("name", "screenshot")
                    options = screenshot_config.get("options")
                else:
                    name = "screenshot"
                    options = None
                
                # v2.1: No need for additional_selectors - we capture ALL visible elements now
                screenshot_data = await self.browser.screenshot(name, options)
                self.artifacts["screenshots"].append(screenshot_data)
                
            elif action_type == "authenticate":
                if self.auth_handler:
                    await self.auth_handler.authenticate(self.browser.page, action["authenticate"])
            
            # Pass-through to Playwright Page API (hover, dblclick, press, etc.)
            else:
                await self._execute_playwright_action(action_type, action)
                    
            # Record action in timeline
            self.timeline.append({
                "timestamp": action_start,
                "type": "browser",
                "event": action_type,
                "data": action,
                "duration": time.time() - action_start
            })
            
        except Exception as e:
            self.logger.error(f"Action failed: {action}, error: {e}")
            raise
    
    async def _execute_playwright_action(self, action_type: str, action: Dict):
        """
        Pass-through to Playwright Page API
        
        Enables using any Playwright method without hardcoding them:
        - hover, dblclick, drag_and_drop
        - press, focus, blur, check, uncheck
        - evaluate, route, expose_function
        - And 90+ more methods
        
        See: https://playwright.dev/python/docs/api/class-page
        """
        # Get the action config
        action_config = action.get(action_type)
        
        # Check if method exists on Playwright Page
        if hasattr(self.browser.page, action_type):
            method = getattr(self.browser.page, action_type)
            
            # Call with appropriate args based on config format
            if isinstance(action_config, str):
                # Simple format: {"hover": ".selector"}
                await method(action_config)
            elif isinstance(action_config, dict):
                # Config format: {"hover": {"selector": ".item", "timeout": 5000}}
                await method(**action_config)
            elif action_config is None:
                # No args: {"reload": null}
                await method()
            else:
                # Numeric or other: {"wait": 2}
                await method(action_config)
        else:
            # Method doesn't exist on Page - provide helpful error
            available_methods = [m for m in dir(self.browser.page) if not m.startswith('_') and callable(getattr(self.browser.page, m))]
            raise AttributeError(
                f"Unknown Playwright action: '{action_type}'\n"
                f"Available methods: {', '.join(sorted(available_methods[:20]))}...\n"
                f"Full API: https://playwright.dev/python/docs/api/class-page"
            )
    
    async def _cleanup_session(self, session_options: Dict):
        """Clean up browser session"""
        try:
            # Save session if requested
            if session_options.get("save_session", False) and self.auth_handler:
                await self.auth_handler.save_session(self.browser.page, self.session_id)
                
            # Cleanup browser
            await self.browser.cleanup()
            
        except Exception as e:
            self.logger.error(f"Session cleanup failed: {e}")
    
    async def test_responsive(self, viewports: List[Dict], actions: List[Dict], session_options: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Test the same actions across multiple viewports in parallel
        
        Args:
            viewports: List of viewport configurations [{"width": 375, "height": 667, "name": "mobile"}, ...]
            actions: Actions to execute on each viewport
            session_options: Optional session configuration
            
        Returns:
            Dict with results for each viewport plus comparison analysis
        """
        session_options = session_options or {}
        responsive_session_id = session_options.get("session_id", f"responsive_{int(time.time())}")
        
        self.logger.info(f"Starting responsive testing across {len(viewports)} viewports")
        
        try:
            # Execute tests in parallel across all viewports
            viewport_tasks = []
            for viewport in viewports:
                task = self._test_single_viewport(viewport, actions, responsive_session_id)
                viewport_tasks.append(task)
            
            # Wait for all viewport tests to complete
            viewport_results = await asyncio.gather(*viewport_tasks, return_exceptions=True)
            
            # Process results and handle any exceptions
            processed_results = {}
            successful_viewports = []
            failed_viewports = []
            
            for i, result in enumerate(viewport_results):
                viewport_name = viewports[i]["name"]
                if isinstance(result, Exception):
                    self.logger.error(f"Viewport {viewport_name} failed: {result}")
                    failed_viewports.append({"name": viewport_name, "error": str(result)})
                else:
                    processed_results[viewport_name] = result
                    successful_viewports.append(viewport_name)
            
            # Create responsive analysis
            responsive_analysis = self._analyze_responsive_results(processed_results, viewports)
            
            return {
                "session_id": responsive_session_id,
                "timestamp": time.time(),
                "viewport_results": processed_results,
                "responsive_analysis": responsive_analysis,
                "execution_summary": {
                    "total_viewports": len(viewports),
                    "successful_viewports": len(successful_viewports),
                    "failed_viewports": len(failed_viewports),
                    "success_rate": len(successful_viewports) / len(viewports),
                    "execution_time": responsive_analysis.get("total_execution_time", 0)
                },
                "failed_viewports": failed_viewports if failed_viewports else None,
                "artifacts": {
                    "screenshots": self._collect_responsive_screenshots(processed_results),
                    "comprehensive_data": self._collect_responsive_data(processed_results)
                }
            }
            
        except Exception as e:
            self.logger.error(f"Responsive testing failed: {e}")
            return {
                "session_id": responsive_session_id,
                "error": str(e),
                "timestamp": time.time()
            }
    
    async def _test_single_viewport(self, viewport: Dict, actions: List[Dict], session_id: str) -> Dict[str, Any]:
        """Execute test actions for a single viewport"""
        viewport_name = viewport["name"]
        viewport_width = viewport["width"]
        viewport_height = viewport["height"]
        
        # Create a separate browser instance for this viewport
        viewport_browser = BrowserController(
            base_url=self.base_url,
            config={
                **self.browser_config,
                "viewport": {"width": viewport_width, "height": viewport_height}
            }
        )
        
        try:
            # Initialize browser with specific viewport
            await viewport_browser.initialize()
            
            # Set the session ID for artifact organization
            viewport_browser.session_id = f"{session_id}_{viewport_name}"
            
            # Execute all actions for this viewport
            viewport_artifacts = {"screenshots": [], "comprehensive_data": []}
            viewport_timeline = []
            
            for action in actions:
                action_start = time.time()
                
                # Use the same action handling as execute_and_collect for consistency
                if "navigate" in action:
                    await viewport_browser.navigate(action["navigate"])
                elif "click" in action:
                    selector = action["click"]
                    if isinstance(selector, dict):
                        selector = selector["selector"]
                    await viewport_browser.click(selector)
                elif "fill" in action:
                    fill_config = action["fill"]
                    await viewport_browser.fill(fill_config["selector"], fill_config["value"])
                elif "wait_for" in action:
                    selector = action["wait_for"]
                    if isinstance(selector, dict):
                        selector = selector["selector"]
                    await viewport_browser.wait_for_element(selector)
                elif "wait" in action:
                    wait_time = action["wait"] * 1000  # Convert to milliseconds
                    await viewport_browser.page.wait_for_timeout(wait_time)
                elif "screenshot" in action:
                    screenshot_config = action["screenshot"]
                    
                    # Handle both string and dict formats
                    if isinstance(screenshot_config, str):
                        name = f"{viewport_name}_{screenshot_config}"
                        options = None
                    elif isinstance(screenshot_config, dict):
                        name = f"{viewport_name}_{screenshot_config.get('name', 'screenshot')}"
                        options = screenshot_config.get("options")
                    else:
                        name = f"{viewport_name}_screenshot"
                        options = None
                    
                    screenshot_data = await viewport_browser.screenshot(name, options)
                    viewport_artifacts["screenshots"].append(screenshot_data)
                elif "authenticate" in action:
                    # Note: Auth handler would need to be passed to viewport browser
                    # For now, log that auth is not supported in responsive mode
                    self.logger.warning(f"Authentication action skipped in responsive mode for viewport {viewport_name}")
                else:
                    # Log unsupported actions
                    action_type = list(action.keys())[0] if action else "unknown"
                    self.logger.warning(f"Unsupported action '{action_type}' in responsive mode for viewport {viewport_name}")
                
                # Record action in timeline
                viewport_timeline.append({
                    "timestamp": action_start,
                    "type": "browser",
                    "event": list(action.keys())[0],
                    "data": action,
                    "duration": time.time() - action_start,
                    "viewport": viewport_name
                })
            
            return {
                "viewport": viewport,
                "artifacts": viewport_artifacts,
                "timeline": viewport_timeline,
                "success": True,
                "execution_time": sum(event["duration"] for event in viewport_timeline)
            }
            
        except Exception as e:
            self.logger.error(f"Viewport {viewport_name} test failed: {e}")
            return {
                "viewport": viewport,
                "error": str(e),
                "success": False
            }
        finally:
            await viewport_browser.cleanup()
    
    def _analyze_responsive_results(self, results: Dict, viewports: List[Dict]) -> Dict[str, Any]:
        """Analyze responsive testing results for patterns and insights"""
        if not results:
            return {"error": "No successful viewport results to analyze"}
        
        analysis = {
            "viewport_comparison": {},
            "responsive_insights": [],
            "performance_analysis": {},
            "total_execution_time": 0
        }
        
        # Compare viewports
        viewport_names = list(results.keys())
        for viewport_name in viewport_names:
            result = results[viewport_name]
            viewport_config = next(v for v in viewports if v["name"] == viewport_name)
            
            analysis["viewport_comparison"][viewport_name] = {
                "dimensions": f"{viewport_config['width']}x{viewport_config['height']}",
                "screenshot_count": len(result.get("artifacts", {}).get("screenshots", [])),
                "execution_time": result.get("execution_time", 0),
                "actions_completed": len(result.get("timeline", [])),
                "success": result.get("success", False)
            }
            
            analysis["total_execution_time"] += result.get("execution_time", 0)
        
        # Generate responsive insights
        if len(viewport_names) >= 2:
            analysis["responsive_insights"].extend([
                f"Tested across {len(viewport_names)} viewports: {', '.join(viewport_names)}",
                f"Total execution time: {analysis['total_execution_time']:.2f}s",
                f"Average time per viewport: {analysis['total_execution_time'] / len(viewport_names):.2f}s"
            ])
            
            # Performance comparison
            execution_times = [results[vp].get("execution_time", 0) for vp in viewport_names]
            fastest_vp = viewport_names[execution_times.index(min(execution_times))]
            slowest_vp = viewport_names[execution_times.index(max(execution_times))]
            
            analysis["performance_analysis"] = {
                "fastest_viewport": fastest_vp,
                "slowest_viewport": slowest_vp,
                "time_difference": max(execution_times) - min(execution_times),
                "performance_variance": "low" if max(execution_times) - min(execution_times) < 2 else "high"
            }
        
        return analysis
    
    def _collect_responsive_screenshots(self, results: Dict) -> List[Dict]:
        """Collect all screenshots from responsive testing"""
        all_screenshots = []
        for viewport_name, result in results.items():
            if result.get("success") and "artifacts" in result:
                for screenshot in result["artifacts"].get("screenshots", []):
                    screenshot["viewport"] = viewport_name
                    all_screenshots.append(screenshot)
        return all_screenshots
    
    def _collect_responsive_data(self, results: Dict) -> List[Dict]:
        """Collect all comprehensive data from responsive testing"""
        all_data = []
        for viewport_name, result in results.items():
            if result.get("success") and "artifacts" in result:
                for data in result["artifacts"].get("comprehensive_data", []):
                    data["viewport"] = viewport_name
                    all_data.append(data)
        return all_data
    
    def _recommend_best_iteration(self, iterations: List[Dict]) -> Optional[str]:
        best_iteration = None
        best_score = -1
        
        for iteration in iterations:
            score = 0
            
            # Penalty for console errors
            if not iteration.get("console_errors", []):
                score += 50
                
            # Bonus for good performance
            perf = iteration.get("performance_impact", {})
            if perf.get("render_time", 1000) < 100:
                score += 30
                
            if score > best_score:
                best_score = score
                best_iteration = iteration.get("name")
                
        return best_iteration
    
    def _check_for_updates_async(self):
        """Check for updates in background (non-blocking)"""
        try:
            import asyncio
            from ..auto_updater import check_for_updates_on_startup
            
            # Try to run update check in background
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # Schedule as background task
                    loop.create_task(check_for_updates_on_startup(str(Path.cwd())))
                else:
                    # Create new loop for quick check
                    asyncio.run(check_for_updates_on_startup(str(Path.cwd())))
            except Exception:
                # If async fails, skip silently - updates not critical for operation
                pass
        except ImportError:
            # Auto-updater not available, skip silently
            pass
