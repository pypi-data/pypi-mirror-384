"""
Universal Browser Controller

Framework-agnostic browser automation using Playwright.
No framework adapters needed - pure universal operations.
"""

import asyncio
import time
from typing import Dict, List, Any, Optional
from playwright.async_api import async_playwright, Page, Browser, BrowserContext
import logging
from pathlib import Path

from .trace_manager import TraceManager
# v2.0 Enhancement: Hot Reload Intelligence
from .hmr_detector import HMRDetector
# v2.0 Enhancement: Enhanced Error Context Collection
from .error_context_collector import ErrorContextCollector


class BrowserController:
    """
    Universal browser automation - works with any web technology
    
    Provides simple, declarative interface without framework complexity.
    """
    
    def __init__(self, base_url: str, config: Dict):
        """
        Initialize browser controller
        
        Args:
            base_url: Base URL for testing
            config: {
                "headless": True,
                "debug_mode": False, 
                "human_timeout": 30,
                "viewport": {"width": 1440, "height": 900}
            }
        """
        self.base_url = base_url
        self.config = config
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None
        
        # Event tracking
        self.console_logs = []
        self.network_requests = []
        self.performance_metrics = []
        
        self.logger = logging.getLogger(__name__)
        
        # Ensure artifacts directory exists
        artifacts_base = Path(".cursorflow/artifacts")
        artifacts_base.mkdir(parents=True, exist_ok=True)
        Path(".cursorflow/artifacts/screenshots").mkdir(parents=True, exist_ok=True)
        
        # Initialize trace manager for v2.0 trace recording
        self.trace_manager = TraceManager(artifacts_base)
        self.session_id = None
        
        # v2.0 Enhancement: Hot Reload Intelligence
        self.hmr_detector = HMRDetector(base_url)
        self.hmr_monitoring_active = False
        
        # v2.0 Enhancement: Enhanced Error Context Collection
        self.error_context_collector = None  # Will be initialized after page is ready
        
    async def initialize(self, session_id: Optional[str] = None):
        """Initialize browser with universal settings and start trace recording"""
        try:
            # Generate session ID if not provided
            if session_id is None:
                session_id = f"session_{int(time.time())}"
            self.session_id = session_id
            
            self.playwright = await async_playwright().start()
            
            # Browser configuration - smart defaults with pass-through
            default_browser_config = {
                "headless": self.config.get("headless", True),
                "slow_mo": 0 if self.config.get("headless", True) else 100,
                "args": [
                    "--disable-web-security",
                    "--disable-features=VizDisplayCompositor",
                    "--disable-background-timer-throttling",
                    "--disable-backgrounding-occluded-windows",
                    "--disable-renderer-backgrounding"
                ]
            }
            
            # Pass-through architecture: Merge user options with defaults
            # Users can override ANY Playwright launch option
            # See: https://playwright.dev/python/docs/api/class-browsertype#browser-type-launch
            user_browser_options = self.config.get("browser_launch_options", {})
            
            # Validate user options (warns about typos, validates types)
            from .config_validator import ConfigValidator
            if user_browser_options:
                user_browser_options = ConfigValidator.validate_browser_options(user_browser_options)
            
            browser_config = {**default_browser_config, **user_browser_options}
            
            self.browser = await self.playwright.chromium.launch(**browser_config)
            
            # Context configuration - smart defaults with pass-through
            viewport = self.config.get("viewport", {"width": 1440, "height": 900})
            default_context_config = {
                "viewport": viewport,
                "ignore_https_errors": True,
                "record_video_dir": ".cursorflow/artifacts/videos" if self.config.get("record_video") else None
            }
            
            # Pass-through architecture: Merge user options with defaults
            # Users can use ANY Playwright context option:
            # - geolocation, permissions, timezone, locale
            # - color_scheme, reduced_motion, http_credentials
            # - user_agent, extra_http_headers, offline
            # See: https://playwright.dev/python/docs/api/class-browser#browser-new-context
            user_context_options = self.config.get("context_options", {})
            
            # Validate user options (warns about typos, validates types)
            if user_context_options:
                user_context_options = ConfigValidator.validate_context_options(user_context_options)
            
            context_config = {**default_context_config, **user_context_options}
            
            self.context = await self.browser.new_context(**context_config)
            self.page = await self.context.new_page()
            
            # Note: We do NOT block tracking scripts by default
            # CursorFlow philosophy: "Capture reality, not fiction"
            # Blocking scripts would alter the actual page behavior we're measuring
            
            # v2.0 Enhancement: Initialize Error Context Collector
            self.error_context_collector = ErrorContextCollector(self.page, self.logger)
            
            # Set references to browser data for context collection
            self.error_context_collector.set_browser_data_references(
                self.console_logs, 
                self.network_requests
            )
            
            # Start trace recording for comprehensive debugging (v2.0 feature)
            try:
                trace_path = await self.trace_manager.start_trace(self.context, self.session_id)
                self.logger.info(f"📹 Trace recording started: {trace_path}")
            except Exception as trace_error:
                self.logger.warning(f"Trace recording failed to start: {trace_error}")
            
            # Set up universal event listeners
            await self._setup_event_listeners()
            
            if not self.config.get("headless", True):
                self.logger.info("🖥️  Browser launched in FOREGROUND mode - human can interact")
            else:
                self.logger.info("🤖 Browser launched in HEADLESS mode - automated only")
                
        except Exception as e:
            self.logger.error(f"Browser initialization failed: {e}")
            
            # Save error trace if context was created (v2.0 feature)
            if self.context and self.trace_manager:
                try:
                    error_trace = await self.trace_manager.stop_trace_on_error(self.context, e)
                    if error_trace:
                        self.logger.error(f"📹 Error trace saved: {error_trace}")
                except Exception:
                    pass  # Don't let trace errors mask the original error
            
            raise
    
    async def _setup_event_listeners(self):
        """Set up universal event listeners for any framework"""
        
        # Console events
        self.page.on("console", self._handle_console_message)
        
        # Network events  
        self.page.on("request", self._handle_request)
        self.page.on("response", self._handle_response)
        
        # Page events
        self.page.on("pageerror", self._handle_page_error)
        self.page.on("crash", self._handle_page_crash)
        
    def _handle_console_message(self, msg):
        """Handle console messages from any framework with enhanced error context collection"""
        try:
            log_entry = {
                "timestamp": time.time(),
                "type": msg.type,
                "text": msg.text,
                "location": {
                    "url": msg.location.get("url", "") if msg.location else "",
                    "line": msg.location.get("lineNumber", 0) if msg.location else 0,
                    "column": msg.location.get("columnNumber", 0) if msg.location else 0
                },
                "args": [str(arg) for arg in msg.args] if msg.args else [],
                "stack_trace": getattr(msg, 'stackTrace', None)
            }
            self.console_logs.append(log_entry)
            
            # Enhanced logging for better correlation
            if msg.type == "error":
                self.logger.error(f"Console Error: {msg.text} at {msg.location}")
                
                # v2.0 Enhancement: Trigger error context collection for console errors
                if self.error_context_collector:
                    error_event = {
                        'type': 'console_error',
                        'message': msg.text,
                        'location': log_entry['location'],
                        'stack_trace': log_entry['stack_trace'],
                        'timestamp': log_entry['timestamp']
                    }
                    # Capture context asynchronously (don't block the event handler)
                    asyncio.create_task(self._collect_error_context_async(error_event))
                
            elif msg.type == "warning":
                self.logger.warning(f"Console Warning: {msg.text}")
            elif msg.type in ["log", "info"] and any(keyword in msg.text.lower() for keyword in ["error", "failed", "exception"]):
                # Catch application logs that indicate errors
                self.logger.warning(f"App Error Log: {msg.text}")
                
                # v2.0 Enhancement: Collect context for application error logs too
                if self.error_context_collector:
                    error_event = {
                        'type': 'app_error_log',
                        'message': msg.text,
                        'timestamp': log_entry['timestamp']
                    }
                    asyncio.create_task(self._collect_error_context_async(error_event))
        except Exception as e:
            # Defensive error handling - don't let console message parsing break tests
            self.logger.debug(f"Console message handler error: {e}")
            # Continue test execution despite error
    
    def _handle_request(self, request):
        """Handle network requests - framework agnostic"""
        try:
            # Capture complete request data
            request_data = {
                "timestamp": time.time(),
                "type": "request",
                "url": request.url,
                "method": request.method,
                "headers": dict(request.headers),
                "resource_type": request.resource_type,  # document, xhr, fetch, etc.
                "is_navigation_request": request.is_navigation_request()
            }
            
            # Capture complete payload data for all request types
            # Wrap in try/except to handle gzip-compressed data gracefully
            try:
                if request.post_data:
                    request_data["post_data"] = request.post_data
                    request_data["post_data_size"] = len(request.post_data)
                    
                    # Try to parse JSON payloads for better debugging
                    content_type = request.headers.get("content-type", "")
                    if "application/json" in content_type:
                        try:
                            import json
                            request_data["parsed_json"] = json.loads(request.post_data)
                        except:
                            pass
                    elif "application/x-www-form-urlencoded" in content_type:
                        try:
                            from urllib.parse import parse_qs
                            request_data["parsed_form"] = parse_qs(request.post_data)
                        except:
                            pass
            except UnicodeDecodeError:
                # Handle gzip-compressed or binary data gracefully
                # This happens when Playwright can't decode the post_data (e.g., gzip magic bytes 0x1f 0x8b)
                request_data["post_data"] = "[binary/compressed data]"
                request_data["post_data_size"] = 0
                self.logger.debug(f"Binary/compressed POST data detected for {request.url}")
            except Exception as e:
                # Graceful degradation - don't let post_data parsing break request tracking
                request_data["post_data"] = None
                request_data["post_data_size"] = 0
                self.logger.debug(f"Could not capture post_data for {request.url}: {e}")
            
            # Capture query parameters
            from urllib.parse import urlparse, parse_qs
            parsed_url = urlparse(request.url)
            if parsed_url.query:
                request_data["query_params"] = parse_qs(parsed_url.query)
                
            # Capture file uploads
            if "multipart/form-data" in request.headers.get("content-type", ""):
                request_data["has_file_upload"] = True
                # Note: Actual file content not captured for performance/privacy
                
            self.network_requests.append(request_data)
            
            # Enhanced logging for correlation
            if request.resource_type in ["xhr", "fetch"] or "/api/" in request.url:
                payload_info = ""
                post_data_value = request_data.get("post_data")
                post_data_size = request_data.get("post_data_size", 0)
                if post_data_value and post_data_size > 0:
                    payload_info = f" (payload: {post_data_size} bytes)"
                self.logger.debug(f"API Request: {request.method} {request.url}{payload_info}")
                
                # Log critical data for immediate debugging
                if post_data_value and post_data_size > 0 and post_data_size < 500:  # Only log small payloads
                    self.logger.debug(f"Request payload: {post_data_value}")
        except Exception as e:
            # Top-level defensive error handling - don't let request handler break event listeners
            self.logger.debug(f"Request handler error: {e}")
            # Continue test execution despite error
    
    def _handle_response(self, response):
        """Handle network responses with enhanced error context collection"""
        try:
            response_data = {
                "timestamp": time.time(),
                "type": "response", 
                "url": response.url,
                "status": response.status,
                "status_text": response.status_text,
                "headers": dict(response.headers),
                "size": 0,  # Will be populated by _capture_response_body if needed
                "from_cache": response.from_service_worker or False
            }
            self.network_requests.append(response_data)
            
            # Capture response body asynchronously (Phase 1.4: Network Response Body Capture)
            asyncio.create_task(self._capture_response_body_async(response, response_data))
            
            # Log failed requests for correlation
            if response.status >= 400:
                self.logger.warning(f"Failed Response: {response.status} {response.url}")
                
                # v2.0 Enhancement: Trigger error context collection for failed requests
                if self.error_context_collector:
                    error_event = {
                        'type': 'network_error',
                        'url': response.url,
                        'status': response.status,
                        'status_text': response.status_text,
                        'headers': dict(response.headers),
                        'timestamp': response_data['timestamp']
                    }
                    # Capture context asynchronously
                    asyncio.create_task(self._collect_error_context_async(error_event))
            
            # Capture response body for important requests
            should_capture_body = (
                response.status >= 400 or  # All error responses
                any(api_path in response.url for api_path in ["/api/", "/ajax", ".json"]) or  # API calls
                "application/json" in response.headers.get("content-type", "")  # JSON responses
            )
            
            if should_capture_body:
                asyncio.create_task(self._capture_response_body(response))
        except Exception as e:
            # Defensive error handling - don't let response handler break event listeners
            self.logger.debug(f"Response handler error: {e}")
            # Continue test execution despite error
    
    def _handle_page_error(self, error):
        """Handle page errors from any framework"""
        try:
            self.console_logs.append({
                "timestamp": time.time(),
                "type": "pageerror",
                "text": str(error),
                "location": None
            })
            self.logger.error(f"Page error: {error}")
        except Exception as e:
            # Defensive error handling - don't let page error handler break event listeners
            self.logger.debug(f"Page error handler error: {e}")
            # Continue test execution despite error
    
    def _handle_page_crash(self, page):
        """Handle page crashes"""
        try:
            self.logger.error("Page crashed - attempting recovery")
        except Exception as e:
            # Defensive error handling - don't let crash handler break event listeners
            self.logger.debug(f"Page crash handler error: {e}")
            # Continue test execution despite error
    
    async def navigate(self, path: str, wait_for_load: bool = True):
        """Navigate to URL - works with any web framework"""
        try:
            # Build full URL
            if path.startswith(("http://", "https://")):
                url = path
            else:
                url = f"{self.base_url.rstrip('/')}/{path.lstrip('/')}"
            
            self.logger.info(f"Navigating to: {url}")
            
            # Navigate and wait
            # Use 'load' instead of 'networkidle' to avoid timeout on pages with tracking scripts
            if wait_for_load:
                await self.page.goto(url, wait_until="load", timeout=30000)
            else:
                await self.page.goto(url, timeout=30000)
                
            # Universal ready state check (works for any framework)
            await self.page.wait_for_load_state("domcontentloaded")
            
        except Exception as e:
            self.logger.error(f"Navigation failed to {path}: {e}")
            raise
    
    async def click(self, selector: str, timeout: int = 10000):
        """Click element - universal across frameworks"""
        try:
            await self.page.wait_for_selector(selector, timeout=timeout)
            await self.page.click(selector)
            self.logger.debug(f"Clicked: {selector}")
            
        except Exception as e:
            if not self.config.get("headless", True):
                # In foreground mode, allow human intervention
                self.logger.warning(f"Click failed for {selector}: {e}")
                self.logger.info(f"Human has {self.config.get('human_timeout', 30)} seconds to manually click...")
                await asyncio.sleep(self.config.get('human_timeout', 30))
            else:
                raise
    
    async def fill(self, selector: str, value: str, timeout: int = 10000):
        """Fill input field - universal"""
        try:
            await self.page.wait_for_selector(selector, timeout=timeout)
            await self.page.fill(selector, value)
            self.logger.debug(f"Filled {selector}: {value}")
            
        except Exception as e:
            self.logger.error(f"Fill failed for {selector}: {e}")
            raise
    
    async def type(self, selector: str, text: str, delay: int = 50):
        """Type text slowly - useful for complex forms"""
        try:
            await self.page.wait_for_selector(selector)
            await self.page.type(selector, text, delay=delay)
            self.logger.debug(f"Typed in {selector}: {text}")
            
        except Exception as e:
            self.logger.error(f"Type failed for {selector}: {e}")
            raise
    
    async def wait_for_element(self, selector: str, timeout: int = 30000, state: str = "visible"):
        """Wait for element - universal"""
        try:
            await self.page.wait_for_selector(selector, timeout=timeout, state=state)
            self.logger.debug(f"Element ready: {selector}")
            
        except Exception as e:
            self.logger.error(f"Wait failed for {selector}: {e}")
            raise
    
    async def wait_for_condition(self, condition: str, timeout: int = 30000):
        """Wait for custom JavaScript condition - universal"""
        try:
            await self.page.wait_for_function(condition, timeout=timeout)
            self.logger.debug(f"Condition met: {condition}")
            
        except Exception as e:
            self.logger.error(f"Condition wait failed: {condition}, {e}")
            raise
    
    async def screenshot(self, name: str, options: Optional[Dict] = None, capture_comprehensive_data: bool = True) -> Dict[str, Any]:
        """
        Take screenshot with comprehensive page analysis - universal
        
        Args:
            name: Screenshot name/identifier
            options: Enhanced screenshot options {
                "full_page": bool,           # Capture full page (default: False)
                "clip": {                    # Clip to specific region
                    "x": int, "y": int,      # Top-left coordinates
                    "width": int, "height": int
                } OR {
                    "selector": str          # Clip to element bounding box
                },
                "mask": [str],              # CSS selectors to hide/mask
                "quality": int              # JPEG quality 0-100 (default: 80) - requires .jpg/.jpeg filename
            }
            capture_comprehensive_data: Whether to capture detailed page analysis
        """
        try:
            # Process options with defaults
            raw_options = options or {}
            full_page = raw_options.get("full_page", False)
            clip_config = raw_options.get("clip")
            mask_selectors = raw_options.get("mask", [])
            quality = raw_options.get("quality", 80)
            
            # Build actual screenshot options used (for metadata)
            screenshot_options = {
                "full_page": full_page,
                "quality": quality
            }
            if clip_config:
                screenshot_options["clip"] = clip_config
            if mask_selectors:
                screenshot_options["mask"] = mask_selectors
            
            timestamp = int(time.time())
            screenshot_filename = f".cursorflow/artifacts/screenshots/{name}_{timestamp}.png"
            
            # Apply masking if requested (hide sensitive elements)
            masked_elements = []
            if mask_selectors:
                for selector in mask_selectors:
                    try:
                        await self.page.add_style_tag(content=f"""
                            {selector} {{
                                visibility: hidden !important;
                                opacity: 0 !important;
                            }}
                        """)
                        masked_elements.append(selector)
                        self.logger.debug(f"Masked element: {selector}")
                    except Exception as e:
                        self.logger.warning(f"Failed to mask {selector}: {e}")
            
            # Prepare screenshot parameters
            screenshot_params = {
                "path": screenshot_filename,
                "full_page": full_page
            }
            
            # Only add quality for JPEG screenshots
            if screenshot_filename.lower().endswith(('.jpg', '.jpeg')):
                screenshot_params["quality"] = quality
                screenshot_params["type"] = "jpeg"
            # PNG is default and doesn't support quality parameter
            
            # Handle clipping options
            if clip_config:
                if "selector" in clip_config:
                    # Clip to element bounding box
                    try:
                        element = await self.page.wait_for_selector(clip_config["selector"], timeout=5000)
                        if element:
                            bounding_box = await element.bounding_box()
                            if bounding_box:
                                screenshot_params["clip"] = bounding_box
                                self.logger.debug(f"Clipping to element {clip_config['selector']}: {bounding_box}")
                            else:
                                self.logger.warning(f"Element {clip_config['selector']} has no bounding box")
                        else:
                            self.logger.warning(f"Element {clip_config['selector']} not found for clipping")
                    except Exception as e:
                        self.logger.warning(f"Failed to clip to element {clip_config['selector']}: {e}")
                
                elif all(key in clip_config for key in ["x", "y", "width", "height"]):
                    # Clip to specific coordinates
                    screenshot_params["clip"] = {
                        "x": clip_config["x"],
                        "y": clip_config["y"], 
                        "width": clip_config["width"],
                        "height": clip_config["height"]
                    }
                    self.logger.debug(f"Clipping to coordinates: {screenshot_params['clip']}")
            
            # Take the visual screenshot
            await self.page.screenshot(**screenshot_params)
            
            # Remove masking styles
            if masked_elements:
                try:
                    for selector in masked_elements:
                        await self.page.add_style_tag(content=f"""
                            {selector} {{
                                visibility: visible !important;
                                opacity: 1 !important;
                            }}
                        """)
                except Exception as e:
                    self.logger.warning(f"Failed to remove masking: {e}")
            
            # Always return structured data for consistency
            screenshot_data = {
                "screenshot_path": screenshot_filename,
                "timestamp": timestamp,
                "name": name,
                "options": screenshot_options,
                "session_id": self.session_id,
                "trace_info": self.trace_manager.get_trace_info() if self.trace_manager else None
            }
            
            if capture_comprehensive_data:
                # Capture comprehensive page analysis (ALL visible elements)
                comprehensive_data = await self._capture_comprehensive_page_analysis()
                
                # Save comprehensive data alongside screenshot
                data_filename = f".cursorflow/artifacts/screenshots/{name}_{timestamp}_comprehensive_data.json"
                import json
                with open(data_filename, 'w') as f:
                    json.dump(comprehensive_data, f, indent=2, default=str)
                
                # Merge all data into structured response
                screenshot_data.update({
                    "comprehensive_data_path": data_filename,
                    "dom_analysis": comprehensive_data.get("dom_analysis", {}),
                    "network_data": comprehensive_data.get("network_data", {}),
                    "console_data": comprehensive_data.get("console_data", {}),
                    "performance_data": comprehensive_data.get("performance_data", {}),
                    "page_state": comprehensive_data.get("page_state", {}),
                    "analysis_summary": comprehensive_data.get("analysis_summary", {})
                })
                
                self.logger.debug(f"Screenshot with comprehensive data saved: {screenshot_filename}, {data_filename}")
            else:
                self.logger.debug(f"Screenshot saved: {screenshot_filename}")
            
            return screenshot_data
            
        except Exception as e:
            self.logger.error(f"Screenshot with comprehensive analysis failed: {e}")
            raise
    
    async def evaluate_javascript(self, script: str) -> Any:
        """Execute JavaScript - universal"""
        try:
            result = await self.page.evaluate(script)
            return result
            
        except Exception as e:
            self.logger.error(f"JavaScript evaluation failed: {e}")
            raise
    
    async def get_computed_styles(self, selector: str) -> Dict:
        """Get computed styles for element - universal"""
        try:
            script = f"""
                (selector) => {{
                    const el = document.querySelector(selector);
                    if (!el) return null;
                    const styles = window.getComputedStyle(el);
                    return {{
                        position: styles.position,
                        display: styles.display,
                        flexDirection: styles.flexDirection,
                        justifyContent: styles.justifyContent,
                        alignItems: styles.alignItems,
                        width: styles.width,
                        height: styles.height,
                        margin: styles.margin,
                        padding: styles.padding,
                        fontSize: styles.fontSize,
                        color: styles.color,
                        backgroundColor: styles.backgroundColor
                    }};
                }}
            """
            
            result = await self.page.evaluate(script, selector)
            return result or {}
            
        except Exception as e:
            self.logger.error(f"Get computed styles failed for {selector}: {e}")
            return {}
    
    async def inject_css(self, css: str) -> bool:
        """Inject CSS into page - universal"""
        try:
            await self.page.add_style_tag(content=css)
            await self.page.wait_for_timeout(100)  # Let CSS apply
            return True
            
        except Exception as e:
            self.logger.error(f"CSS injection failed: {e}")
            return False
    
    async def set_viewport(self, width: int, height: int):
        """Change viewport size - universal"""
        try:
            await self.page.set_viewport_size({"width": width, "height": height})
            await self.page.wait_for_timeout(200)  # Let layout stabilize
            
        except Exception as e:
            self.logger.error(f"Viewport change failed: {e}")
            raise
    
    async def get_performance_metrics(self) -> Dict:
        """Get page performance metrics - universal with proper null handling"""
        try:
            metrics = await self.page.evaluate("""
                () => {
                    // Helper function to safely calculate timing differences
                    const safeTiming = (end, start) => {
                        if (!end || !start || end === 0 || start === 0) return null;
                        const diff = end - start;
                        return diff >= 0 ? diff : null;
                    };
                    
                    const perf = performance.getEntriesByType('navigation')[0];
                    const paint = performance.getEntriesByType('paint');
                    const lcp = performance.getEntriesByType('largest-contentful-paint')[0];
                    
                    return {
                        loadTime: perf ? safeTiming(perf.loadEventEnd, perf.loadEventStart) : null,
                        domContentLoaded: perf ? safeTiming(perf.domContentLoadedEventEnd, perf.domContentLoadedEventStart) : null,
                        firstPaint: paint.find(p => p.name === 'first-paint')?.startTime || null,
                        largestContentfulPaint: lcp?.startTime || null,
                        _reliability: {
                            navigation_available: perf !== undefined,
                            paint_available: paint.length > 0,
                            lcp_available: lcp !== undefined,
                            note: "null values in headless mode are expected"
                        }
                    };
                }
            """)
            
            return metrics
            
        except Exception as e:
            self.logger.error(f"Performance metrics failed: {e}")
            return {"error": str(e)}
    
    async def cleanup(self):
        """Clean up browser resources and stop trace recording"""
        try:
            # Stop trace recording first (v2.0 feature)
            trace_path = None
            if self.context and self.trace_manager:
                try:
                    trace_path = await self.trace_manager.stop_trace(self.context)
                    if trace_path:
                        self.logger.info(f"📹 Trace recording saved: {trace_path}")
                        self.logger.info(f"View trace: {self.trace_manager.get_viewing_instructions(trace_path)}")
                except Exception as trace_error:
                    self.logger.warning(f"Trace recording cleanup failed: {trace_error}")
            
            # Clean up browser resources
            if self.page:
                await self.page.close()
            if self.context:
                await self.context.close()
            if self.browser:
                await self.browser.close()
            if self.playwright:
                await self.playwright.stop()
                
            self.logger.info("Browser cleanup completed")
            return trace_path
            
        except Exception as e:
            self.logger.error(f"Browser cleanup failed: {e}")
            return None
    
    async def _capture_response_body_async(self, response, response_data: Dict):
        """
        Async wrapper to capture response body without blocking event handlers
        
        Phase 1.4: Network Response Body Capture
        Captures request/response bodies for complete debugging data
        """
        try:
            # Get response body
            body = await response.body()
            decoded_body = body.decode('utf-8', errors='ignore')
            
            # Update the response_data dict directly (it's already in self.network_requests)
            response_data["response_body"] = decoded_body[:5000]  # Capture more for debugging
            response_data["response_body_size"] = len(decoded_body)
            response_data["response_body_truncated"] = len(decoded_body) > 5000
            
            # Parse JSON responses automatically
            content_type = response.headers.get("content-type", "")
            if "application/json" in content_type:
                try:
                    import json
                    response_data["response_body_json"] = json.loads(decoded_body)
                    
                    # Log key data for debugging undefined values
                    self.logger.debug(f"JSON Response from {response.url[:50]}: {len(response_data['response_body_json'])} keys")
                except json.JSONDecodeError as e:
                    response_data["json_parse_error"] = str(e)
                    self.logger.warning(f"Failed to parse JSON response from {response.url}: {e}")
            
            # Log error responses
            if response.status >= 400:
                error_preview = decoded_body[:200].replace('\n', ' ')
                self.logger.error(f"Error response ({response.status}) from {response.url}: {error_preview}")
                    
        except Exception as e:
            self.logger.debug(f"Response body capture failed for {response.url}: {e}")
            response_data["body_capture_error"] = str(e)
    
    async def _capture_response_body(self, response):
        """Legacy method - captures response body for specific cases"""
        try:
            body = await response.body()
            decoded_body = body.decode('utf-8', errors='ignore')
            
            # Find and update the matching response entry
            for req in reversed(self.network_requests):
                if (req.get("type") == "response" and 
                    req.get("url") == response.url and
                    req.get("status") == response.status):
                    
                    # Store raw body (truncated for large responses)
                    req["body"] = decoded_body[:2000]  # Increased limit for debugging
                    req["body_size"] = len(decoded_body)
                    req["body_truncated"] = len(decoded_body) > 2000
                    
                    # Parse JSON responses for easier debugging
                    content_type = response.headers.get("content-type", "")
                    if "application/json" in content_type:
                        try:
                            import json
                            req["parsed_json"] = json.loads(decoded_body)
                        except:
                            req["json_parse_error"] = True
                    
                    # Log important error responses for immediate visibility
                    if response.status >= 400:
                        error_preview = decoded_body[:200].replace('\n', ' ')
                        self.logger.error(f"Error response body: {error_preview}")
                    
                    break
                    
        except Exception as e:
            self.logger.error(f"Response body capture failed for {response.url}: {e}")
            # Add error info to the response record
            for req in reversed(self.network_requests):
                if (req.get("type") == "response" and req.get("url") == response.url):
                    req["body_capture_error"] = str(e)
                    break
    
    async def _capture_javascript_context(self) -> Dict[str, Any]:
        """
        Phase 2.2: JavaScript Context Capture
        
        Captures global JavaScript scope including:
        - Global functions (enumerate window properties that are functions)
        - Global variables (enumerate window properties that are not functions)
        - Specific window objects (configurable list to serialize)
        """
        try:
            # Get list of objects to capture from config
            capture_objects = self.config.get("capture_window_objects", [])
            
            context_data = await self.page.evaluate("""
                (captureObjects) => {
                    const context = {
                        global_functions: [],
                        global_variables: [],
                        window_property_count: 0,
                        window_objects: {}
                    };
                    
                    // Enumerate window properties
                    const windowProps = Object.getOwnPropertyNames(window);
                    context.window_property_count = windowProps.length;
                    
                    // Categorize by type
                    windowProps.forEach(prop => {
                        try {
                            const value = window[prop];
                            
                            // Skip built-in browser objects (too many)
                            if (prop.startsWith('webkit') || prop.startsWith('moz') || 
                                prop.startsWith('chrome') || prop === 'constructor') {
                                return;
                            }
                            
                            if (typeof value === 'function') {
                                // Skip native functions (toString contains '[native code]')
                                const funcStr = value.toString();
                                if (!funcStr.includes('[native code]')) {
                                    context.global_functions.push(prop);
                                }
                            } else if (value !== null && typeof value !== 'undefined' && 
                                      typeof value !== 'function' && typeof value !== 'object') {
                                // Primitive global variables
                                context.global_variables.push({
                                    name: prop,
                                    type: typeof value,
                                    value: String(value).substring(0, 100)  // Truncate long values
                                });
                            }
                        } catch (e) {
                            // Skip properties that throw on access
                        }
                    });
                    
                    // Capture specific window objects (configurable)
                    captureObjects.forEach(objName => {
                        try {
                            const obj = window[objName];
                            if (obj && typeof obj === 'object') {
                                // Serialize object (handle circular references)
                                context.window_objects[objName] = JSON.parse(
                                    JSON.stringify(obj, (key, value) => {
                                        // Handle circular references
                                        if (typeof value === 'object' && value !== null) {
                                            if (key && typeof value === 'object' && Object.keys(value).length > 50) {
                                                return '[Large Object]';
                                            }
                                        }
                                        // Handle functions
                                        if (typeof value === 'function') {
                                            return '[Function]';
                                        }
                                        return value;
                                    })
                                );
                            }
                        } catch (e) {
                            context.window_objects[objName] = {
                                error: `Failed to serialize: ${e.message}`
                            };
                        }
                    });
                    
                    return context;
                }
            """, capture_objects)
            
            return context_data
            
        except Exception as e:
            self.logger.error(f"JavaScript context capture failed: {e}")
            return {
                "error": str(e),
                "global_functions": [],
                "global_variables": [],
                "window_objects": {}
            }
    
    async def _capture_storage_state(self) -> Dict[str, Any]:
        """
        Phase 2.3: Storage State Capture
        
        Captures browser storage state:
        - localStorage
        - sessionStorage
        - cookies
        
        Masks sensitive keys based on configuration.
        """
        try:
            # Get masking configuration
            sensitive_keys = self.config.get("sensitive_storage_keys", [
                "authToken", "apiKey", "sessionId", "password", "secret", "token"
            ])
            
            storage_data = await self.page.evaluate("""
                (sensitiveKeys) => {
                    const storage = {
                        localStorage: {},
                        sessionStorage: {},
                        cookies: []
                    };
                    
                    // Capture localStorage
                    for (let i = 0; i < localStorage.length; i++) {
                        const key = localStorage.key(i);
                        const value = localStorage.getItem(key);
                        
                        // Mask sensitive keys
                        const isSensitive = sensitiveKeys.some(pattern => 
                            key.toLowerCase().includes(pattern.toLowerCase())
                        );
                        
                        storage.localStorage[key] = isSensitive ? '****' : value;
                    }
                    
                    // Capture sessionStorage
                    for (let i = 0; i < sessionStorage.length; i++) {
                        const key = sessionStorage.key(i);
                        const value = sessionStorage.getItem(key);
                        
                        const isSensitive = sensitiveKeys.some(pattern =>
                            key.toLowerCase().includes(pattern.toLowerCase())
                        );
                        
                        storage.sessionStorage[key] = isSensitive ? '****' : value;
                    }
                    
                    // Capture cookies (just names, not values for security)
                    storage.cookies = document.cookie.split(';').map(c => c.trim().split('=')[0]);
                    
                    return storage;
                }
            """, sensitive_keys)
            
            return storage_data
            
        except Exception as e:
            self.logger.error(f"Storage state capture failed: {e}")
            return {
                "error": str(e),
                "localStorage": {},
                "sessionStorage": {},
                "cookies": []
            }
    
    async def _capture_form_state(self) -> Dict[str, Any]:
        """
        Phase 2.4: Form State Capture
        
        Captures all form field values at time of capture.
        Automatically masks password fields.
        """
        try:
            form_data = await self.page.evaluate("""
                () => {
                    const forms = {};
                    
                    // Get all forms on page
                    document.querySelectorAll('form').forEach(form => {
                        const formId = form.id || form.name || `form_${forms.length}`;
                        const formData = {};
                        
                        // Get all form inputs
                        form.querySelectorAll('input, select, textarea').forEach(field => {
                            const fieldName = field.name || field.id || `field_${field.type}`;
                            
                            // Mask password fields
                            if (field.type === 'password') {
                                formData[fieldName] = '****';
                            }
                            // Checkbox/radio
                            else if (field.type === 'checkbox' || field.type === 'radio') {
                                formData[fieldName] = field.checked;
                            }
                            // Select dropdowns
                            else if (field.tagName === 'SELECT') {
                                formData[fieldName] = field.value;
                            }
                            // Text inputs, textareas
                            else {
                                formData[fieldName] = field.value;
                            }
                        });
                        
                        forms[formId] = formData;
                    });
                    
                    return forms;
                }
            """)
            
            return form_data
            
        except Exception as e:
            self.logger.error(f"Form state capture failed: {e}")
            return {"error": str(e)}
    
    def _categorize_http_error(self, status_code: int) -> str:
        """Categorize HTTP errors for better debugging (v2.0 enhancement)"""
        if 400 <= status_code < 500:
            error_categories = {
                400: "Bad Request",
                401: "Authentication Required", 
                403: "Access Forbidden",
                404: "Resource Not Found",
                405: "Method Not Allowed",
                409: "Conflict",
                422: "Validation Error",
                429: "Rate Limited"
            }
            return error_categories.get(status_code, "Client Error")
        elif 500 <= status_code < 600:
            error_categories = {
                500: "Server Error",
                502: "Bad Gateway",
                503: "Service Unavailable",
                504: "Gateway Timeout"
            }
            return error_categories.get(status_code, "Server Error")
        else:
            return "Unknown Error"
    
    def _analyze_error_cause(self, status_code: int, body: str) -> str:
        """Analyze likely cause of HTTP errors (v2.0 enhancement)"""
        body_lower = body.lower()
        
        if status_code == 401:
            if "token" in body_lower or "jwt" in body_lower:
                return "Invalid or expired authentication token"
            elif "login" in body_lower or "credential" in body_lower:
                return "Invalid credentials"
            else:
                return "Authentication required"
        elif status_code == 403:
            if "permission" in body_lower or "role" in body_lower:
                return "Insufficient permissions"
            else:
                return "Access denied"
        elif status_code == 404:
            return "Endpoint or resource does not exist"
        elif status_code == 422:
            if "validation" in body_lower:
                return "Input validation failed"
            else:
                return "Request data invalid"
        elif status_code == 429:
            return "Too many requests - rate limit exceeded"
        elif status_code >= 500:
            if "database" in body_lower or "sql" in body_lower:
                return "Database connection or query error"
            elif "timeout" in body_lower:
                return "Server timeout"
            else:
                return "Internal server error"
        else:
            return "Unknown error condition"
    
    async def capture_network_har(self) -> Dict:
        """Capture full network activity as HAR format"""
        try:
            # Get all network requests in HAR-like format
            har_entries = []
            
            for req in self.network_requests:
                if req.get("type") == "request":
                    # Find matching response
                    response = None
                    for resp in self.network_requests:
                        if (resp.get("type") == "response" and 
                            resp.get("url") == req.get("url") and
                            resp.get("timestamp", 0) > req.get("timestamp", 0)):
                            response = resp
                            break
                    
                    har_entry = {
                        "request": {
                            "method": req.get("method"),
                            "url": req.get("url"),
                            "headers": req.get("headers", {}),
                            "postData": req.get("post_data"),
                            "timestamp": req.get("timestamp")
                        },
                        "response": response if response else {"status": 0},
                        "time": (response.get("timestamp", 0) - req.get("timestamp", 0)) * 1000  # ms
                    }
                    har_entries.append(har_entry)
            
            return {"entries": har_entries}
            
        except Exception as e:
            self.logger.error(f"HAR capture failed: {e}")
            return {"entries": []}
    
    def get_console_errors(self) -> List[Dict]:
        """Get only console errors for quick analysis"""
        return [log for log in self.console_logs if log.get("type") == "error"]
    
    def get_failed_requests(self) -> List[Dict]:
        """Get only failed network requests"""
        failed = []
        for req in self.network_requests:
            if (req.get("type") == "response" and 
                req.get("status", 0) >= 400):
                failed.append(req)
        return failed
    
    async def _capture_comprehensive_page_analysis(self) -> Dict[str, Any]:
        """
        Enhanced comprehensive page analysis with v2.0 features: fonts, animations, resources, storage
        
        v2.1: Now captures ALL visible elements - truly comprehensive, no hardcoded limits.
        """
        try:
            # Capture DOM analysis (ALL visible elements)
            dom_analysis = await self._capture_dom_analysis()
            
            # Capture current network state
            network_data = self._capture_network_data()
            
            # Capture current console state
            console_data = self._capture_console_data()
            
            # Capture performance metrics
            performance_data = await self._capture_performance_data()
            
            # Capture page state information
            page_state = await self._capture_page_state()
            
            # v2.0 Enhancement: Font loading status
            font_analysis = await self._capture_font_loading_status()
            
            # v2.0 Enhancement: Animation state
            animation_analysis = await self._capture_animation_state()
            
            # v2.0 Enhancement: Resource loading analysis
            resource_analysis = await self._capture_resource_loading_analysis()
            
            # v2.2 Enhancement: Enhanced context capture
            javascript_context = await self._capture_javascript_context()
            storage_state = await self._capture_storage_state()  # This also serves as storage_analysis
            form_state = await self._capture_form_state()
            
            # Create enhanced analysis summary
            analysis_summary = self._create_analysis_summary(
                dom_analysis, network_data, console_data, performance_data,
                font_analysis, animation_analysis, resource_analysis, storage_state
            )
            
            return {
                "dom_analysis": dom_analysis,
                "network_data": network_data,
                "console_data": console_data,
                "javascript_context": javascript_context,
                "storage_state": storage_state,
                "form_state": form_state,
                "performance_data": performance_data,
                "page_state": page_state,
                
                # v2.0 Enhancements
                "font_analysis": font_analysis,
                "animation_analysis": animation_analysis,
                "resource_analysis": resource_analysis,
                "storage_analysis": storage_state,  # v2.2 uses storage_state
                
                "analysis_summary": analysis_summary,
                "capture_timestamp": time.time(),
                "analysis_version": "2.0"
            }
            
        except Exception as e:
            self.logger.error(f"Enhanced comprehensive page analysis failed: {e}")
            return {"error": str(e), "capture_timestamp": time.time()}
    
    async def _capture_font_loading_status(self) -> Dict[str, Any]:
        """v2.0 Enhancement: Capture comprehensive font loading analysis"""
        try:
            font_analysis = await self.page.evaluate("""
                async () => {
                    // Wait for document.fonts to be available
                    if (!document.fonts) {
                        return {
                            fonts_supported: false,
                            error: "Font Loading API not supported"
                        };
                    }
                    
                    // Get all font faces
                    const fontFaces = Array.from(document.fonts);
                    
                    // Analyze font loading status
                    const fontStatus = {
                        total_fonts: fontFaces.length,
                        loaded_fonts: 0,
                        loading_fonts: 0,
                        failed_fonts: 0,
                        unloaded_fonts: 0,
                        font_details: []
                    };
                    
                    // Check if fonts are ready
                    const fontsReady = await document.fonts.ready;
                    
                    // Analyze each font face
                    fontFaces.forEach(fontFace => {
                        const fontInfo = {
                            family: fontFace.family,
                            style: fontFace.style,
                            weight: fontFace.weight,
                            stretch: fontFace.stretch,
                            unicode_range: fontFace.unicodeRange,
                            variant: fontFace.variant,
                            status: fontFace.status,
                            source: fontFace.src || 'system'
                        };
                        
                        // Count by status
                        switch (fontFace.status) {
                            case 'loaded':
                                fontStatus.loaded_fonts++;
                                break;
                            case 'loading':
                                fontStatus.loading_fonts++;
                                break;
                            case 'error':
                                fontStatus.failed_fonts++;
                                break;
                            case 'unloaded':
                                fontStatus.unloaded_fonts++;
                                break;
                        }
                        
                        fontStatus.font_details.push(fontInfo);
                    });
                    
                    // Get computed font families used on the page
                    const usedFonts = new Set();
                    const elements = document.querySelectorAll('*');
                    
                    elements.forEach(element => {
                        const computedStyle = window.getComputedStyle(element);
                        const fontFamily = computedStyle.fontFamily;
                        if (fontFamily && fontFamily !== 'inherit') {
                            usedFonts.add(fontFamily);
                        }
                    });
                    
                    // Font loading performance
                    const fontLoadingMetrics = {
                        fonts_ready: fontsReady !== null,
                        loading_complete: fontStatus.loading_fonts === 0,
                        has_failures: fontStatus.failed_fonts > 0,
                        load_success_rate: fontStatus.total_fonts > 0 ? 
                            (fontStatus.loaded_fonts / fontStatus.total_fonts * 100).toFixed(2) + '%' : '100%'
                    };
                    
                    return {
                        fonts_supported: true,
                        font_status: fontStatus,
                        used_font_families: Array.from(usedFonts),
                        loading_metrics: fontLoadingMetrics,
                        capture_timestamp: Date.now()
                    };
                }
            """)
            
            return font_analysis
            
        except Exception as e:
            self.logger.error(f"Font loading analysis failed: {e}")
            return {
                "fonts_supported": False,
                "error": str(e),
                "capture_timestamp": time.time()
            }
    
    async def _capture_animation_state(self) -> Dict[str, Any]:
        """v2.0 Enhancement: Capture CSS animation and transition state"""
        try:
            animation_analysis = await self.page.evaluate("""
                () => {
                    const animationData = {
                        total_animated_elements: 0,
                        running_animations: 0,
                        paused_animations: 0,
                        finished_animations: 0,
                        running_transitions: 0,
                        animation_details: [],
                        transition_details: []
                    };
                    
                    // Get all elements on the page
                    const elements = document.querySelectorAll('*');
                    
                    elements.forEach(element => {
                        // Check for CSS animations
                        const animations = element.getAnimations ? element.getAnimations() : [];
                        
                        if (animations.length > 0) {
                            animationData.total_animated_elements++;
                            
                            animations.forEach(animation => {
                                const animInfo = {
                                    element_selector: element.tagName.toLowerCase() + 
                                        (element.id ? '#' + element.id : '') +
                                        (element.className && typeof element.className === 'string' ? '.' + element.className.split(' ').join('.') : ''),
                                    animation_name: animation.animationName || 'transition',
                                    duration: animation.effect?.getTiming?.()?.duration || 0,
                                    delay: animation.effect?.getTiming?.()?.delay || 0,
                                    iterations: animation.effect?.getTiming?.()?.iterations || 1,
                                    direction: animation.effect?.getTiming?.()?.direction || 'normal',
                                    fill_mode: animation.effect?.getTiming?.()?.fill || 'none',
                                    play_state: animation.playState,
                                    current_time: animation.currentTime,
                                    start_time: animation.startTime,
                                    timeline: animation.timeline?.currentTime || null
                                };
                                
                                // Count by play state
                                switch (animation.playState) {
                                    case 'running':
                                        if (animation.animationName) {
                                            animationData.running_animations++;
                                        } else {
                                            animationData.running_transitions++;
                                        }
                                        break;
                                    case 'paused':
                                        animationData.paused_animations++;
                                        break;
                                    case 'finished':
                                        animationData.finished_animations++;
                                        break;
                                }
                                
                                if (animation.animationName) {
                                    animationData.animation_details.push(animInfo);
                                } else {
                                    animationData.transition_details.push(animInfo);
                                }
                            });
                        }
                        
                        // Also check computed styles for animation properties
                        const computedStyle = window.getComputedStyle(element);
                        const animationName = computedStyle.animationName;
                        const transitionProperty = computedStyle.transitionProperty;
                        
                        if (animationName && animationName !== 'none' && animations.length === 0) {
                            // Animation defined but not running (possibly finished or not started)
                            animationData.animation_details.push({
                                element_selector: element.tagName.toLowerCase() + 
                                    (element.id ? '#' + element.id : '') +
                                    (element.className && typeof element.className === 'string' ? '.' + element.className.split(' ').join('.') : ''),
                                animation_name: animationName,
                                duration: computedStyle.animationDuration,
                                delay: computedStyle.animationDelay,
                                iterations: computedStyle.animationIterationCount,
                                direction: computedStyle.animationDirection,
                                fill_mode: computedStyle.animationFillMode,
                                play_state: 'inactive',
                                timing_function: computedStyle.animationTimingFunction
                            });
                        }
                        
                        if (transitionProperty && transitionProperty !== 'none' && 
                            !animationData.transition_details.some(t => t.element_selector.includes(element.tagName))) {
                            animationData.transition_details.push({
                                element_selector: element.tagName.toLowerCase() + 
                                    (element.id ? '#' + element.id : '') +
                                    (element.className && typeof element.className === 'string' ? '.' + element.className.split(' ').join('.') : ''),
                                transition_property: transitionProperty,
                                duration: computedStyle.transitionDuration,
                                delay: computedStyle.transitionDelay,
                                timing_function: computedStyle.transitionTimingFunction,
                                play_state: 'ready'
                            });
                        }
                    });
                    
                    // Animation performance summary
                    const animationSummary = {
                        has_active_animations: animationData.running_animations > 0 || animationData.running_transitions > 0,
                        performance_impact: animationData.running_animations > 10 ? 'high' : 
                                          animationData.running_animations > 3 ? 'medium' : 'low',
                        animation_stability: animationData.paused_animations === 0 && animationData.running_animations > 0 ? 'stable' : 'mixed',
                        total_active: animationData.running_animations + animationData.running_transitions
                    };
                    
                    return {
                        ...animationData,
                        animation_summary: animationSummary,
                        capture_timestamp: Date.now()
                    };
                }
            """)
            
            return animation_analysis
            
        except Exception as e:
            self.logger.error(f"Animation state analysis failed: {e}")
            return {
                "error": str(e),
                "total_animated_elements": 0,
                "capture_timestamp": time.time()
            }
    
    async def _capture_resource_loading_analysis(self) -> Dict[str, Any]:
        """v2.0 Enhancement: Comprehensive resource loading analysis"""
        try:
            resource_analysis = await self.page.evaluate("""
                () => {
                    // Get performance entries for all resources
                    const resourceEntries = performance.getEntriesByType('resource');
                    const navigationEntry = performance.getEntriesByType('navigation')[0];
                    
                    const resourceData = {
                        total_resources: resourceEntries.length,
                        resource_types: {},
                        loading_performance: {
                            fastest_resource: null,
                            slowest_resource: null,
                            average_load_time: 0,
                            total_transfer_size: 0,
                            total_encoded_size: 0
                        },
                        resource_details: [],
                        critical_resources: [],
                        failed_resources: []
                    };
                    
                    let totalLoadTime = 0;
                    let fastestTime = Infinity;
                    let slowestTime = 0;
                    
                    // Analyze each resource
                    resourceEntries.forEach(entry => {
                        const resourceType = entry.initiatorType || 'other';
                        const loadTime = entry.responseEnd - entry.startTime;
                        
                        // Count by type
                        resourceData.resource_types[resourceType] = (resourceData.resource_types[resourceType] || 0) + 1;
                        
                        // Performance tracking
                        totalLoadTime += loadTime;
                        if (loadTime < fastestTime) {
                            fastestTime = loadTime;
                            resourceData.loading_performance.fastest_resource = {
                                name: entry.name,
                                type: resourceType,
                                load_time: loadTime
                            };
                        }
                        if (loadTime > slowestTime) {
                            slowestTime = loadTime;
                            resourceData.loading_performance.slowest_resource = {
                                name: entry.name,
                                type: resourceType,
                                load_time: loadTime
                            };
                        }
                        
                        // Size tracking
                        resourceData.loading_performance.total_transfer_size += entry.transferSize || 0;
                        resourceData.loading_performance.total_encoded_size += entry.encodedBodySize || 0;
                        
                        // Detailed resource info
                        const resourceInfo = {
                            name: entry.name,
                            type: resourceType,
                            start_time: entry.startTime,
                            duration: loadTime,
                            transfer_size: entry.transferSize || 0,
                            encoded_size: entry.encodedBodySize || 0,
                            decoded_size: entry.decodedBodySize || 0,
                            dns_time: entry.domainLookupEnd - entry.domainLookupStart,
                            connect_time: entry.connectEnd - entry.connectStart,
                            request_time: entry.responseStart - entry.requestStart,
                            response_time: entry.responseEnd - entry.responseStart,
                            is_cached: entry.transferSize === 0 && entry.decodedBodySize > 0,
                            protocol: entry.nextHopProtocol || 'unknown'
                        };
                        
                        resourceData.resource_details.push(resourceInfo);
                        
                        // Identify critical resources (CSS, fonts, scripts in head)
                        if (['stylesheet', 'script', 'font'].includes(resourceType) || 
                            entry.name.includes('.css') || entry.name.includes('.js') || 
                            entry.name.match(/\\.(woff|woff2|ttf|otf)$/)) {
                            resourceData.critical_resources.push(resourceInfo);
                        }
                        
                        // Check for failed resources (this would need to be cross-referenced with network errors)
                        if (loadTime === 0 || entry.transferSize === 0 && entry.decodedBodySize === 0) {
                            resourceData.failed_resources.push(resourceInfo);
                        }
                    });
                    
                    // Calculate averages
                    resourceData.loading_performance.average_load_time = 
                        resourceEntries.length > 0 ? totalLoadTime / resourceEntries.length : 0;
                    
                    // Resource loading summary
                    const loadingSummary = {
                        page_load_complete: navigationEntry ? navigationEntry.loadEventEnd > 0 : false,
                        dom_content_loaded: navigationEntry ? navigationEntry.domContentLoadedEventEnd > 0 : false,
                        critical_path_loaded: resourceData.critical_resources.every(r => r.duration > 0),
                        has_failed_resources: resourceData.failed_resources.length > 0,
                        resource_efficiency: {
                            cached_resources: resourceData.resource_details.filter(r => r.is_cached).length,
                            cache_hit_rate: resourceData.resource_details.length > 0 ? 
                                (resourceData.resource_details.filter(r => r.is_cached).length / resourceData.resource_details.length * 100).toFixed(2) + '%' : '0%',
                            compression_ratio: resourceData.loading_performance.total_encoded_size > 0 ? 
                                (resourceData.loading_performance.total_transfer_size / resourceData.loading_performance.total_encoded_size).toFixed(2) : 'N/A'
                        }
                    };
                    
                    return {
                        ...resourceData,
                        loading_summary: loadingSummary,
                        capture_timestamp: Date.now()
                    };
                }
            """)
            
            return resource_analysis
            
        except Exception as e:
            self.logger.error(f"Resource loading analysis failed: {e}")
            return {
                "error": str(e),
                "total_resources": 0,
                "capture_timestamp": time.time()
            }
    
    async def _capture_storage_state(self) -> Dict[str, Any]:
        """v2.0 Enhancement: Capture browser storage state (read-only observation)"""
        try:
            storage_analysis = await self.page.evaluate("""
                () => {
                    const storageData = {
                        local_storage: {
                            available: typeof localStorage !== 'undefined',
                            item_count: 0,
                            total_size_estimate: 0,
                            keys: []
                        },
                        session_storage: {
                            available: typeof sessionStorage !== 'undefined',
                            item_count: 0,
                            total_size_estimate: 0,
                            keys: []
                        },
                        cookies: {
                            available: typeof document.cookie !== 'undefined',
                            cookie_count: 0,
                            total_size_estimate: 0,
                            cookie_names: []
                        },
                        indexed_db: {
                            available: typeof indexedDB !== 'undefined',
                            databases: []
                        }
                    };
                    
                    // Analyze localStorage
                    if (storageData.local_storage.available) {
                        try {
                            storageData.local_storage.item_count = localStorage.length;
                            for (let i = 0; i < localStorage.length; i++) {
                                const key = localStorage.key(i);
                                const value = localStorage.getItem(key);
                                storageData.local_storage.keys.push({
                                    key: key,
                                    size_estimate: (key.length + (value ? value.length : 0)) * 2 // rough UTF-16 estimate
                                });
                                storageData.local_storage.total_size_estimate += (key.length + (value ? value.length : 0)) * 2;
                            }
                        } catch (e) {
                            storageData.local_storage.error = e.message;
                        }
                    }
                    
                    // Analyze sessionStorage
                    if (storageData.session_storage.available) {
                        try {
                            storageData.session_storage.item_count = sessionStorage.length;
                            for (let i = 0; i < sessionStorage.length; i++) {
                                const key = sessionStorage.key(i);
                                const value = sessionStorage.getItem(key);
                                storageData.session_storage.keys.push({
                                    key: key,
                                    size_estimate: (key.length + (value ? value.length : 0)) * 2
                                });
                                storageData.session_storage.total_size_estimate += (key.length + (value ? value.length : 0)) * 2;
                            }
                        } catch (e) {
                            storageData.session_storage.error = e.message;
                        }
                    }
                    
                    // Analyze cookies
                    if (storageData.cookies.available) {
                        try {
                            const cookieString = document.cookie;
                            if (cookieString) {
                                const cookies = cookieString.split(';');
                                storageData.cookies.cookie_count = cookies.length;
                                storageData.cookies.total_size_estimate = cookieString.length;
                                
                                cookies.forEach(cookie => {
                                    const [name] = cookie.trim().split('=');
                                    if (name) {
                                        storageData.cookies.cookie_names.push(name);
                                    }
                                });
                            }
                        } catch (e) {
                            storageData.cookies.error = e.message;
                        }
                    }
                    
                    // IndexedDB analysis (basic availability check)
                    if (storageData.indexed_db.available) {
                        try {
                            // Note: Full IndexedDB analysis would require async operations
                            // For now, we just check availability
                            storageData.indexed_db.status = 'available_but_not_analyzed';
                            storageData.indexed_db.note = 'Full analysis requires async operations';
                        } catch (e) {
                            storageData.indexed_db.error = e.message;
                        }
                    }
                    
                    // Storage summary
                    const storageSummary = {
                        has_stored_data: storageData.local_storage.item_count > 0 || 
                                        storageData.session_storage.item_count > 0 || 
                                        storageData.cookies.cookie_count > 0,
                        total_estimated_size: storageData.local_storage.total_size_estimate + 
                                            storageData.session_storage.total_size_estimate + 
                                            storageData.cookies.total_size_estimate,
                        storage_types_used: [
                            storageData.local_storage.item_count > 0 ? 'localStorage' : null,
                            storageData.session_storage.item_count > 0 ? 'sessionStorage' : null,
                            storageData.cookies.cookie_count > 0 ? 'cookies' : null,
                            storageData.indexed_db.available ? 'indexedDB' : null
                        ].filter(Boolean),
                        privacy_indicators: {
                            has_tracking_cookies: storageData.cookies.cookie_names.some(name => 
                                ['_ga', '_gid', '_fbp', '_gat', 'utm_'].some(tracker => name.includes(tracker))),
                            has_session_data: storageData.session_storage.item_count > 0,
                            has_persistent_data: storageData.local_storage.item_count > 0
                        }
                    };
                    
                    return {
                        ...storageData,
                        storage_summary: storageSummary,
                        capture_timestamp: Date.now()
                    };
                }
            """)
            
            return storage_analysis
            
        except Exception as e:
            self.logger.error(f"Storage state analysis failed: {e}")
            return {
                "error": str(e),
                "capture_timestamp": time.time()
            }
    
    async def _capture_dom_analysis(self) -> Dict[str, Any]:
        """
        Enhanced DOM analysis with multi-selector strategies and accessibility data (v2.0)
        
        Captures ALL visible elements on the page - truly comprehensive analysis.
        No hardcoded selector limits, no artificial filtering.
        """
        try:
            dom_analysis = await self.page.evaluate("""
                () => {
                    // Enhanced helper function to generate multiple selector strategies
                    function generateMultipleSelectors(element) {
                        const selectors = {};
                        
                        // CSS selector (improved)
                        let cssSelector = element.tagName.toLowerCase();
                        if (element.id) {
                            cssSelector = '#' + element.id;
                            selectors.css = cssSelector;
                        } else if (element.className && typeof element.className === 'string') {
                            const classes = element.className.split(' ').filter(c => c.trim());
                            if (classes.length > 0) {
                                cssSelector += '.' + classes.join('.');
                                selectors.css = cssSelector;
                            }
                        } else {
                            selectors.css = cssSelector;
                        }
                        
                        // XPath selector
                        function getXPath(element) {
                            if (element.id) {
                                return `//*[@id="${element.id}"]`;
                            }
                            
                            let path = '';
                            let current = element;
                            
                            while (current && current.nodeType === Node.ELEMENT_NODE) {
                                let index = 0;
                                let sibling = current.previousSibling;
                                
                                while (sibling) {
                                    if (sibling.nodeType === Node.ELEMENT_NODE && sibling.tagName === current.tagName) {
                                        index++;
                                    }
                                    sibling = sibling.previousSibling;
                                }
                                
                                const tagName = current.tagName.toLowerCase();
                                const pathIndex = index > 0 ? `[${index + 1}]` : '';
                                path = '/' + tagName + pathIndex + path;
                                
                                current = current.parentNode;
                            }
                            
                            return path;
                        }
                        selectors.xpath = getXPath(element);
                        
                        // Text-based selector
                        const textContent = element.textContent?.trim();
                        if (textContent && textContent.length > 0 && textContent.length < 50) {
                            selectors.text = textContent;
                        }
                        
                        // Role-based selector
                        const role = element.getAttribute('role') || element.getAttribute('aria-role');
                        if (role) {
                            selectors.role = `[role="${role}"]`;
                        }
                        
                        // Test ID selectors
                        const testId = element.getAttribute('data-testid') || 
                                     element.getAttribute('data-cy') || 
                                     element.getAttribute('data-test');
                        if (testId) {
                            selectors.testid = `[data-testid="${testId}"]`;
                        }
                        
                        // ARIA label selector
                        const ariaLabel = element.getAttribute('aria-label');
                        if (ariaLabel) {
                            selectors.aria_label = `[aria-label="${ariaLabel}"]`;
                        }
                        
                        // Unique CSS selector (most specific)
                        function getUniqueSelector(element) {
                            if (element.id) return '#' + element.id;
                            
                            let path = [];
                            let current = element;
                            
                            while (current && current !== document.body) {
                                let selector = current.tagName.toLowerCase();
                                
                                if (current.className && typeof current.className === 'string') {
                                    const classes = current.className.split(' ').filter(c => c.trim());
                                    if (classes.length > 0) {
                                        selector += '.' + classes.join('.');
                                    }
                                }
                                
                                // Add nth-child if needed for uniqueness
                                const siblings = Array.from(current.parentNode?.children || [])
                                    .filter(sibling => sibling.tagName === current.tagName);
                                if (siblings.length > 1) {
                                    const index = siblings.indexOf(current) + 1;
                                    selector += `:nth-child(${index})`;
                                }
                                
                                path.unshift(selector);
                                current = current.parentElement;
                            }
                            
                            return path.join(' > ');
                        }
                        selectors.unique_css = getUniqueSelector(element);
                        
                        return selectors;
                    }
                    
                    // Phase 2.1: Event Handler Capture
                    function getEventHandlers(element) {
                        const handlers = {};
                        
                        // Common event handler attributes
                        const eventAttributes = [
                            'onclick', 'ondblclick', 'onmousedown', 'onmouseup',
                            'onmouseover', 'onmouseout', 'onmousemove', 'onmouseenter', 'onmouseleave',
                            'onkeydown', 'onkeyup', 'onkeypress',
                            'onsubmit', 'onchange', 'oninput', 'onfocus', 'onblur',
                            'onload', 'onerror', 'onabort',
                            'ontouchstart', 'ontouchend', 'ontouchmove',
                            'ondrag', 'ondrop', 'ondragover', 'ondragstart', 'ondragend'
                        ];
                        
                        eventAttributes.forEach(attr => {
                            const handler = element.getAttribute(attr);
                            if (handler) {
                                handlers[attr] = handler;
                            }
                        });
                        
                        return Object.keys(handlers).length > 0 ? handlers : null;
                    }
                    
                    // Enhanced accessibility analysis
                    function getAccessibilityData(element) {
                        return {
                            // ARIA attributes
                            role: element.getAttribute('role'),
                            aria_label: element.getAttribute('aria-label'),
                            aria_labelledby: element.getAttribute('aria-labelledby'),
                            aria_describedby: element.getAttribute('aria-describedby'),
                            aria_expanded: element.getAttribute('aria-expanded'),
                            aria_hidden: element.getAttribute('aria-hidden'),
                            aria_disabled: element.getAttribute('aria-disabled'),
                            aria_required: element.getAttribute('aria-required'),
                            aria_invalid: element.getAttribute('aria-invalid'),
                            aria_live: element.getAttribute('aria-live'),
                            
                            // Keyboard navigation
                            tabindex: element.tabIndex,
                            is_focusable: element.tabIndex >= 0 || 
                                         ['INPUT', 'BUTTON', 'SELECT', 'TEXTAREA', 'A'].includes(element.tagName),
                            
                            // Interactive element detection
                            is_interactive: ['BUTTON', 'A', 'INPUT', 'SELECT', 'TEXTAREA'].includes(element.tagName) ||
                                          element.hasAttribute('onclick') ||
                                          element.getAttribute('role') === 'button' ||
                                          element.style.cursor === 'pointer',
                            
                            // Form element specifics
                            form_label: element.tagName === 'INPUT' ? 
                                       document.querySelector(`label[for="${element.id}"]`)?.textContent?.trim() : null,
                            
                            // Semantic meaning
                            semantic_role: element.tagName.toLowerCase(),
                            landmark_role: ['HEADER', 'NAV', 'MAIN', 'ASIDE', 'FOOTER'].includes(element.tagName) ? 
                                          element.tagName.toLowerCase() : element.getAttribute('role')
                        };
                    }
                    
                    // Enhanced visual context analysis
                    function getVisualContext(element, computedStyles) {
                        const rect = element.getBoundingClientRect();
                        
                        return {
                            bounding_box: {
                                x: Math.round(rect.x),
                                y: Math.round(rect.y),
                                width: Math.round(rect.width),
                                height: Math.round(rect.height),
                                top: Math.round(rect.top),
                                left: Math.round(rect.left),
                                right: Math.round(rect.right),
                                bottom: Math.round(rect.bottom)
                            },
                            
                            // Visibility analysis
                            visibility: {
                                is_visible: rect.width > 0 && rect.height > 0 && 
                                           computedStyles.display !== 'none' && 
                                           computedStyles.visibility !== 'hidden' &&
                                           parseFloat(computedStyles.opacity) > 0,
                                is_in_viewport: rect.top < window.innerHeight && 
                                               rect.bottom > 0 && 
                                               rect.left < window.innerWidth && 
                                               rect.right > 0,
                                opacity: parseFloat(computedStyles.opacity),
                                display: computedStyles.display,
                                visibility: computedStyles.visibility
                            },
                            
                            // Z-index and layering
                            layering: {
                                z_index: computedStyles.zIndex,
                                position: computedStyles.position,
                                stacking_context: computedStyles.zIndex !== 'auto' || 
                                                 computedStyles.position === 'fixed' || 
                                                 computedStyles.position === 'sticky' ||
                                                 parseFloat(computedStyles.opacity) < 1
                            },
                            
                            // Size classification
                            size_category: rect.width === 0 || rect.height === 0 ? 'hidden' :
                                          rect.width * rect.height < 100 ? 'tiny' :
                                          rect.width * rect.height < 1000 ? 'small' :
                                          rect.width * rect.height < 10000 ? 'medium' :
                                          rect.width * rect.height < 100000 ? 'large' : 'huge',
                            
                            // Visual relationships
                            relationships: {
                                has_children: element.children.length > 0,
                                children_count: element.children.length,
                                parent_tag: element.parentElement?.tagName?.toLowerCase(),
                                siblings_count: element.parentElement?.children?.length - 1 || 0
                            }
                        };
                    }
                    
                    // Helper function to get comprehensive computed styles (enhanced)
                    function getComputedStylesDetailed(element) {
                        const computed = window.getComputedStyle(element);
                        return {
                            // Layout properties
                            display: computed.display,
                            position: computed.position,
                            top: computed.top,
                            left: computed.left,
                            right: computed.right,
                            bottom: computed.bottom,
                            width: computed.width,
                            height: computed.height,
                            minWidth: computed.minWidth,
                            maxWidth: computed.maxWidth,
                            minHeight: computed.minHeight,
                            maxHeight: computed.maxHeight,
                            
                            // Flexbox properties
                            flexDirection: computed.flexDirection,
                            flexWrap: computed.flexWrap,
                            justifyContent: computed.justifyContent,
                            alignItems: computed.alignItems,
                            alignContent: computed.alignContent,
                            flex: computed.flex,
                            flexGrow: computed.flexGrow,
                            flexShrink: computed.flexShrink,
                            flexBasis: computed.flexBasis,
                            
                            // Grid properties
                            gridTemplateColumns: computed.gridTemplateColumns,
                            gridTemplateRows: computed.gridTemplateRows,
                            gridGap: computed.gridGap,
                            gridArea: computed.gridArea,
                            gridColumn: computed.gridColumn,
                            gridRow: computed.gridRow,
                            
                            // Spacing
                            margin: computed.margin,
                            marginTop: computed.marginTop,
                            marginRight: computed.marginRight,
                            marginBottom: computed.marginBottom,
                            marginLeft: computed.marginLeft,
                            padding: computed.padding,
                            paddingTop: computed.paddingTop,
                            paddingRight: computed.paddingRight,
                            paddingBottom: computed.paddingBottom,
                            paddingLeft: computed.paddingLeft,
                            
                            // Typography
                            fontFamily: computed.fontFamily,
                            fontSize: computed.fontSize,
                            fontWeight: computed.fontWeight,
                            fontStyle: computed.fontStyle,
                            lineHeight: computed.lineHeight,
                            letterSpacing: computed.letterSpacing,
                            textAlign: computed.textAlign,
                            textDecoration: computed.textDecoration,
                            textTransform: computed.textTransform,
                            whiteSpace: computed.whiteSpace,
                            wordWrap: computed.wordWrap,
                            
                            // Colors and backgrounds
                            color: computed.color,
                            backgroundColor: computed.backgroundColor,
                            backgroundImage: computed.backgroundImage,
                            backgroundSize: computed.backgroundSize,
                            backgroundPosition: computed.backgroundPosition,
                            backgroundRepeat: computed.backgroundRepeat,
                            
                            // Borders
                            border: computed.border,
                            borderTop: computed.borderTop,
                            borderRight: computed.borderRight,
                            borderBottom: computed.borderBottom,
                            borderLeft: computed.borderLeft,
                            borderRadius: computed.borderRadius,
                            borderWidth: computed.borderWidth,
                            borderStyle: computed.borderStyle,
                            borderColor: computed.borderColor,
                            
                            // Visual effects
                            boxShadow: computed.boxShadow,
                            opacity: computed.opacity,
                            transform: computed.transform,
                            transition: computed.transition,
                            animation: computed.animation,
                            filter: computed.filter,
                            
                            // Z-index and overflow
                            zIndex: computed.zIndex,
                            overflow: computed.overflow,
                            overflowX: computed.overflowX,
                            overflowY: computed.overflowY,
                            
                            // Cursor and interaction
                            cursor: computed.cursor,
                            pointerEvents: computed.pointerEvents,
                            userSelect: computed.userSelect
                        };
                    }
                    
                    // Get ALL visible elements - truly comprehensive analysis
                    const elements = [];
                    
                    // Query EVERY element on the page (true comprehensive capture)
                    const allElements = document.querySelectorAll('*');
                    
                    allElements.forEach((element, globalIndex) => {
                        try {
                            const computedStyles = getComputedStylesDetailed(element);
                            const visualContext = getVisualContext(element, computedStyles);
                            
                            // Only include elements with meaningful size OR important semantic meaning
                            // This filters out invisible helper elements but keeps everything visible
                            if (visualContext.bounding_box.width > 0 && visualContext.bounding_box.height > 0 ||
                                ['HTML', 'BODY', 'HEAD', 'HEADER', 'NAV', 'MAIN', 'ASIDE', 'FOOTER'].includes(element.tagName)) {
                                
                                elements.push({
                                    // Basic element info
                                    index: globalIndex,
                                    tagName: element.tagName.toLowerCase(),
                                    id: element.id || null,
                                    className: element.className || null,
                                    textContent: element.textContent ? element.textContent.trim().substring(0, 200) : null,
                                        
                                        // v2.0 Enhancement: Multiple selector strategies
                                        selectors: generateMultipleSelectors(element),
                                        
                                        // v2.0 Enhancement: Accessibility data
                                        accessibility: getAccessibilityData(element),
                                        
                                        // Phase 2.1: Event Handlers
                                        event_handlers: getEventHandlers(element),
                                        
                                        // v2.0 Enhancement: Visual context
                                        visual_context: visualContext,
                                        
                                        // Enhanced computed styles
                                        computedStyles: computedStyles,
                                        
                                        // Element attributes
                                        attributes: Array.from(element.attributes).reduce((attrs, attr) => {
                                            attrs[attr.name] = attr.value;
                                            return attrs;
                                        }, {}),
                                        
                                    // Element hierarchy info
                                    childrenCount: element.children.length,
                                    parentTagName: element.parentElement ? element.parentElement.tagName.toLowerCase() : null
                                });
                            }
                        } catch (e) {
                            // Skip elements that fail to analyze (e.g., detached nodes, iframes)
                        }
                    });
                    
                    // Get page-level information
                    const pageInfo = {
                        title: document.title,
                        url: window.location.href,
                        viewport: {
                            width: window.innerWidth,
                            height: window.innerHeight
                        },
                        documentSize: {
                            width: Math.max(
                                document.body.scrollWidth || 0,
                                document.body.offsetWidth || 0,
                                document.documentElement.clientWidth || 0,
                                document.documentElement.scrollWidth || 0,
                                document.documentElement.offsetWidth || 0
                            ),
                            height: Math.max(
                                document.body.scrollHeight || 0,
                                document.body.offsetHeight || 0,
                                document.documentElement.clientHeight || 0,
                                document.documentElement.scrollHeight || 0,
                                document.documentElement.offsetHeight || 0
                            )
                        },
                        scrollPosition: {
                            x: window.pageXOffset || document.documentElement.scrollLeft || 0,
                            y: window.pageYOffset || document.documentElement.scrollTop || 0
                        }
                    };
                    
                    // Enhanced page structure analysis
                    const pageStructure = {
                        hasHeader: elements.some(el => ['header', 'nav', '.header', '.navbar'].includes(el.selector)),
                        hasFooter: elements.some(el => ['footer', '.footer'].includes(el.selector)),
                        hasNavigation: elements.some(el => ['nav', '.nav', '.navbar', '.menu'].includes(el.selector)),
                        hasSidebar: elements.some(el => ['.sidebar', '.aside', 'aside'].includes(el.selector)),
                        hasMainContent: elements.some(el => ['main', '.main', '.content'].includes(el.selector)),
                        
                        // v2.0 Enhancement: Accessibility structure
                        accessibilityFeatures: {
                            landmarkElements: elements.filter(el => el.accessibility.landmark_role).length,
                            focusableElements: elements.filter(el => el.accessibility.is_focusable).length,
                            interactiveElements: elements.filter(el => el.accessibility.is_interactive).length,
                            elementsWithAriaLabels: elements.filter(el => el.accessibility.aria_label).length,
                            elementsWithRoles: elements.filter(el => el.accessibility.role).length
                        },
                        
                        // v2.0 Enhancement: Visual structure
                        visualFeatures: {
                            visibleElements: elements.filter(el => el.visual_context.visibility.is_visible).length,
                            elementsInViewport: elements.filter(el => el.visual_context.visibility.is_in_viewport).length,
                            layeredElements: elements.filter(el => el.visual_context.layering.stacking_context).length,
                            sizeDistribution: {
                                tiny: elements.filter(el => el.visual_context.size_category === 'tiny').length,
                                small: elements.filter(el => el.visual_context.size_category === 'small').length,
                                medium: elements.filter(el => el.visual_context.size_category === 'medium').length,
                                large: elements.filter(el => el.visual_context.size_category === 'large').length,
                                huge: elements.filter(el => el.visual_context.size_category === 'huge').length
                            }
                        },
                        
                        totalVisibleElements: elements.filter(el => el.visual_context.visibility.is_visible).length,
                        totalElements: elements.length
                    };
                    
                    return {
                        pageInfo: pageInfo,
                        pageStructure: pageStructure,
                        elements: elements,
                        totalElements: elements.length,
                        captureTimestamp: Date.now(),
                        analysisVersion: "2.1"  // v2.1: Truly comprehensive (ALL elements)
                    };
                }
            """)
            
            return dom_analysis
            
        except Exception as e:
            self.logger.error(f"Enhanced DOM analysis failed: {e}")
            return {
                "error": str(e),
                "elements": [],
                "totalElements": 0,
                "captureTimestamp": time.time(),
                "analysisVersion": "2.0-error"
            }
    
    def _capture_network_data(self) -> Dict[str, Any]:
        """Capture comprehensive network request and response data"""
        try:
            # Organize network requests by type
            requests = [req for req in self.network_requests if req.get("type") == "request"]
            responses = [req for req in self.network_requests if req.get("type") == "response"]
            
            # Categorize requests
            api_requests = [req for req in requests if any(api_path in req.get("url", "") for api_path in ["/api/", "/ajax", ".json", "/graphql"])]
            static_requests = [req for req in requests if req.get("resource_type") in ["stylesheet", "script", "image", "font"]]
            navigation_requests = [req for req in requests if req.get("is_navigation_request", False)]
            
            # Analyze failed requests
            failed_requests = [req for req in responses if req.get("status", 0) >= 400]
            
            # Calculate timing statistics
            request_timings = []
            for req in requests:
                # Find matching response
                matching_response = next((resp for resp in responses if resp.get("url") == req.get("url")), None)
                if matching_response:
                    timing = matching_response.get("timestamp", 0) - req.get("timestamp", 0)
                    request_timings.append({
                        "url": req.get("url"),
                        "method": req.get("method"),
                        "timing_ms": timing * 1000,
                        "status": matching_response.get("status"),
                        "size": matching_response.get("size", 0)
                    })
            
            return {
                "total_requests": len(requests),
                "total_responses": len(responses),
                "api_requests": {
                    "count": len(api_requests),
                    "requests": api_requests
                },
                "static_requests": {
                    "count": len(static_requests),
                    "requests": static_requests
                },
                "navigation_requests": {
                    "count": len(navigation_requests),
                    "requests": navigation_requests
                },
                "failed_requests": {
                    "count": len(failed_requests),
                    "requests": failed_requests
                },
                "request_timings": request_timings,
                "network_summary": {
                    "total_requests": len(requests),
                    "successful_requests": len([r for r in responses if 200 <= r.get("status", 0) < 400]),
                    "failed_requests": len(failed_requests),
                    "average_response_time": sum(t["timing_ms"] for t in request_timings) / len(request_timings) if request_timings else 0,
                    "total_data_transferred": sum(r.get("size", 0) for r in responses)
                },
                "all_network_events": self.network_requests  # Complete raw data
            }
            
        except Exception as e:
            self.logger.error(f"Network data capture failed: {e}")
            return {"error": str(e)}
    
    def _capture_console_data(self) -> Dict[str, Any]:
        """Capture comprehensive console log data"""
        try:
            # Debug: Log console capture state
            self.logger.debug(f"Capturing console data: {len(self.console_logs)} messages in buffer")
            
            # Categorize console logs
            errors = [log for log in self.console_logs if log.get("type") == "error"]
            warnings = [log for log in self.console_logs if log.get("type") == "warning"]
            info_logs = [log for log in self.console_logs if log.get("type") in ["log", "info"]]
            debug_logs = [log for log in self.console_logs if log.get("type") == "debug"]
            
            # Analyze error patterns
            error_patterns = {}
            for error in errors:
                error_text = error.get("text", "")
                # Group similar errors
                error_key = error_text[:100]  # First 100 chars as key
                if error_key not in error_patterns:
                    error_patterns[error_key] = {
                        "count": 0,
                        "first_occurrence": error.get("timestamp"),
                        "last_occurrence": error.get("timestamp"),
                        "sample_error": error
                    }
                error_patterns[error_key]["count"] += 1
                error_patterns[error_key]["last_occurrence"] = error.get("timestamp")
            
            # Recent activity (last 30 seconds)
            current_time = time.time()
            recent_logs = [log for log in self.console_logs if current_time - log.get("timestamp", 0) <= 30]
            
            return {
                "total_console_logs": len(self.console_logs),
                "errors": {
                    "count": len(errors),
                    "logs": errors,
                    "patterns": error_patterns
                },
                "warnings": {
                    "count": len(warnings),
                    "logs": warnings
                },
                "info_logs": {
                    "count": len(info_logs),
                    "logs": info_logs
                },
                "debug_logs": {
                    "count": len(debug_logs),
                    "logs": debug_logs
                },
                "recent_activity": {
                    "count": len(recent_logs),
                    "logs": recent_logs
                },
                "console_summary": {
                    "total_logs": len(self.console_logs),
                    "error_count": len(errors),
                    "warning_count": len(warnings),
                    "unique_error_patterns": len(error_patterns),
                    "has_recent_errors": any(log.get("type") == "error" for log in recent_logs)
                },
                "all_console_logs": self.console_logs  # Complete raw data
            }
            
        except Exception as e:
            self.logger.error(f"Console data capture failed: {e}")
            return {"error": str(e)}
    
    async def _capture_performance_data(self) -> Dict[str, Any]:
        """Capture comprehensive performance metrics"""
        try:
            # Get browser performance metrics
            browser_metrics = await self.get_performance_metrics()
            
            # Get additional performance data from the page
            additional_metrics = await self.page.evaluate("""
                () => {
                    const perf = performance;
                    const navigation = perf.getEntriesByType('navigation')[0];
                    const paint = perf.getEntriesByType('paint');
                    const resources = perf.getEntriesByType('resource');
                    
                    // Helper function to safely calculate timing differences
                    const safeTiming = (end, start) => {
                        if (!end || !start || end === 0 || start === 0) return null;
                        const diff = end - start;
                        return diff >= 0 ? diff : null;
                    };
                    
                    // Memory usage (if available)
                    const memory = performance.memory ? {
                        usedJSHeapSize: performance.memory.usedJSHeapSize,
                        totalJSHeapSize: performance.memory.totalJSHeapSize,
                        jsHeapSizeLimit: performance.memory.jsHeapSizeLimit
                    } : null;
                    
                    // Resource timing summary
                    const resourceSummary = {
                        totalResources: resources.length,
                        slowestResource: resources.reduce((slowest, resource) => 
                            resource.duration > (slowest?.duration || 0) ? resource : slowest, null),
                        averageLoadTime: resources.length > 0 ? 
                            resources.reduce((sum, r) => sum + r.duration, 0) / resources.length : 0
                    };
                    
                    return {
                        navigation: navigation ? {
                            domContentLoaded: safeTiming(navigation.domContentLoadedEventEnd, navigation.domContentLoadedEventStart),
                            loadComplete: safeTiming(navigation.loadEventEnd, navigation.loadEventStart),
                            domInteractive: safeTiming(navigation.domInteractive, navigation.navigationStart),
                            domComplete: safeTiming(navigation.domComplete, navigation.navigationStart),
                            redirectTime: safeTiming(navigation.redirectEnd, navigation.redirectStart),
                            dnsTime: safeTiming(navigation.domainLookupEnd, navigation.domainLookupStart),
                            connectTime: safeTiming(navigation.connectEnd, navigation.connectStart),
                            requestTime: safeTiming(navigation.responseStart, navigation.requestStart),
                            responseTime: safeTiming(navigation.responseEnd, navigation.responseStart),
                            // Add raw values for debugging
                            _raw: {
                                navigationStart: navigation.navigationStart,
                                domContentLoadedEventStart: navigation.domContentLoadedEventStart,
                                domContentLoadedEventEnd: navigation.domContentLoadedEventEnd,
                                loadEventStart: navigation.loadEventStart,
                                loadEventEnd: navigation.loadEventEnd
                            }
                        } : {
                            domContentLoaded: null,
                            loadComplete: null,
                            domInteractive: null,
                            domComplete: null,
                            redirectTime: null,
                            dnsTime: null,
                            connectTime: null,
                            requestTime: null,
                            responseTime: null,
                            _raw: null,
                            _note: "Navigation timing not available (likely headless mode)"
                        },
                        paint: {
                            firstPaint: paint.find(p => p.name === 'first-paint')?.startTime || null,
                            firstContentfulPaint: paint.find(p => p.name === 'first-contentful-paint')?.startTime || null,
                            _available: paint.length > 0
                        },
                        memory: memory,
                        resources: {
                            summary: resourceSummary,
                            details: resources.map(r => ({
                                name: r.name,
                                duration: r.duration,
                                size: r.transferSize,
                                type: r.initiatorType
                            }))
                        },
                        timing: {
                            now: performance.now(),
                            timeOrigin: performance.timeOrigin
                        }
                    };
                }
            """)
            
            return {
                "browser_metrics": browser_metrics,
                "detailed_metrics": additional_metrics,
                "performance_summary": {
                    "page_load_time": additional_metrics.get("navigation", {}).get("loadComplete"),
                    "dom_content_loaded": additional_metrics.get("navigation", {}).get("domContentLoaded"),
                    "first_paint": additional_metrics.get("paint", {}).get("firstPaint"),
                    "first_contentful_paint": additional_metrics.get("paint", {}).get("firstContentfulPaint"),
                    "total_resources": additional_metrics.get("resources", {}).get("summary", {}).get("totalResources", 0),
                    "memory_usage_mb": additional_metrics.get("memory", {}).get("usedJSHeapSize", 0) / (1024 * 1024) if additional_metrics.get("memory") else None,
                    "_reliability": {
                        "navigation_timing_available": additional_metrics.get("navigation", {}).get("_raw") is not None,
                        "paint_timing_available": additional_metrics.get("paint", {}).get("_available", False),
                        "memory_available": additional_metrics.get("memory") is not None,
                        "note": "Some metrics may be null in headless mode - this is expected behavior"
                    }
                }
            }
            
        except Exception as e:
            self.logger.error(f"Performance data capture failed: {e}")
            return {"error": str(e)}
    
    async def _capture_page_state(self) -> Dict[str, Any]:
        """Capture current page state information"""
        try:
            page_state = await self.page.evaluate("""
                () => {
                    return {
                        url: window.location.href,
                        title: document.title,
                        readyState: document.readyState,
                        visibilityState: document.visibilityState,
                        activeElement: document.activeElement ? {
                            tagName: document.activeElement.tagName,
                            id: document.activeElement.id,
                            className: document.activeElement.className
                        } : null,
                        viewport: {
                            width: window.innerWidth,
                            height: window.innerHeight,
                            scrollX: window.scrollX,
                            scrollY: window.scrollY
                        },
                        documentSize: {
                            width: Math.max(
                                document.body.scrollWidth || 0,
                                document.body.offsetWidth || 0,
                                document.documentElement.clientWidth || 0,
                                document.documentElement.scrollWidth || 0,
                                document.documentElement.offsetWidth || 0
                            ),
                            height: Math.max(
                                document.body.scrollHeight || 0,
                                document.body.offsetHeight || 0,
                                document.documentElement.clientHeight || 0,
                                document.documentElement.scrollHeight || 0,
                                document.documentElement.offsetHeight || 0
                            )
                        },
                        userAgent: navigator.userAgent,
                        timestamp: Date.now()
                    };
                }
            """)
            
            return page_state
            
        except Exception as e:
            self.logger.error(f"Page state capture failed: {e}")
            return {"error": str(e)}
    
    def _create_analysis_summary(self, dom_analysis: Dict, network_data: Dict, console_data: Dict, performance_data: Dict,
                                font_analysis: Dict = None, animation_analysis: Dict = None, 
                                resource_analysis: Dict = None, storage_analysis: Dict = None) -> Dict[str, Any]:
        """Enhanced analysis summary with v2.0 comprehensive data"""
        try:
            # Safe value extraction with null-safety
            error_count = console_data.get("console_summary", {}).get("error_count") or 0
            failed_requests = network_data.get("failed_requests", {}).get("count") or 0
            page_load_time = performance_data.get("performance_summary", {}).get("page_load_time") or 0
            
            # Ensure numeric values are actually numeric (not None)
            if not isinstance(error_count, (int, float)):
                error_count = 0
            if not isinstance(failed_requests, (int, float)):
                failed_requests = 0
            if not isinstance(page_load_time, (int, float)):
                page_load_time = 0
            
            # Base summary (v1.x compatibility)
            summary = {
                "page_health": {
                    "dom_elements_count": dom_analysis.get("totalElements", 0),
                    "has_errors": error_count > 0,
                    "error_count": error_count,
                    "warning_count": console_data.get("console_summary", {}).get("warning_count", 0),
                    "failed_requests": network_data.get("network_summary", {}).get("failed_requests", 0),
                    "page_load_time_ms": page_load_time
                },
                "interaction_readiness": {
                    "interactive_elements": dom_analysis.get("pageStructure", {}).get("interactiveElements", 0),
                    "has_navigation": dom_analysis.get("pageStructure", {}).get("hasNavigation", False),
                    "has_main_content": dom_analysis.get("pageStructure", {}).get("hasMainContent", False),
                    "page_ready": dom_analysis.get("pageInfo", {}).get("title", "") != ""
                },
                "technical_metrics": {
                    "total_network_requests": network_data.get("network_summary", {}).get("total_requests", 0),
                    "average_response_time_ms": network_data.get("network_summary", {}).get("average_response_time", 0),
                    "memory_usage_mb": performance_data.get("performance_summary", {}).get("memory_usage_mb"),
                    "first_contentful_paint_ms": performance_data.get("performance_summary", {}).get("first_contentful_paint", 0)
                },
                "quality_indicators": {
                    "has_console_errors": console_data.get("console_summary", {}).get("has_recent_errors", False),
                    "has_failed_requests": failed_requests > 0,
                    "performance_score": self._calculate_performance_score(performance_data),
                    "overall_health": "good" if (
                        error_count == 0 and
                        failed_requests == 0 and
                        page_load_time < 3000
                    ) else "needs_attention"
                }
            }
            
            # v2.0 Enhancements
            if font_analysis:
                summary["font_status"] = {
                    "fonts_loaded": font_analysis.get("font_status", {}).get("loaded_fonts", 0),
                    "fonts_loading": font_analysis.get("font_status", {}).get("loading_fonts", 0),
                    "fonts_failed": font_analysis.get("font_status", {}).get("failed_fonts", 0),
                    "loading_complete": font_analysis.get("loading_metrics", {}).get("loading_complete", False),
                    "load_success_rate": font_analysis.get("loading_metrics", {}).get("load_success_rate", "100%"),
                    "used_font_families_count": len(font_analysis.get("used_font_families", []))
                }
            
            if animation_analysis:
                summary["animation_status"] = {
                    "animated_elements": animation_analysis.get("total_animated_elements", 0),
                    "running_animations": animation_analysis.get("running_animations", 0),
                    "running_transitions": animation_analysis.get("running_transitions", 0),
                    "has_active_animations": animation_analysis.get("animation_summary", {}).get("has_active_animations", False),
                    "performance_impact": animation_analysis.get("animation_summary", {}).get("performance_impact", "low"),
                    "animation_stability": animation_analysis.get("animation_summary", {}).get("animation_stability", "stable")
                }
            
            if resource_analysis:
                summary["resource_status"] = {
                    "total_resources": resource_analysis.get("total_resources", 0),
                    "critical_resources": len(resource_analysis.get("critical_resources", [])),
                    "failed_resources": len(resource_analysis.get("failed_resources", [])),
                    "average_load_time_ms": resource_analysis.get("loading_performance", {}).get("average_load_time", 0),
                    "cache_hit_rate": resource_analysis.get("loading_summary", {}).get("resource_efficiency", {}).get("cache_hit_rate", "0%"),
                    "page_load_complete": resource_analysis.get("loading_summary", {}).get("page_load_complete", False),
                    "critical_path_loaded": resource_analysis.get("loading_summary", {}).get("critical_path_loaded", False)
                }
            
            if storage_analysis:
                summary["storage_status"] = {
                    "has_stored_data": storage_analysis.get("storage_summary", {}).get("has_stored_data", False),
                    "storage_types_used": storage_analysis.get("storage_summary", {}).get("storage_types_used", []),
                    "total_estimated_size_bytes": storage_analysis.get("storage_summary", {}).get("total_estimated_size", 0),
                    "has_tracking_cookies": storage_analysis.get("storage_summary", {}).get("privacy_indicators", {}).get("has_tracking_cookies", False),
                    "has_session_data": storage_analysis.get("storage_summary", {}).get("privacy_indicators", {}).get("has_session_data", False),
                    "has_persistent_data": storage_analysis.get("storage_summary", {}).get("privacy_indicators", {}).get("has_persistent_data", False)
                }
            
            # v2.0 Enhanced accessibility summary
            if dom_analysis.get("pageStructure", {}).get("accessibilityFeatures"):
                summary["accessibility_status"] = {
                    "landmark_elements": dom_analysis.get("pageStructure", {}).get("accessibilityFeatures", {}).get("landmarkElements", 0),
                    "focusable_elements": dom_analysis.get("pageStructure", {}).get("accessibilityFeatures", {}).get("focusableElements", 0),
                    "interactive_elements": dom_analysis.get("pageStructure", {}).get("accessibilityFeatures", {}).get("interactiveElements", 0),
                    "elements_with_aria_labels": dom_analysis.get("pageStructure", {}).get("accessibilityFeatures", {}).get("elementsWithAriaLabels", 0),
                    "elements_with_roles": dom_analysis.get("pageStructure", {}).get("accessibilityFeatures", {}).get("elementsWithRoles", 0),
                    "accessibility_score": self._calculate_accessibility_score(dom_analysis)
                }
            
            # v2.0 Enhanced visual summary
            if dom_analysis.get("pageStructure", {}).get("visualFeatures"):
                summary["visual_status"] = {
                    "visible_elements": dom_analysis.get("pageStructure", {}).get("visualFeatures", {}).get("visibleElements", 0),
                    "elements_in_viewport": dom_analysis.get("pageStructure", {}).get("visualFeatures", {}).get("elementsInViewport", 0),
                    "layered_elements": dom_analysis.get("pageStructure", {}).get("visualFeatures", {}).get("layeredElements", 0),
                    "size_distribution": dom_analysis.get("pageStructure", {}).get("visualFeatures", {}).get("sizeDistribution", {}),
                    "viewport_utilization": self._calculate_viewport_utilization(dom_analysis)
                }
            
            return summary
            
        except Exception as e:
            self.logger.error(f"Enhanced analysis summary creation failed: {e}")
            return {"error": str(e)}
    
    def _calculate_performance_score(self, performance_data: Dict) -> int:
        """Calculate a simple performance score (0-100)"""
        try:
            score = 100
            
            # Deduct points for slow loading
            load_time = performance_data.get("performance_summary", {}).get("page_load_time", 0)
            if load_time > 3000:
                score -= 30
            elif load_time > 1000:
                score -= 15
            
            # Deduct points for slow first contentful paint
            fcp = performance_data.get("performance_summary", {}).get("first_contentful_paint", 0)
            if fcp > 2000:
                score -= 20
            elif fcp > 1000:
                score -= 10
            
            # Deduct points for high memory usage
            memory_mb = performance_data.get("performance_summary", {}).get("memory_usage_mb")
            if memory_mb and memory_mb > 100:
                score -= 20
            elif memory_mb and memory_mb > 50:
                score -= 10
            
            return max(0, score)
            
        except Exception as e:
            return 50  # Default middle score if calculation fails
    
    def _calculate_accessibility_score(self, dom_analysis: Dict) -> int:
        """v2.0 Enhancement: Calculate accessibility compliance score (0-100)"""
        try:
            score = 100
            accessibility_features = dom_analysis.get("pageStructure", {}).get("accessibilityFeatures", {})
            total_elements = dom_analysis.get("totalElements", 1)  # Avoid division by zero
            
            # Deduct points for missing accessibility features
            landmark_elements = accessibility_features.get("landmarkElements", 0)
            if landmark_elements == 0:
                score -= 20  # No semantic landmarks
            
            focusable_elements = accessibility_features.get("focusableElements", 0)
            interactive_elements = accessibility_features.get("interactiveElements", 0)
            if interactive_elements > 0 and focusable_elements == 0:
                score -= 30  # Interactive elements but none focusable
            
            elements_with_aria_labels = accessibility_features.get("elementsWithAriaLabels", 0)
            if interactive_elements > 0 and elements_with_aria_labels == 0:
                score -= 25  # Interactive elements without ARIA labels
            
            elements_with_roles = accessibility_features.get("elementsWithRoles", 0)
            role_coverage = elements_with_roles / total_elements if total_elements > 0 else 0
            if role_coverage < 0.1:  # Less than 10% of elements have roles
                score -= 15
            
            # Bonus points for good accessibility practices
            if landmark_elements > 3:  # Good semantic structure
                score += 5
            if role_coverage > 0.5:  # Excellent role coverage
                score += 5
            
            return max(0, min(100, score))
            
        except Exception as e:
            self.logger.error(f"Accessibility score calculation failed: {e}")
            return 50  # Default middle score
    
    def _calculate_viewport_utilization(self, dom_analysis: Dict) -> Dict[str, Any]:
        """v2.0 Enhancement: Calculate how well the viewport is utilized"""
        try:
            visual_features = dom_analysis.get("pageStructure", {}).get("visualFeatures", {})
            page_info = dom_analysis.get("pageInfo", {})
            
            visible_elements = visual_features.get("visibleElements", 0)
            elements_in_viewport = visual_features.get("elementsInViewport", 0)
            viewport_height = page_info.get("viewport", {}).get("height", 1)  # Avoid division by zero
            document_height = page_info.get("documentSize", {}).get("height", viewport_height)
            
            # Calculate utilization metrics
            viewport_fill_ratio = elements_in_viewport / visible_elements if visible_elements > 0 else 0
            content_density = visible_elements / viewport_height * 1000 if viewport_height > 0 else 0  # Elements per 1000px
            scroll_ratio = document_height / viewport_height if viewport_height > 0 else 1
            
            # Determine utilization quality
            utilization_quality = "excellent" if viewport_fill_ratio > 0.8 and content_density > 2 else \
                                 "good" if viewport_fill_ratio > 0.6 and content_density > 1 else \
                                 "fair" if viewport_fill_ratio > 0.4 else "poor"
            
            return {
                "viewport_fill_ratio": round(viewport_fill_ratio, 2),
                "content_density_per_1000px": round(content_density, 1),
                "scroll_ratio": round(scroll_ratio, 1),
                "utilization_quality": utilization_quality,
                "elements_in_viewport": elements_in_viewport,
                "total_visible_elements": visible_elements
            }
            
        except Exception as e:
            self.logger.error(f"Viewport utilization calculation failed: {e}")
            return {
                "viewport_fill_ratio": 0.5,
                "content_density_per_1000px": 1.0,
                "scroll_ratio": 1.0,
                "utilization_quality": "unknown",
                "elements_in_viewport": 0,
                "total_visible_elements": 0
            }

    def get_collected_data(self) -> Dict:
        """Get all collected browser data"""
        return {
            "console_logs": self.console_logs,
            "network_requests": self.network_requests,
            "performance_metrics": self.performance_metrics,
            "console_errors": self.get_console_errors(),
            "failed_requests": self.get_failed_requests(),
            "summary": {
                "total_console_logs": len(self.console_logs),
                "total_errors": len(self.get_console_errors()),
                "total_requests": len([r for r in self.network_requests if r.get("type") == "request"]),
                "failed_requests": len(self.get_failed_requests())
            }
        }
    
    # v2.0 Enhancement: Hot Reload Intelligence Methods
    
    async def start_hmr_monitoring(self) -> Dict[str, Any]:
        """
        Start Hot Module Replacement monitoring for precision CSS iteration
        
        This enables the breakthrough v2.0 feature: precise timing instead of arbitrary waits
        
        Returns:
            Status dict with framework detection and monitoring state
        """
        try:
            self.logger.info("🔥 Starting Hot Reload Intelligence monitoring...")
            
            # Auto-detect framework
            detected_framework = await self.hmr_detector.auto_detect_framework()
            
            if detected_framework:
                # Start monitoring
                success = await self.hmr_detector.start_monitoring()
                
                if success:
                    self.hmr_monitoring_active = True
                    framework_info = self.hmr_detector.get_framework_info()
                    
                    self.logger.info(f"✅ HMR monitoring active for {framework_info['name']}")
                    
                    return {
                        'success': True,
                        'framework_detected': True,
                        'framework': framework_info,
                        'monitoring_active': True,
                        'message': f"Hot reload monitoring started for {framework_info['name']}"
                    }
                else:
                    return {
                        'success': False,
                        'framework_detected': True,
                        'framework': self.hmr_detector.get_framework_info(),
                        'monitoring_active': False,
                        'message': 'Framework detected but monitoring failed to start'
                    }
            else:
                return {
                    'success': False,
                    'framework_detected': False,
                    'framework': None,
                    'monitoring_active': False,
                    'message': 'No HMR framework detected - using fallback timing',
                    'supported_frameworks': ['Vite', 'Webpack Dev Server', 'Next.js', 'Parcel', 'Laravel Mix']
                }
                
        except Exception as e:
            self.logger.error(f"HMR monitoring startup failed: {e}")
            return {
                'success': False,
                'framework_detected': False,
                'framework': None,
                'monitoring_active': False,
                'error': str(e),
                'message': 'HMR monitoring failed to start'
            }
    
    async def wait_for_css_update(self, timeout: float = 10.0) -> Dict[str, Any]:
        """
        Wait for CSS update with precision timing - the key v2.0 breakthrough method
        
        This replaces arbitrary waits with precise HMR event detection:
        
        OLD WAY (unreliable):
        await page.screenshot("before.png")
        # ... developer makes CSS changes ...
        await page.wait_for_timeout(2000)  # Arbitrary wait - too short or too long
        await page.screenshot("after.png")
        
        NEW WAY (precise):
        await page.screenshot("before.png") 
        # ... developer makes CSS changes ...
        result = await browser_controller.wait_for_css_update()  # Exact timing
        await page.screenshot("after.png")
        
        Args:
            timeout: Maximum time to wait for CSS update (seconds)
            
        Returns:
            Dict with timing results and HMR event data
        """
        if not self.hmr_monitoring_active:
            # Fallback to traditional wait with warning
            self.logger.warning("⚠️  HMR monitoring not active - using fallback timing")
            await asyncio.sleep(2.0)  # Default fallback wait
            return {
                'method': 'fallback_timing',
                'wait_time': 2.0,
                'hmr_event': None,
                'precision_timing': False,
                'message': 'Used fallback timing - consider starting HMR monitoring for precision'
            }
        
        start_time = time.time()
        hmr_event = await self.hmr_detector.wait_for_css_update(timeout)
        actual_wait_time = time.time() - start_time
        
        if hmr_event:
            self.logger.info(f"✅ CSS update detected after {actual_wait_time:.2f}s - precision timing achieved")
            return {
                'method': 'hmr_precision_timing',
                'wait_time': actual_wait_time,
                'hmr_event': hmr_event,
                'precision_timing': True,
                'framework': hmr_event['framework'],
                'event_type': hmr_event['event_type'],
                'message': f"CSS update detected via {hmr_event['framework']} HMR"
            }
        else:
            self.logger.warning(f"⏰ CSS update timeout after {timeout}s - no HMR event detected")
            return {
                'method': 'hmr_timeout',
                'wait_time': actual_wait_time,
                'hmr_event': None,
                'precision_timing': False,
                'timeout': timeout,
                'message': f'No CSS update detected within {timeout}s timeout'
            }
    
    def get_hmr_status(self) -> Dict[str, Any]:
        """Get current Hot Reload Intelligence status"""
        base_status = {
            'hmr_monitoring_active': self.hmr_monitoring_active,
            'browser_controller_ready': self.page is not None
        }
        
        if hasattr(self, 'hmr_detector'):
            hmr_status = self.hmr_detector.get_hmr_status()
            framework_info = self.hmr_detector.get_framework_info()
            
            return {
                **base_status,
                **hmr_status,
                'framework_info': framework_info,
                'capabilities': {
                    'precision_css_timing': self.hmr_monitoring_active,
                    'build_completion_detection': self.hmr_monitoring_active,
                    'framework_auto_detection': True,
                    'supported_frameworks': ['Vite', 'Webpack Dev Server', 'Next.js', 'Parcel', 'Laravel Mix']
                }
            }
        else:
            return {
                **base_status,
                'error': 'HMR detector not initialized'
            }
    
    async def stop_hmr_monitoring(self):
        """Stop Hot Reload Intelligence monitoring"""
        if hasattr(self, 'hmr_detector') and self.hmr_monitoring_active:
            await self.hmr_detector.stop_monitoring()
            self.hmr_monitoring_active = False
            self.logger.info("🔥 Hot Reload Intelligence monitoring stopped")
    
    # v2.0 Enhancement: Error Context Collection Methods
    
    async def _collect_error_context_async(self, error_event: Dict[str, Any]):
        """Asynchronously collect error context without blocking event handlers"""
        try:
            if self.error_context_collector:
                context_data = await self.error_context_collector.capture_error_context(error_event)
                self.logger.debug(f"📊 Error context collected for {error_event.get('type')}")
        except Exception as e:
            self.logger.error(f"Error context collection failed: {e}")
    
    def record_browser_action(self, action_type: str, details: Dict = None):
        """Record browser action for error correlation"""
        if self.error_context_collector:
            self.error_context_collector.record_action(action_type, details)
    
    async def capture_interaction_error_context(self, action: str, target: str, error: Exception) -> Dict[str, Any]:
        """Capture context for interaction failures (clicks, fills, etc.)"""
        if not self.error_context_collector:
            return {'error': 'Error context collector not initialized'}
        
        error_event = {
            'type': 'interaction_error',
            'action': action,
            'target': target,
            'error_message': str(error),
            'selector': target,
            'timestamp': time.time()
        }
        
        return await self.error_context_collector.capture_error_context(error_event)
    
    def get_error_context_summary(self) -> Dict[str, Any]:
        """Get summary of collected error contexts"""
        if not self.error_context_collector:
            return {'error': 'Error context collector not initialized'}
        
        return self.error_context_collector.get_error_context_summary()
