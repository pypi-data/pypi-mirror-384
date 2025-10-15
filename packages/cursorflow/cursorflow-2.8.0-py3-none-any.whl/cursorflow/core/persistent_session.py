"""
Persistent Browser Session Manager

Maintains browser sessions across CSS iterations to take advantage of hot reload
environments. Allows rapid CSS iteration without page reloads.
"""

import asyncio
import json
import time
import weakref
from typing import Dict, List, Optional, Any, Set
from pathlib import Path
import logging

from .browser_controller import BrowserController
from .file_change_monitor import get_file_monitor, get_hot_reload_synchronizer


class PersistentSession:
    """
    Manages persistent browser sessions for hot reload environments
    
    Keeps browser instances alive between CursorFlow operations to take advantage
    of hot reload, live CSS updates, and maintain application state.
    """
    
    def __init__(self, session_id: str, base_url: str, config: Dict):
        """
        Initialize persistent session
        
        Args:
            session_id: Unique identifier for this session
            base_url: Base URL for the application
            config: Browser configuration with persistent session options
        """
        self.session_id = session_id
        self.base_url = base_url
        self.config = config
        
        # Browser controller instance (persistent)
        self.browser: Optional[BrowserController] = None
        
        # Session state tracking
        self.is_active = False
        self.last_used = time.time()
        self.navigation_history: List[str] = []
        self.css_injections: List[str] = []
        
        # Hot reload detection
        self.hot_reload_urls: Set[str] = set()
        self.last_reload_time = 0
        
        # CSS iteration state
        self.baseline_captured = False
        self.iteration_count = 0
        self.applied_css_cache: List[Dict] = []
        
        self.logger = logging.getLogger(__name__)
        
        # Session artifacts directory
        self.session_dir = Path.cwd() / ".cursorflow" / "sessions" / session_id
        self.session_dir.mkdir(parents=True, exist_ok=True)
        
        # File monitoring integration
        self.file_monitor = get_file_monitor()
        self.hot_reload_sync = get_hot_reload_synchronizer()
        self.file_monitoring_active = False
        
    async def initialize(self) -> bool:
        """
        Initialize the persistent browser session
        
        Returns:
            True if initialization successful
        """
        try:
            if self.browser is None:
                # Create browser with persistent-friendly config
                persistent_config = self._get_persistent_browser_config()
                self.browser = BrowserController(self.base_url, persistent_config)
                await self.browser.initialize()
                
                # Setup hot reload detection
                await self._setup_hot_reload_detection()
                
                # Start file monitoring for hot reload synchronization
                await self._start_file_monitoring()
                
                self.is_active = True
                self.last_used = time.time()
                
                self.logger.info(f"Persistent session initialized: {self.session_id}")
                return True
            else:
                # Session already active
                self.last_used = time.time()
                return True
                
        except Exception as e:
            self.logger.error(f"Failed to initialize persistent session: {e}")
            return False
    
    def _get_persistent_browser_config(self) -> Dict:
        """Get browser configuration optimized for persistent sessions"""
        config = self.config.copy()
        
        # Optimize for persistence and hot reload
        config.update({
            "headless": config.get("headless", True),
            "debug_mode": config.get("debug_mode", False),
            "human_timeout": config.get("human_timeout", 30),
            
            # Hot reload optimizations
            "disable_cache": False,  # Keep cache for faster reloads
            "preserve_local_storage": True,
            "preserve_session_storage": True,
            
            # Performance optimizations for long sessions
            "disable_background_throttling": True,
            "keep_alive": True
        })
        
        return config
    
    async def _setup_hot_reload_detection(self):
        """Setup detection for hot reload events"""
        if not self.browser or not self.browser.page:
            return
            
        # Monitor for hot reload indicators
        await self.browser.page.add_init_script("""
            // Detect common hot reload frameworks
            window.__cursorflow_hot_reload_detected = false;
            
            // Webpack Hot Module Replacement
            if (window.module && window.module.hot) {
                window.__cursorflow_hot_reload_detected = true;
                window.__cursorflow_hot_reload_type = 'webpack-hmr';
            }
            
            // Vite HMR
            if (window.__vite_hot_update) {
                window.__cursorflow_hot_reload_detected = true;
                window.__cursorflow_hot_reload_type = 'vite-hmr';
            }
            
            // Live reload (general)
            if (window.location.protocol === 'ws:' || window.WebSocket) {
                const originalWebSocket = window.WebSocket;
                window.WebSocket = function(...args) {
                    const ws = new originalWebSocket(...args);
                    if (args[0] && args[0].includes('reload')) {
                        window.__cursorflow_hot_reload_detected = true;
                        window.__cursorflow_hot_reload_type = 'websocket-reload';
                    }
                    return ws;
                };
            }
            
            // CSS hot reload detection
            const originalCreateElement = document.createElement;
            document.createElement = function(tagName) {
                const el = originalCreateElement.call(this, tagName);
                if (tagName.toLowerCase() === 'style' || tagName.toLowerCase() === 'link') {
                    window.__cursorflow_css_hot_reload = true;
                }
                return el;
            };
        """)
        
        self.logger.debug("Hot reload detection setup complete")
    
    async def _start_file_monitoring(self):
        """Start file monitoring for hot reload synchronization"""
        try:
            # Start file monitoring if not already active
            if not self.file_monitor.is_monitoring:
                await self.file_monitor.start_monitoring(poll_interval=0.5)
            
            # Register this session with hot reload synchronizer
            self.hot_reload_sync.register_browser_session(self.session_id, self)
            
            # Add callback for file changes
            def on_file_change(change):
                self.logger.debug(f"File change detected: {change.file_path.name} ({change.change_type.value})")
            
            self.file_monitor.add_change_callback(on_file_change)
            self.file_monitoring_active = True
            
            self.logger.debug("File monitoring integration active")
            
        except Exception as e:
            self.logger.warning(f"Failed to start file monitoring: {e}")
            # Continue without file monitoring - not critical
    
    async def navigate_persistent(self, path: str, wait_for_load: bool = True) -> bool:
        """
        Navigate while maintaining session state
        
        Args:
            path: Path to navigate to
            wait_for_load: Whether to wait for page load completion
            
        Returns:
            True if navigation successful
        """
        try:
            if not self.browser:
                await self.initialize()
            
            # Detect if hot reload is available
            hot_reload_available = await self._check_hot_reload_capability()
            
            if hot_reload_available and path in self.navigation_history:
                # Use hot reload for faster navigation
                self.logger.info(f"Using hot reload navigation to: {path}")
                await self._hot_reload_navigate(path)
            else:
                # Standard navigation
                self.logger.info(f"Standard navigation to: {path}")
                await self.browser.navigate(path, wait_for_load)
                
            # Track navigation
            self.navigation_history.append(path)
            self.last_used = time.time()
            
            return True
            
        except Exception as e:
            self.logger.error(f"Persistent navigation failed: {e}")
            return False
    
    async def _check_hot_reload_capability(self) -> bool:
        """Check if hot reload is available and working"""
        if not self.browser or not self.browser.page:
            return False
            
        try:
            result = await self.browser.page.evaluate("""
                () => {
                    return {
                        detected: window.__cursorflow_hot_reload_detected || false,
                        type: window.__cursorflow_hot_reload_type || 'none',
                        css_reload: window.__cursorflow_css_hot_reload || false
                    };
                }
            """)
            
            if result.get("detected"):
                self.hot_reload_urls.add(self.browser.page.url)
                self.logger.debug(f"Hot reload detected: {result.get('type')}")
                return True
                
            return False
            
        except Exception as e:
            self.logger.debug(f"Hot reload check failed: {e}")
            return False
    
    async def _hot_reload_navigate(self, path: str):
        """Perform navigation using hot reload when possible"""
        try:
            # For hot reload environments, we can often just change the URL
            # without full page reload
            current_origin = await self.browser.page.evaluate("() => window.location.origin")
            target_url = f"{current_origin}/{path.lstrip('/')}"
            
            # Use history API for SPA navigation
            await self.browser.page.evaluate(f"""
                () => {{
                    if (window.history && window.history.pushState) {{
                        window.history.pushState(null, null, '{target_url}');
                        
                        // Trigger route change for SPA frameworks
                        const event = new PopStateEvent('popstate', {{
                            state: null
                        }});
                        window.dispatchEvent(event);
                        
                        // Trigger hashchange if needed
                        if (window.location.hash) {{
                            const hashEvent = new HashChangeEvent('hashchange');
                            window.dispatchEvent(hashEvent);
                        }}
                    }}
                }}
            """)
            
            # Wait for potential async route updates
            await asyncio.sleep(0.5)
            
        except Exception as e:
            self.logger.warning(f"Hot reload navigation failed, falling back to standard: {e}")
            await self.browser.navigate(path)
    
    async def apply_css_persistent(
        self, 
        css: str, 
        name: str = "", 
        replace_previous: bool = False
    ) -> Dict[str, Any]:
        """
        Apply CSS changes while maintaining session and taking advantage of hot reload
        
        Args:
            css: CSS code to apply
            name: Name for this CSS change
            replace_previous: Whether to replace all previous CSS injections
            
        Returns:
            Result data with before/after state
        """
        try:
            if not self.browser:
                await self.initialize()
            
            # Clear previous CSS if requested
            if replace_previous:
                await self._clear_injected_css()
                self.applied_css_cache.clear()
            
            # Capture before state
            before_state = await self._capture_session_state("before_css")
            
            # Check if hot CSS reload is available
            hot_css_reload = await self._check_css_hot_reload()
            
            if hot_css_reload:
                # Use hot CSS reload mechanism
                await self._apply_css_hot_reload(css, name)
            else:
                # Standard CSS injection
                await self.browser.inject_css(css)
            
            # Track applied CSS
            css_entry = {
                "name": name or f"css_{self.iteration_count}",
                "css": css,
                "timestamp": time.time(),
                "method": "hot_reload" if hot_css_reload else "injection"
            }
            self.applied_css_cache.append(css_entry)
            self.iteration_count += 1
            
            # Capture after state
            after_state = await self._capture_session_state("after_css")
            
            # Update session tracking
            self.last_used = time.time()
            
            return {
                "success": True,
                "css_applied": css,
                "method": css_entry["method"],
                "before_state": before_state,
                "after_state": after_state,
                "iteration_count": self.iteration_count
            }
            
        except Exception as e:
            self.logger.error(f"Persistent CSS application failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "css": css
            }
    
    async def _check_css_hot_reload(self) -> bool:
        """Check if CSS hot reload is available"""
        if not self.browser or not self.browser.page:
            return False
            
        try:
            result = await self.browser.page.evaluate("""
                () => {
                    // Check for style-loader (webpack)
                    if (window.__webpack_require__ && window.__webpack_require__.hmr) {
                        return true;
                    }
                    
                    // Check for Vite CSS HMR
                    if (window.__vite_hot_update) {
                        return true;
                    }
                    
                    // Check for live CSS reload WebSocket
                    const wsConnections = Array.from(document.querySelectorAll('script')).some(script => 
                        script.src && script.src.includes('livereload')
                    );
                    
                    return wsConnections || window.__cursorflow_css_hot_reload;
                }
            """)
            
            return bool(result)
            
        except Exception:
            return False
    
    async def _apply_css_hot_reload(self, css: str, name: str):
        """Apply CSS using hot reload mechanisms when available"""
        try:
            # Try to inject CSS in a way that triggers hot reload
            await self.browser.page.evaluate(f"""
                (css, name) => {{
                    // Create a style element with hot reload attributes
                    const style = document.createElement('style');
                    style.id = 'cursorflow-css-' + name;
                    style.setAttribute('data-hot-reload', 'true');
                    style.textContent = css;
                    
                    // Remove previous iteration if exists
                    const existing = document.getElementById(style.id);
                    if (existing) {{
                        existing.remove();
                    }}
                    
                    // Inject CSS
                    document.head.appendChild(style);
                    
                    // Trigger hot reload events if framework supports it
                    if (window.__webpack_require__ && window.__webpack_require__.hmr) {{
                        // Webpack HMR
                        const event = new CustomEvent('webpack-hot-update', {{
                            detail: {{ type: 'css', module: name }}
                        }});
                        window.dispatchEvent(event);
                    }}
                    
                    if (window.__vite_hot_update) {{
                        // Vite HMR
                        window.__vite_hot_update({{
                            type: 'style-update',
                            path: '/' + name + '.css'
                        }});
                    }}
                    
                    return true;
                }}
            """, css, name)
            
            # Give hot reload time to process
            await asyncio.sleep(0.1)
            
        except Exception as e:
            self.logger.warning(f"Hot CSS reload failed, using standard injection: {e}")
            await self.browser.inject_css(css)
    
    async def _clear_injected_css(self):
        """Clear all previously injected CSS"""
        if not self.browser or not self.browser.page:
            return
            
        try:
            await self.browser.page.evaluate("""
                () => {
                    // Remove all CursorFlow injected styles
                    const styles = document.querySelectorAll('style[id^="cursorflow-css-"]');
                    styles.forEach(style => style.remove());
                    
                    // Remove any other injected styles
                    const injectedStyles = document.querySelectorAll('style[data-hot-reload="true"]');
                    injectedStyles.forEach(style => style.remove());
                }
            """)
            
        except Exception as e:
            self.logger.warning(f"Failed to clear injected CSS: {e}")
    
    async def _capture_session_state(self, stage: str) -> Dict[str, Any]:
        """Capture current session state for comparison"""
        if not self.browser or not self.browser.page:
            return {}
            
        try:
            timestamp = int(time.time())
            
            # Screenshot
            screenshot_path = str(self.session_dir / f"{stage}_{timestamp}.png")
            await self.browser.page.screenshot(path=screenshot_path, full_page=False)
            
            # Basic page state
            state = {
                "timestamp": time.time(),
                "stage": stage,
                "url": self.browser.page.url,
                "screenshot": screenshot_path,
                "viewport": await self.browser.page.evaluate("() => ({width: window.innerWidth, height: window.innerHeight})"),
                "scroll": await self.browser.page.evaluate("() => ({x: window.pageXOffset, y: window.pageYOffset})")
            }
            
            return state
            
        except Exception as e:
            self.logger.error(f"Failed to capture session state: {e}")
            return {"error": str(e)}
    
    async def get_session_info(self) -> Dict[str, Any]:
        """Get current session information"""
        hot_reload_info = await self._check_hot_reload_capability() if self.browser else False
        
        return {
            "session_id": self.session_id,
            "is_active": self.is_active,
            "last_used": self.last_used,
            "age_seconds": time.time() - self.last_used if self.last_used else 0,
            "navigation_history": self.navigation_history[-10:],  # Last 10 navigations
            "applied_css_count": len(self.applied_css_cache),
            "iteration_count": self.iteration_count,
            "hot_reload_available": hot_reload_info,
            "hot_reload_urls": list(self.hot_reload_urls),
            "current_url": self.browser.page.url if self.browser and self.browser.page else None
        }
    
    async def save_session_state(self) -> str:
        """Save current session state to disk"""
        try:
            session_state = {
                "session_id": self.session_id,
                "base_url": self.base_url,
                "config": self.config,
                "navigation_history": self.navigation_history,
                "applied_css_cache": self.applied_css_cache,
                "iteration_count": self.iteration_count,
                "hot_reload_urls": list(self.hot_reload_urls),
                "saved_at": time.time()
            }
            
            state_file = self.session_dir / "session_state.json"
            with open(state_file, 'w') as f:
                json.dump(session_state, f, indent=2)
            
            self.logger.info(f"Session state saved: {state_file}")
            return str(state_file)
            
        except Exception as e:
            self.logger.error(f"Failed to save session state: {e}")
            return ""
    
    async def restore_session_state(self, state_file: str) -> bool:
        """Restore session state from disk"""
        try:
            with open(state_file, 'r') as f:
                session_state = json.load(f)
            
            self.navigation_history = session_state.get("navigation_history", [])
            self.applied_css_cache = session_state.get("applied_css_cache", [])
            self.iteration_count = session_state.get("iteration_count", 0)
            self.hot_reload_urls = set(session_state.get("hot_reload_urls", []))
            
            self.logger.info(f"Session state restored from: {state_file}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to restore session state: {e}")
            return False
    
    def is_session_stale(self, max_age_seconds: int = 3600) -> bool:
        """Check if session is stale and should be cleaned up"""
        if not self.last_used:
            return True
        return (time.time() - self.last_used) > max_age_seconds
    
    async def cleanup(self, save_state: bool = True):
        """Clean up session resources"""
        try:
            if save_state:
                await self.save_session_state()
            
            # Clean up file monitoring
            if self.file_monitoring_active:
                self.hot_reload_sync.unregister_browser_session(self.session_id)
                self.file_monitoring_active = False
            
            if self.browser:
                await self.browser.cleanup()
                self.browser = None
            
            self.is_active = False
            self.logger.info(f"Persistent session cleaned up: {self.session_id}")
            
        except Exception as e:
            self.logger.error(f"Session cleanup failed: {e}")


