"""
CursorFlow v2.0 Enhanced Error Context Collection System

This module provides intelligent error context data collection with smart
screenshot deduplication, maintaining our core philosophy of pure data
collection without analysis or recommendations.

Core Philosophy: Collect more error context data, collect it better,
but never analyze what the errors mean - that's the AI's job.
"""

import asyncio
import hashlib
import json
import logging
import time
from pathlib import Path
from typing import Dict, List, Optional, Any


class ErrorContextCollector:
    """
    v2.0 Enhancement: Intelligent error context data collection
    
    Collects comprehensive error context data while avoiding duplicate
    screenshots and maintaining efficient artifact management.
    """
    
    def __init__(self, page, logger: logging.Logger):
        self.page = page
        self.logger = logger
        
        # Smart screenshot deduplication
        self.recent_screenshots = {}  # timestamp -> screenshot_info
        self.content_hash_to_screenshot = {}  # content_hash -> screenshot_path
        self.screenshot_dedup_window = 5.0  # 5 seconds
        
        # Error context tracking
        self.error_contexts = []
        self.recent_actions = []
        
        # Ensure diagnostics directory exists
        diagnostics_dir = Path(".cursorflow/artifacts/diagnostics")
        diagnostics_dir.mkdir(parents=True, exist_ok=True)
    
    async def capture_error_context(self, error_event: Dict[str, Any]) -> Dict[str, Any]:
        """
        Capture comprehensive error context data with smart deduplication
        
        Args:
            error_event: The error event that triggered context collection
            
        Returns:
            Complete error context data for AI analysis
        """
        try:
            current_time = time.time()
            
            # Capture screenshot with smart deduplication
            screenshot_info = await self._capture_smart_screenshot(current_time, error_event)
            
            # Capture comprehensive context data
            context_data = {
                'error_timestamp': current_time,
                'error_details': error_event,
                'screenshot_info': screenshot_info,
                
                # DOM state at error time
                'dom_snapshot': await self._capture_error_dom_snapshot(),
                
                # Page state information
                'page_state': await self._capture_error_page_state(),
                
                # Console context (last 10 messages)
                'console_context': await self._capture_console_context(),
                
                # Network context (last 20 requests)
                'network_context': await self._capture_network_context(),
                
                # Recent browser actions
                'action_context': self._capture_action_context(current_time),
                
                # Element visibility and interaction state
                'element_context': await self._capture_element_context(error_event),
                
                # Performance state at error time
                'performance_context': await self._capture_performance_context(),
                
                # Browser environment context
                'environment_context': await self._capture_environment_context(),
                
                # Error correlation data
                'correlation_context': self._capture_correlation_context(current_time, error_event)
            }
            
            # Store context for potential correlation with future errors
            self.error_contexts.append(context_data)
            
            # Keep only last 50 error contexts to prevent memory issues
            if len(self.error_contexts) > 50:
                self.error_contexts = self.error_contexts[-50:]
            
            self.logger.info(f"📊 Error context captured: {error_event.get('type', 'unknown')} at {current_time}")
            
            return context_data
            
        except Exception as e:
            self.logger.error(f"Error context capture failed: {e}")
            return {
                'error_timestamp': time.time(),
                'error_details': error_event,
                'context_capture_error': str(e),
                'partial_data': True
            }
    
    async def _capture_smart_screenshot(self, current_time: float, error_event: Dict) -> Dict[str, Any]:
        """Capture screenshot with intelligent deduplication"""
        try:
            # Check if we should capture a new screenshot based on error type
            if not self._should_capture_screenshot_for_error(error_event):
                return {
                    'screenshot_captured': False,
                    'reason': f"Error type '{error_event.get('type')}' typically doesn't require visual context",
                    'screenshot_path': None
                }
            
            # Check for reusable recent screenshot
            reusable_screenshot = self._find_reusable_screenshot(current_time)
            
            if reusable_screenshot:
                # Reuse existing screenshot
                self.recent_screenshots[reusable_screenshot['timestamp']]['error_count'] += 1
                
                return {
                    'screenshot_path': reusable_screenshot['path'],
                    'screenshot_timestamp': reusable_screenshot['timestamp'],
                    'shared_with_errors': reusable_screenshot['error_count'] + 1,
                    'is_reused': True,
                    'reuse_reason': 'Recent screenshot within deduplication window'
                }
            
            # Check for content-based deduplication
            content_hash = await self._generate_content_hash()
            if content_hash in self.content_hash_to_screenshot:
                return {
                    'screenshot_path': self.content_hash_to_screenshot[content_hash],
                    'is_content_duplicate': True,
                    'content_hash': content_hash,
                    'reuse_reason': 'Identical page content detected'
                }
            
            # Capture new screenshot
            screenshot_filename = f"error_context_{int(current_time)}.png"
            screenshot_path = f".cursorflow/artifacts/diagnostics/{screenshot_filename}"
            
            await self.page.screenshot(path=screenshot_path, full_page=True)
            
            screenshot_info = {
                'screenshot_path': screenshot_path,
                'screenshot_timestamp': current_time,
                'shared_with_errors': 1,
                'is_reused': False,
                'content_hash': content_hash,
                'full_page': True
            }
            
            # Store for potential reuse
            self.recent_screenshots[current_time] = {
                'path': screenshot_path,
                'timestamp': current_time,
                'error_count': 1
            }
            self.content_hash_to_screenshot[content_hash] = screenshot_path
            
            # Clean up old references
            self._cleanup_old_screenshot_refs(current_time)
            
            return screenshot_info
            
        except Exception as e:
            self.logger.error(f"Screenshot capture failed: {e}")
            return {
                'screenshot_captured': False,
                'error': str(e),
                'screenshot_path': None
            }
    
    def _should_capture_screenshot_for_error(self, error_event: Dict) -> bool:
        """Determine if this error type needs visual context"""
        error_type = error_event.get('type', 'unknown')
        
        # Visual/interaction errors always need screenshots
        visual_error_types = [
            'selector_failed',
            'click_failed', 
            'element_not_visible',
            'layout_shift',
            'css_error',
            'render_error'
        ]
        
        if error_type in visual_error_types:
            return True
        
        # Console errors might need screenshots if they're UI-related
        if error_type == 'console_error':
            error_message = error_event.get('message', '').lower()
            ui_related_keywords = ['element', 'dom', 'css', 'style', 'render', 'layout']
            return any(keyword in error_message for keyword in ui_related_keywords)
        
        # Network errors typically don't need screenshots
        if error_type == 'network_error':
            return False
        
        # Default: capture screenshot for unknown error types
        return True
    
    def _find_reusable_screenshot(self, current_time: float) -> Optional[Dict]:
        """Find a recent screenshot that can be reused"""
        for timestamp, screenshot_data in self.recent_screenshots.items():
            if current_time - timestamp <= self.screenshot_dedup_window:
                return screenshot_data
        return None
    
    async def _generate_content_hash(self) -> str:
        """Generate a hash of current page content for deduplication"""
        try:
            content_fingerprint = await self.page.evaluate("""
                () => {
                    const body = document.body;
                    if (!body) return 'no-body';
                    
                    // Create content fingerprint from key page characteristics
                    const fingerprint = {
                        text_sample: body.innerText.substring(0, 1000),
                        element_count: body.querySelectorAll('*').length,
                        viewport: window.innerWidth + 'x' + window.innerHeight,
                        url: window.location.href,
                        title: document.title
                    };
                    
                    return JSON.stringify(fingerprint);
                }
            """)
            
            # Create hash from fingerprint
            return hashlib.md5(content_fingerprint.encode()).hexdigest()[:16]
            
        except Exception as e:
            self.logger.error(f"Content hash generation failed: {e}")
            return f"hash_error_{int(time.time())}"
    
    def _cleanup_old_screenshot_refs(self, current_time: float):
        """Remove old screenshot references outside the dedup window"""
        expired_timestamps = [
            ts for ts in self.recent_screenshots.keys() 
            if current_time - ts > self.screenshot_dedup_window
        ]
        for ts in expired_timestamps:
            del self.recent_screenshots[ts]
        
        # Also cleanup content hash references (keep last 20)
        if len(self.content_hash_to_screenshot) > 20:
            # Remove oldest entries
            sorted_items = sorted(self.content_hash_to_screenshot.items())
            items_to_keep = sorted_items[-20:]
            self.content_hash_to_screenshot = dict(items_to_keep)
    
    async def _capture_error_dom_snapshot(self) -> Dict[str, Any]:
        """Capture DOM state at error time"""
        try:
            dom_snapshot = await self.page.evaluate("""
                () => {
                    // Capture essential DOM state information
                    const snapshot = {
                        document_ready_state: document.readyState,
                        active_element: document.activeElement ? {
                            tag_name: document.activeElement.tagName.toLowerCase(),
                            id: document.activeElement.id,
                            class_name: document.activeElement.className
                        } : null,
                        visible_elements_count: document.querySelectorAll('*').length,
                        interactive_elements: Array.from(document.querySelectorAll('button, a, input, select, textarea')).map(el => ({
                            tag_name: el.tagName.toLowerCase(),
                            id: el.id,
                            class_name: el.className,
                            visible: el.offsetWidth > 0 && el.offsetHeight > 0,
                            disabled: el.disabled
                        })),
                        forms_data: Array.from(document.forms).map(form => ({
                            id: form.id,
                            name: form.name,
                            method: form.method,
                            action: form.action,
                            elements_count: form.elements.length
                        })),
                        scripts_count: document.scripts.length,
                        stylesheets_count: document.styleSheets.length
                    };
                    
                    return snapshot;
                }
            """)
            
            return dom_snapshot
            
        except Exception as e:
            self.logger.error(f"DOM snapshot capture failed: {e}")
            return {'error': str(e)}
    
    async def _capture_error_page_state(self) -> Dict[str, Any]:
        """Capture page state at error time"""
        try:
            page_state = await self.page.evaluate("""
                () => {
                    return {
                        url: window.location.href,
                        title: document.title,
                        ready_state: document.readyState,
                        visibility_state: document.visibilityState,
                        viewport: {
                            width: window.innerWidth,
                            height: window.innerHeight
                        },
                        scroll_position: {
                            x: window.pageXOffset,
                            y: window.pageYOffset
                        },
                        document_size: {
                            width: Math.max(
                                document.body.scrollWidth,
                                document.body.offsetWidth,
                                document.documentElement.clientWidth,
                                document.documentElement.scrollWidth,
                                document.documentElement.offsetWidth
                            ),
                            height: Math.max(
                                document.body.scrollHeight,
                                document.body.offsetHeight,
                                document.documentElement.clientHeight,
                                document.documentElement.scrollHeight,
                                document.documentElement.offsetHeight
                            )
                        },
                        user_agent: navigator.userAgent,
                        timestamp: Date.now()
                    };
                }
            """)
            
            return page_state
            
        except Exception as e:
            self.logger.error(f"Page state capture failed: {e}")
            return {'error': str(e)}
    
    async def _capture_console_context(self) -> List[Dict]:
        """Capture recent console messages for context"""
        # Get console logs from BrowserController (last 10 messages)
        try:
            # This will be populated via integration - for now return empty
            # The BrowserController will pass console_logs when initializing
            return getattr(self, '_console_logs_ref', [])[-10:]
        except Exception:
            return []
    
    async def _capture_network_context(self) -> List[Dict]:
        """Capture recent network requests for context"""
        # Get network requests from BrowserController (last 20 requests)
        try:
            # This will be populated via integration - for now return empty
            # The BrowserController will pass network_requests when initializing
            return getattr(self, '_network_requests_ref', [])[-20:]
        except Exception:
            return []
    
    def set_browser_data_references(self, console_logs: List[Dict], network_requests: List[Dict]):
        """Set references to browser data from BrowserController"""
        self._console_logs_ref = console_logs
        self._network_requests_ref = network_requests
    
    def _capture_action_context(self, error_time: float) -> List[Dict]:
        """Capture recent browser actions that might be related to the error"""
        # Get actions from the last 30 seconds
        recent_actions = [
            action for action in self.recent_actions 
            if error_time - action.get('timestamp', 0) <= 30.0
        ]
        
        return recent_actions[-10:]  # Last 10 actions
    
    async def _capture_element_context(self, error_event: Dict) -> Dict[str, Any]:
        """Capture element-specific context if the error is element-related"""
        try:
            # If error involves a specific element/selector
            selector = error_event.get('selector') or error_event.get('element')
            
            if not selector:
                return {'no_element_context': True}
            
            element_context = await self.page.evaluate(f"""
                (selector) => {{
                    try {{
                        const element = document.querySelector(selector);
                        
                        if (!element) {{
                            // Element not found - get similar elements
                            const allElements = Array.from(document.querySelectorAll('*'));
                            const similarElements = allElements.filter(el => {{
                                return el.id.includes(selector.replace('#', '').replace('.', '')) ||
                                       el.className.includes(selector.replace('#', '').replace('.', ''));
                            }}).slice(0, 5);
                            
                            return {{
                                element_found: false,
                                selector: selector,
                                similar_elements: similarElements.map(el => ({{
                                    tag_name: el.tagName.toLowerCase(),
                                    id: el.id,
                                    class_name: el.className,
                                    text_content: el.textContent ? el.textContent.trim().substring(0, 50) : null
                                }}))
                            }};
                        }}
                        
                        // Element found - get detailed info
                        const rect = element.getBoundingClientRect();
                        const computedStyle = window.getComputedStyle(element);
                        
                        return {{
                            element_found: true,
                            selector: selector,
                            element_info: {{
                                tag_name: element.tagName.toLowerCase(),
                                id: element.id,
                                class_name: element.className,
                                text_content: element.textContent ? element.textContent.trim().substring(0, 100) : null,
                                bounding_box: {{
                                    x: Math.round(rect.x),
                                    y: Math.round(rect.y),
                                    width: Math.round(rect.width),
                                    height: Math.round(rect.height)
                                }},
                                visibility: {{
                                    is_visible: rect.width > 0 && rect.height > 0,
                                    display: computedStyle.display,
                                    visibility: computedStyle.visibility,
                                    opacity: computedStyle.opacity
                                }},
                                interaction_state: {{
                                    disabled: element.disabled,
                                    readonly: element.readOnly,
                                    focusable: element.tabIndex >= 0
                                }}
                            }}
                        }};
                    }} catch (e) {{
                        return {{
                            element_context_error: e.message,
                            selector: selector
                        }};
                    }}
                }}
            """, selector)
            
            return element_context
            
        except Exception as e:
            self.logger.error(f"Element context capture failed: {e}")
            return {'error': str(e)}
    
    async def _capture_performance_context(self) -> Dict[str, Any]:
        """Capture performance state at error time"""
        try:
            performance_context = await self.page.evaluate("""
                () => {
                    const performance = window.performance;
                    const navigation = performance.getEntriesByType('navigation')[0];
                    
                    return {
                        timing: {
                            dom_content_loaded: navigation ? navigation.domContentLoadedEventEnd - navigation.domContentLoadedEventStart : null,
                            load_complete: navigation ? navigation.loadEventEnd - navigation.loadEventStart : null
                        },
                        memory: performance.memory ? {
                            used_js_heap_size: performance.memory.usedJSHeapSize,
                            total_js_heap_size: performance.memory.totalJSHeapSize,
                            js_heap_size_limit: performance.memory.jsHeapSizeLimit
                        } : null,
                        resource_count: performance.getEntriesByType('resource').length,
                        timestamp: performance.now()
                    };
                }
            """)
            
            return performance_context
            
        except Exception as e:
            self.logger.error(f"Performance context capture failed: {e}")
            return {'error': str(e)}
    
    async def _capture_environment_context(self) -> Dict[str, Any]:
        """Capture browser environment context"""
        try:
            environment_context = await self.page.evaluate("""
                () => {
                    return {
                        user_agent: navigator.userAgent,
                        platform: navigator.platform,
                        language: navigator.language,
                        cookie_enabled: navigator.cookieEnabled,
                        online: navigator.onLine,
                        connection: navigator.connection ? {
                            effective_type: navigator.connection.effectiveType,
                            downlink: navigator.connection.downlink,
                            rtt: navigator.connection.rtt
                        } : null,
                        screen: {
                            width: screen.width,
                            height: screen.height,
                            color_depth: screen.colorDepth
                        },
                        timezone_offset: new Date().getTimezoneOffset()
                    };
                }
            """)
            
            return environment_context
            
        except Exception as e:
            self.logger.error(f"Environment context capture failed: {e}")
            return {'error': str(e)}
    
    def _capture_correlation_context(self, error_time: float, error_event: Dict) -> Dict[str, Any]:
        """Capture data for correlating this error with other events"""
        
        # Find recent errors for pattern detection
        recent_errors = [
            ctx for ctx in self.error_contexts 
            if error_time - ctx.get('error_timestamp', 0) <= 60.0  # Last minute
        ]
        
        # Find errors of the same type
        same_type_errors = [
            ctx for ctx in recent_errors 
            if ctx.get('error_details', {}).get('type') == error_event.get('type')
        ]
        
        return {
            'recent_errors_count': len(recent_errors),
            'same_type_errors_count': len(same_type_errors),
            'error_frequency': len(recent_errors) / 60.0 if recent_errors else 0,  # errors per second
            'time_since_last_error': min([
                error_time - ctx.get('error_timestamp', 0) 
                for ctx in recent_errors
            ]) if recent_errors else None,
            'error_pattern_detected': len(same_type_errors) >= 3  # 3+ similar errors indicate pattern
        }
    
    def record_action(self, action_type: str, details: Dict = None):
        """Record a browser action for context correlation"""
        action_record = {
            'timestamp': time.time(),
            'action_type': action_type,
            'details': details or {}
        }
        
        self.recent_actions.append(action_record)
        
        # Keep only last 100 actions to prevent memory issues
        if len(self.recent_actions) > 100:
            self.recent_actions = self.recent_actions[-100:]
    
    def get_error_context_summary(self) -> Dict[str, Any]:
        """Get summary of collected error contexts"""
        if not self.error_contexts:
            return {'no_errors_recorded': True}
        
        error_types = {}
        for ctx in self.error_contexts:
            error_type = ctx.get('error_details', {}).get('type', 'unknown')
            error_types[error_type] = error_types.get(error_type, 0) + 1
        
        return {
            'total_errors': len(self.error_contexts),
            'error_types': error_types,
            'screenshots_captured': len(self.recent_screenshots),
            'unique_content_hashes': len(self.content_hash_to_screenshot),
            'recent_actions': len(self.recent_actions)
        }
