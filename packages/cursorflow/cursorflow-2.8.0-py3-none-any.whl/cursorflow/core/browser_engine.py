"""
Universal Browser Engine

Framework-agnostic browser automation using Playwright.
Adapts to different web architectures through pluggable adapters.
"""

import asyncio
import json
import time
from typing import Dict, List, Any, Optional
from playwright.async_api import async_playwright, Page, Browser, BrowserContext
import logging

class BrowserEngine:
    """Universal browser automation engine"""
    
    def __init__(self, base_url: str, adapter):
        self.base_url = base_url
        self.adapter = adapter
        self.browser = None
        self.context = None
        self.page = None
        
        # Event tracking
        self.events = []
        self.network_requests = []
        self.console_errors = []
        
        self.logger = logging.getLogger(__name__)
        
    async def initialize(self, headless: bool = True, device: str = 'desktop'):
        """Initialize browser with framework-appropriate settings"""
        
        playwright = await async_playwright().start()
        
        # Browser configuration
        browser_config = {
            'headless': headless,
            'args': ['--disable-web-security', '--disable-features=VizDisplayCompositor']
        }
        
        # Add framework-specific browser settings
        framework_config = self.adapter.get_browser_config()
        browser_config.update(framework_config)
        
        self.browser = await playwright.chromium.launch(**browser_config)
        
        # Create context with device settings
        context_config = {
            'viewport': {'width': 1440, 'height': 900},
            'user_agent': 'CursorTestingAgent/1.0'
        }
        
        if device == 'mobile':
            context_config['viewport'] = {'width': 375, 'height': 667}
        elif device == 'tablet':
            context_config['viewport'] = {'width': 768, 'height': 1024}
            
        self.context = await self.browser.new_context(**context_config)
        self.page = await self.context.new_page()
        
        # Setup event listeners
        await self._setup_event_listeners()
        
        self.logger.info(f"Browser initialized for {self.adapter.__class__.__name__}")
    
    async def _setup_event_listeners(self):
        """Setup browser event monitoring"""
        
        # Console message handler
        self.page.on('console', lambda msg: self._handle_console_message(msg))
        
        # Request/response handler
        self.page.on('request', lambda req: self._handle_request(req))
        self.page.on('response', lambda resp: self._handle_response(resp))
        
        # Error handlers
        self.page.on('pageerror', lambda err: self._handle_page_error(err))
        self.page.on('requestfailed', lambda req: self._handle_request_failed(req))
    
    def _handle_console_message(self, message):
        """Handle browser console messages"""
        event = {
            'timestamp': time.time(),
            'type': 'console',
            'level': message.type,
            'text': message.text,
            'location': message.location
        }
        
        self.events.append(event)
        
        if message.type in ['error', 'warning']:
            self.console_errors.append(event)
    
    def _handle_request(self, request):
        """Handle network requests"""
        self.network_requests.append({
            'timestamp': time.time(),
            'type': 'request',
            'method': request.method,
            'url': request.url,
            'headers': dict(request.headers),
            'post_data': request.post_data
        })
    
    def _handle_response(self, response):
        """Handle network responses"""
        self.network_requests.append({
            'timestamp': time.time(),
            'type': 'response', 
            'status': response.status,
            'url': response.url,
            'headers': dict(response.headers)
        })
    
    def _handle_page_error(self, error):
        """Handle JavaScript page errors"""
        self.events.append({
            'timestamp': time.time(),
            'type': 'page_error',
            'message': str(error),
            'severity': 'critical'
        })
    
    def _handle_request_failed(self, request):
        """Handle failed network requests"""
        self.events.append({
            'timestamp': time.time(),
            'type': 'request_failed',
            'url': request.url,
            'method': request.method,
            'failure_text': request.failure,
            'severity': 'high'
        })
    
    async def navigate(self, url: str, params: Optional[Dict] = None):
        """Navigate to URL with framework-appropriate handling"""
        
        # Build full URL using adapter
        full_url = self.adapter.build_url(self.base_url, url, params)
        
        self.logger.info(f"Navigating to: {full_url}")
        
        # Record navigation event
        self.events.append({
            'timestamp': time.time(),
            'type': 'navigation',
            'url': full_url,
            'params': params
        })
        
        # Navigate
        await self.page.goto(full_url)
        
        # Wait for framework-specific ready state
        await self.adapter.wait_for_ready_state(self.page)
        
        # Capture initial state
        await self._capture_page_state('navigation_complete')
    
    async def execute_workflow(self, workflow_definition: List[Dict]) -> Dict:
        """Execute a defined workflow of actions"""
        
        workflow_results = {
            'actions': [],
            'success': True,
            'errors': []
        }
        
        for step in workflow_definition:
            try:
                action_result = await self._execute_action(step)
                workflow_results['actions'].append(action_result)
                
                if not action_result.get('success', True):
                    workflow_results['success'] = False
                    
            except Exception as e:
                error = {
                    'action': step,
                    'error': str(e),
                    'timestamp': time.time()
                }
                workflow_results['errors'].append(error)
                workflow_results['success'] = False
                self.logger.error(f"Workflow step failed: {e}")
        
        return workflow_results
    
    async def _execute_action(self, action: Dict) -> Dict:
        """Execute a single test action"""
        
        # Validate action format
        from .action_validator import ActionValidator, ActionValidationError
        
        try:
            action = ActionValidator.validate(action)
        except ActionValidationError as e:
            return {
                'action': 'unknown',
                'success': False,
                'error': f"Invalid action format: {e}"
            }
        
        # Extract action type safely
        action_type = action.get('type') or list(action.keys())[0]
        action_config = action.get(action_type, action)
        
        start_time = time.time()
        
        # Record action start
        self.events.append({
            'timestamp': start_time,
            'type': 'action_start',
            'action': action_type,
            'config': action_config
        })
        
        result = {'action': action_type, 'success': True}
        
        try:
            if action_type == 'click':
                await self.page.click(action_config['selector'])
                
            elif action_type == 'fill':
                await self.page.fill(action_config['selector'], action_config['value'])
                
            elif action_type == 'select':
                await self.page.select_option(action_config['selector'], action_config['value'])
                
            elif action_type == 'wait_for':
                await self.page.wait_for_selector(action_config['selector'])
                
            elif action_type == 'wait_for_condition':
                await self.page.wait_for_function(action_config['condition'])
                
            elif action_type == 'capture':
                await self._capture_page_state(action_config['name'])
                
            elif action_type == 'validate':
                validation_result = await self._validate_condition(action_config)
                result['validation'] = validation_result
                result['success'] = validation_result['passed']
                
            elif action_type == 'wait':
                wait_time = action_config.get('timeout', 1000)
                await self.page.wait_for_timeout(wait_time)
                
            else:
                # Let adapter handle framework-specific actions
                await self.adapter.execute_custom_action(self.page, action_type, action_config)
                
        except Exception as e:
            result['success'] = False
            result['error'] = str(e)
            self.logger.error(f"Action {action_type} failed: {e}")
        
        # Record completion
        result['duration'] = time.time() - start_time
        
        self.events.append({
            'timestamp': time.time(),
            'type': 'action_complete',
            'action': action_type,
            'result': result
        })
        
        return result
    
    async def _capture_page_state(self, name: str):
        """Capture current page state for debugging"""
        
        state = {
            'timestamp': time.time(),
            'name': name,
            'url': self.page.url,
            'title': await self.page.title(),
            'screenshot': f"screenshots/{name}_{int(time.time())}.png",
            'dom_snapshot': await self.page.content(),
            'local_storage': await self.page.evaluate('() => JSON.stringify(localStorage)'),
            'session_storage': await self.page.evaluate('() => JSON.stringify(sessionStorage)')
        }
        
        # Take screenshot
        await self.page.screenshot(path=state['screenshot'])
        
        # Framework-specific state capture
        framework_state = await self.adapter.capture_framework_state(self.page)
        state['framework_data'] = framework_state
        
        self.events.append({
            'timestamp': time.time(),
            'type': 'state_capture',
            'state': state
        })
        
        return state
    
    async def _validate_condition(self, validation_config: Dict) -> Dict:
        """Validate page conditions"""
        
        validation_result = {
            'passed': True,
            'checks': []
        }
        
        # Standard validations
        if 'selector' in validation_config:
            selector = validation_config['selector']
            
            # Check existence
            if validation_config.get('exists') is not None:
                exists = await self.page.is_visible(selector)
                expected = validation_config['exists']
                passed = exists == expected
                
                validation_result['checks'].append({
                    'type': 'exists',
                    'selector': selector,
                    'expected': expected,
                    'actual': exists,
                    'passed': passed
                })
                
                if not passed:
                    validation_result['passed'] = False
            
            # Check text content
            if 'text_contains' in validation_config:
                text = await self.page.text_content(selector)
                expected = validation_config['text_contains']
                passed = expected in (text or '')
                
                validation_result['checks'].append({
                    'type': 'text_contains',
                    'selector': selector,
                    'expected': expected,
                    'actual': text,
                    'passed': passed
                })
                
                if not passed:
                    validation_result['passed'] = False
        
        # Framework-specific validations
        framework_validations = await self.adapter.validate_framework_conditions(
            self.page, validation_config
        )
        validation_result['framework_checks'] = framework_validations
        
        return validation_result
    
    async def get_performance_metrics(self) -> Dict:
        """Get browser performance metrics with proper null handling"""
        
        metrics = await self.page.evaluate("""() => {
            // Helper function to safely calculate timing differences
            const safeTiming = (end, start) => {
                if (!end || !start || end === 0 || start === 0) return null;
                const diff = end - start;
                return diff >= 0 ? diff : null;
            };
            
            const timing = performance.timing;
            const navigation = performance.getEntriesByType('navigation')[0];
            
            return {
                page_load_time: safeTiming(timing.loadEventEnd, timing.navigationStart),
                dom_ready_time: safeTiming(timing.domContentLoadedEventEnd, timing.navigationStart),
                first_paint: navigation ? navigation.loadEventEnd : null,
                resource_count: performance.getEntriesByType('resource').length,
                memory_usage: performance.memory ? {
                    used: performance.memory.usedJSHeapSize,
                    total: performance.memory.totalJSHeapSize,
                    limit: performance.memory.jsHeapSizeLimit
                } : null,
                _reliability: {
                    timing_available: timing !== undefined,
                    navigation_available: navigation !== undefined,
                    memory_available: performance.memory !== undefined,
                    note: "null values in headless mode are expected"
                }
            };
        }""")
        
        return metrics
    
    def get_events(self) -> List[Dict]:
        """Get all recorded browser events"""
        return self.events.copy()
    
    def get_console_errors(self) -> List[Dict]:
        """Get browser console errors"""
        return self.console_errors.copy()
    
    def get_network_requests(self) -> List[Dict]:
        """Get network request/response data"""
        return self.network_requests.copy()
    
    async def cleanup(self):
        """Clean up browser resources"""
        
        if self.page:
            await self.page.close()
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()
            
        self.logger.info("Browser cleanup complete")