class SessionManager:
    """
    Manages multiple persistent browser sessions
    
    Allows CursorFlow to maintain multiple concurrent sessions and reuse them
    for different components or iteration cycles.
    """
    
    def __init__(self, max_sessions: int = 5, session_timeout: int = 3600):
        """
        Initialize session manager
        
        Args:
            max_sessions: Maximum number of concurrent sessions
            session_timeout: Session timeout in seconds
        """
        self.max_sessions = max_sessions
        self.session_timeout = session_timeout
        self.sessions: Dict[str, PersistentSession] = {}
        self.session_refs: Dict[str, weakref.ref] = {}
        
        self.logger = logging.getLogger(__name__)
        
        # Start cleanup task
        self._cleanup_task = None
        self._start_cleanup_task()
    
    def _start_cleanup_task(self):
        """Start background cleanup task"""
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                self._cleanup_task = loop.create_task(self._periodic_cleanup())
        except RuntimeError:
            # No event loop, cleanup will be manual
            pass
    
    async def _periodic_cleanup(self):
        """Periodic cleanup of stale sessions"""
        while True:
            try:
                await asyncio.sleep(300)  # Check every 5 minutes
                await self.cleanup_stale_sessions()
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Cleanup task error: {e}")
    
    async def get_or_create_session(
        self, 
        session_id: str, 
        base_url: str, 
        config: Dict
    ) -> PersistentSession:
        """
        Get existing session or create new one
        
        Args:
            session_id: Unique session identifier
            base_url: Base URL for the session
            config: Browser configuration
            
        Returns:
            PersistentSession instance
        """
        # Check if session already exists and is active
        if session_id in self.sessions:
            session = self.sessions[session_id]
            if session.is_active and not session.is_session_stale(self.session_timeout):
                session.last_used = time.time()
                return session
            else:
                # Clean up stale session
                await self.remove_session(session_id)
        
        # Create new session
        if len(self.sessions) >= self.max_sessions:
            await self._cleanup_oldest_session()
        
        session = PersistentSession(session_id, base_url, config)
        self.sessions[session_id] = session
        
        # Create weak reference for cleanup
        def cleanup_callback(ref):
            if session_id in self.sessions:
                del self.sessions[session_id]
            if session_id in self.session_refs:
                del self.session_refs[session_id]
        
        self.session_refs[session_id] = weakref.ref(session, cleanup_callback)
        
        self.logger.info(f"Created new persistent session: {session_id}")
        return session
    
    async def remove_session(self, session_id: str):
        """Remove and cleanup a specific session"""
        if session_id in self.sessions:
            session = self.sessions[session_id]
            await session.cleanup()
            del self.sessions[session_id]
            
        if session_id in self.session_refs:
            del self.session_refs[session_id]
        
        self.logger.info(f"Removed session: {session_id}")
    
    async def _cleanup_oldest_session(self):
        """Remove the oldest session to make room for new one"""
        if not self.sessions:
            return
        
        oldest_id = min(self.sessions.keys(), 
                       key=lambda sid: self.sessions[sid].last_used or 0)
        await self.remove_session(oldest_id)
    
    async def cleanup_stale_sessions(self):
        """Clean up all stale sessions"""
        stale_sessions = [
            sid for sid, session in self.sessions.items()
            if session.is_session_stale(self.session_timeout)
        ]
        
        for session_id in stale_sessions:
            await self.remove_session(session_id)
        
        if stale_sessions:
            self.logger.info(f"Cleaned up {len(stale_sessions)} stale sessions")
    
    async def smart_cleanup(self, force_cleanup: bool = False) -> Dict[str, Any]:
        """
        Intelligent session cleanup based on usage patterns and resource optimization
        
        Args:
            force_cleanup: Force cleanup even for active sessions
            
        Returns:
            Cleanup report with statistics and actions taken
        """
        cleanup_report = {
            "sessions_before": len(self.sessions),
            "sessions_cleaned": 0,
            "sessions_optimized": 0,
            "memory_freed": 0,
            "actions_taken": []
        }
        
        current_time = time.time()
        sessions_to_remove = []
        sessions_to_optimize = []
        
        for session_id, session in self.sessions.items():
            try:
                session_info = await session.get_session_info()
                age_seconds = session_info.get("age_seconds", 0)
                iteration_count = session_info.get("iteration_count", 0)
                hot_reload_available = session_info.get("hot_reload_available", False)
                
                # Cleanup criteria
                should_cleanup = False
                cleanup_reason = ""
                
                if force_cleanup:
                    should_cleanup = True
                    cleanup_reason = "forced_cleanup"
                elif age_seconds > 7200:  # 2 hours
                    should_cleanup = True
                    cleanup_reason = "session_too_old"
                elif iteration_count > 50 and not hot_reload_available:
                    should_cleanup = True
                    cleanup_reason = "too_many_iterations_without_hot_reload"
                elif not session.is_active:
                    should_cleanup = True
                    cleanup_reason = "session_inactive"
                elif session.is_session_stale(3600):  # 1 hour threshold
                    should_cleanup = True
                    cleanup_reason = "session_stale"
                
                if should_cleanup:
                    sessions_to_remove.append((session_id, cleanup_reason))
                elif age_seconds > 1800 and iteration_count > 10:  # 30 minutes, many iterations
                    # Session could benefit from optimization
                    sessions_to_optimize.append((session_id, "heavy_usage_optimization"))
                
            except Exception as e:
                self.logger.error(f"Error analyzing session {session_id}: {e}")
                sessions_to_remove.append((session_id, "analysis_error"))
        
        # Perform cleanup
        for session_id, reason in sessions_to_remove:
            try:
                await self.remove_session(session_id)
                cleanup_report["sessions_cleaned"] += 1
                cleanup_report["actions_taken"].append(f"Cleaned {session_id}: {reason}")
            except Exception as e:
                self.logger.error(f"Failed to cleanup session {session_id}: {e}")
        
        # Perform optimization
        for session_id, reason in sessions_to_optimize:
            try:
                await self._optimize_session(session_id)
                cleanup_report["sessions_optimized"] += 1
                cleanup_report["actions_taken"].append(f"Optimized {session_id}: {reason}")
            except Exception as e:
                self.logger.error(f"Failed to optimize session {session_id}: {e}")
        
        cleanup_report["sessions_after"] = len(self.sessions)
        cleanup_report["memory_freed"] = cleanup_report["sessions_cleaned"] * 50  # Estimated MB per session
        
        if cleanup_report["sessions_cleaned"] > 0 or cleanup_report["sessions_optimized"] > 0:
            self.logger.info(f"Smart cleanup completed: {cleanup_report}")
        
        return cleanup_report
    
    async def _optimize_session(self, session_id: str):
        """Optimize a session for better performance"""
        if session_id not in self.sessions:
            return
        
        session = self.sessions[session_id]
        
        try:
            # Clear injected CSS to reduce memory usage
            if session.browser and session.browser.page:
                await session._clear_injected_css()
            
            # Clear old applied CSS cache
            if len(session.applied_css_cache) > 20:
                session.applied_css_cache = session.applied_css_cache[-10:]  # Keep last 10
            
            # Save current state
            await session.save_session_state()
            
            self.logger.info(f"Optimized session: {session_id}")
            
        except Exception as e:
            self.logger.error(f"Session optimization failed for {session_id}: {e}")
    
    async def get_cleanup_recommendations(self) -> Dict[str, Any]:
        """Get recommendations for session cleanup without performing cleanup"""
        recommendations = {
            "immediate_cleanup": [],
            "optimization_candidates": [],
            "healthy_sessions": [],
            "total_sessions": len(self.sessions),
            "estimated_memory_usage": len(self.sessions) * 50  # MB estimate
        }
        
        for session_id, session in self.sessions.items():
            try:
                session_info = await session.get_session_info()
                age_seconds = session_info.get("age_seconds", 0)
                iteration_count = session_info.get("iteration_count", 0)
                hot_reload_available = session_info.get("hot_reload_available", False)
                
                session_summary = {
                    "session_id": session_id,
                    "age_hours": age_seconds / 3600,
                    "iteration_count": iteration_count,
                    "hot_reload": hot_reload_available,
                    "active": session.is_active
                }
                
                # Categorize sessions
                if age_seconds > 7200 or iteration_count > 50 or not session.is_active:
                    recommendations["immediate_cleanup"].append({
                        **session_summary,
                        "reason": "old_session" if age_seconds > 7200 else "inactive" if not session.is_active else "overused"
                    })
                elif age_seconds > 1800 and iteration_count > 10:
                    recommendations["optimization_candidates"].append({
                        **session_summary,
                        "reason": "heavy_usage"
                    })
                else:
                    recommendations["healthy_sessions"].append(session_summary)
                    
            except Exception as e:
                self.logger.error(f"Error analyzing session {session_id}: {e}")
        
        # Add summary statistics
        recommendations["cleanup_impact"] = {
            "sessions_to_cleanup": len(recommendations["immediate_cleanup"]),
            "sessions_to_optimize": len(recommendations["optimization_candidates"]),
            "memory_recoverable": len(recommendations["immediate_cleanup"]) * 50,  # MB estimate
            "performance_impact": "high" if len(recommendations["immediate_cleanup"]) > 2 else "low"
        }
        
        return recommendations
    
    async def get_session_info(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get information about a specific session"""
        if session_id in self.sessions:
            return await self.sessions[session_id].get_session_info()
        return None
    
    async def list_sessions(self) -> List[Dict[str, Any]]:
        """List all active sessions"""
        session_list = []
        for session_id, session in self.sessions.items():
            info = await session.get_session_info()
            session_list.append(info)
        return session_list
    
    async def cleanup_all_sessions(self):
        """Clean up all sessions"""
        session_ids = list(self.sessions.keys())
        for session_id in session_ids:
            await self.remove_session(session_id)
        
        if self._cleanup_task:
            self._cleanup_task.cancel()
        
        self.logger.info("All sessions cleaned up")


# Global session manager instance
_session_manager: Optional[SessionManager] = None

def get_session_manager() -> SessionManager:
    """Get or create global session manager"""
    global _session_manager
    if _session_manager is None:
        _session_manager = SessionManager()
    return _session_manager