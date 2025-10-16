"""
CursorFlow v2.0 Hot Module Replacement (HMR) Detection System

This module provides intelligent detection and monitoring of Hot Module Replacement
events across different development frameworks, enabling precision timing for CSS
iteration workflows.

Core Philosophy: Pure observation of HMR events - we listen but never trigger.
"""

import asyncio
import json
import logging
import time
from typing import Dict, List, Optional, Any, Callable
from urllib.parse import urlparse
import websockets
from websockets.exceptions import ConnectionClosed, InvalidURI


class HMRDetector:
    """
    v2.0 Enhancement: Intelligent Hot Module Replacement event detection
    
    Supports auto-detection and monitoring for:
    - Vite (port 5173, WebSocket path /__vite_hmr)
    - Webpack Dev Server (port 3000, WebSocket path /sockjs-node)
    - Next.js (port 3000, WebSocket path /_next/webpack-hmr)
    - Parcel (port 1234, WebSocket path /hmr)
    - Laravel Mix (port 3000, WebSocket path /browser-sync/socket.io)
    """
    
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Parse the base URL to get host and port
        parsed_url = urlparse(base_url)
        self.host = parsed_url.hostname or 'localhost'
        self.port = parsed_url.port or 3000
        
        # HMR detection state
        self.detected_framework = None
        self.hmr_config = None
        self.websocket = None
        self.is_monitoring = False
        self.hmr_events = []
        self.event_callbacks = []
        
        # Framework configurations
        self.framework_configs = {
            'vite': {
                'name': 'Vite',
                'default_port': 5173,
                'ws_paths': ['/__vite_hmr', '/vite-hmr'],
                'event_patterns': ['vite:beforeUpdate', 'vite:afterUpdate', 'css-update'],
                'css_update_indicators': ['css-update', 'style-update']
            },
            'webpack': {
                'name': 'Webpack Dev Server',
                'default_port': 3000,
                'ws_paths': ['/sockjs-node', '/webpack-hmr', '/ws'],
                'event_patterns': ['webpackHotUpdate', 'hot', 'hash'],
                'css_update_indicators': ['css', 'style', 'hot-update']
            },
            'nextjs': {
                'name': 'Next.js',
                'default_port': 3000,
                'ws_paths': ['/_next/webpack-hmr', '/_next/static/hmr'],
                'event_patterns': ['building', 'built', 'sync'],
                'css_update_indicators': ['css', 'style']
            },
            'parcel': {
                'name': 'Parcel',
                'default_port': 1234,
                'ws_paths': ['/hmr', '/parcel-hmr'],
                'event_patterns': ['buildSuccess', 'buildError', 'hmr:update'],
                'css_update_indicators': ['css', 'style']
            },
            'laravel_mix': {
                'name': 'Laravel Mix',
                'default_port': 3000,
                'ws_paths': ['/browser-sync/socket.io', '/browsersync'],
                'event_patterns': ['file:changed', 'browser:reload'],
                'css_update_indicators': ['css', 'scss', 'sass']
            }
        }
    
    async def auto_detect_framework(self) -> Optional[str]:
        """
        Auto-detect the development framework by probing WebSocket endpoints
        
        Returns the detected framework key or None if no framework detected
        """
        self.logger.info(f"Auto-detecting HMR framework for {self.base_url}")
        
        # Try to detect based on port first
        port_hints = {
            5173: ['vite'],
            3000: ['webpack', 'nextjs', 'laravel_mix'],
            1234: ['parcel']
        }
        
        frameworks_to_check = port_hints.get(self.port, list(self.framework_configs.keys()))
        
        for framework_key in frameworks_to_check:
            config = self.framework_configs[framework_key]
            
            # Test WebSocket connections for this framework
            for ws_path in config['ws_paths']:
                ws_url = f"ws://{self.host}:{self.port}{ws_path}"
                
                try:
                    self.logger.debug(f"Testing WebSocket connection: {ws_url}")
                    
                    # Quick connection test with timeout
                    websocket = await asyncio.wait_for(
                        websockets.connect(ws_url, ping_interval=None),
                        timeout=2.0
                    )
                    
                    # Connection successful - this is likely our framework
                    await websocket.close()
                    
                    self.detected_framework = framework_key
                    self.hmr_config = {
                        'framework': framework_key,
                        'name': config['name'],
                        'ws_url': ws_url,
                        'ws_path': ws_path,
                        'event_patterns': config['event_patterns'],
                        'css_indicators': config['css_update_indicators']
                    }
                    
                    self.logger.info(f"✅ Detected HMR framework: {config['name']} at {ws_url}")
                    return framework_key
                    
                except (ConnectionClosed, InvalidURI, OSError, asyncio.TimeoutError) as e:
                    self.logger.debug(f"WebSocket test failed for {ws_url}: {e}")
                    continue
        
        self.logger.warning("❌ No HMR framework detected - CSS iteration will use fallback timing")
        return None
    
    async def start_monitoring(self, on_hmr_event: Optional[Callable] = None) -> bool:
        """
        Start monitoring HMR events
        
        Args:
            on_hmr_event: Optional callback function for HMR events
            
        Returns:
            True if monitoring started successfully, False otherwise
        """
        if not self.hmr_config:
            await self.auto_detect_framework()
        
        if not self.hmr_config:
            self.logger.warning("Cannot start HMR monitoring - no framework detected")
            return False
        
        try:
            ws_url = self.hmr_config['ws_url']
            self.logger.info(f"Starting HMR monitoring for {self.hmr_config['name']} at {ws_url}")
            
            self.websocket = await websockets.connect(ws_url, ping_interval=20)
            self.is_monitoring = True
            
            if on_hmr_event:
                self.event_callbacks.append(on_hmr_event)
            
            # Start the monitoring loop
            asyncio.create_task(self._monitor_hmr_events())
            
            self.logger.info("✅ HMR monitoring started successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to start HMR monitoring: {e}")
            self.is_monitoring = False
            return False
    
    async def _monitor_hmr_events(self):
        """Internal method to monitor WebSocket messages for HMR events"""
        try:
            async for message in self.websocket:
                await self._process_hmr_message(message)
                
        except ConnectionClosed:
            self.logger.info("HMR WebSocket connection closed")
            self.is_monitoring = False
        except Exception as e:
            self.logger.error(f"HMR monitoring error: {e}")
            self.is_monitoring = False
    
    async def _process_hmr_message(self, message: str):
        """Process incoming HMR WebSocket messages"""
        try:
            # Parse message (could be JSON or plain text depending on framework)
            try:
                data = json.loads(message)
                message_type = 'json'
            except json.JSONDecodeError:
                data = message
                message_type = 'text'
            
            # Create HMR event record
            hmr_event = {
                'timestamp': time.time(),
                'framework': self.hmr_config['framework'],
                'message_type': message_type,
                'raw_message': message,
                'parsed_data': data if message_type == 'json' else None,
                'event_type': self._classify_hmr_event(data, message),
                'is_css_update': self._is_css_update(data, message)
            }
            
            # Store the event
            self.hmr_events.append(hmr_event)
            
            # Keep only last 100 events to prevent memory issues
            if len(self.hmr_events) > 100:
                self.hmr_events = self.hmr_events[-100:]
            
            # Notify callbacks
            for callback in self.event_callbacks:
                try:
                    await callback(hmr_event)
                except Exception as e:
                    self.logger.error(f"HMR event callback error: {e}")
            
            # Log important events
            if hmr_event['is_css_update']:
                self.logger.info(f"🎨 CSS update detected: {hmr_event['event_type']}")
            elif hmr_event['event_type'] != 'heartbeat':
                self.logger.debug(f"HMR event: {hmr_event['event_type']}")
                
        except Exception as e:
            self.logger.error(f"Error processing HMR message: {e}")
    
    def _classify_hmr_event(self, data: Any, raw_message: str) -> str:
        """Classify the type of HMR event based on message content"""
        if not self.hmr_config:
            return 'unknown'
        
        framework = self.hmr_config['framework']
        event_patterns = self.hmr_config['event_patterns']
        
        # Convert to string for pattern matching
        message_str = str(data).lower() if data else raw_message.lower()
        
        # Framework-specific event classification
        if framework == 'vite':
            if 'vite:beforeupdate' in message_str:
                return 'build_start'
            elif 'vite:afterupdate' in message_str or 'css-update' in message_str:
                return 'css_update'
            elif 'connected' in message_str:
                return 'connection'
            elif 'ping' in message_str or 'pong' in message_str:
                return 'heartbeat'
                
        elif framework == 'webpack':
            if 'webpackhotupdate' in message_str:
                return 'hot_update'
            elif 'building' in message_str:
                return 'build_start'
            elif 'built' in message_str:
                return 'build_complete'
            elif 'hash' in message_str:
                return 'hash_update'
                
        elif framework == 'nextjs':
            if 'building' in message_str:
                return 'build_start'
            elif 'built' in message_str:
                return 'build_complete'
            elif 'sync' in message_str:
                return 'sync'
                
        elif framework == 'parcel':
            if 'buildsuccess' in message_str:
                return 'build_success'
            elif 'builderror' in message_str:
                return 'build_error'
            elif 'hmr:update' in message_str:
                return 'hmr_update'
                
        elif framework == 'laravel_mix':
            if 'file:changed' in message_str:
                return 'file_change'
            elif 'browser:reload' in message_str:
                return 'browser_reload'
        
        # Check against general patterns
        for pattern in event_patterns:
            if pattern.lower() in message_str:
                return pattern
        
        return 'unknown'
    
    def _is_css_update(self, data: Any, raw_message: str) -> bool:
        """Determine if this HMR event represents a CSS update"""
        if not self.hmr_config:
            return False
        
        css_indicators = self.hmr_config['css_indicators']
        message_str = str(data).lower() if data else raw_message.lower()
        
        # Check for CSS-specific indicators
        for indicator in css_indicators:
            if indicator in message_str:
                return True
        
        # Additional CSS detection patterns
        css_patterns = ['.css', '.scss', '.sass', '.less', 'style', 'stylesheet']
        for pattern in css_patterns:
            if pattern in message_str:
                return True
        
        return False
    
    async def wait_for_css_update(self, timeout: float = 10.0) -> Optional[Dict]:
        """
        Wait for the next CSS update event with precision timing
        
        This is the key method that replaces arbitrary waits in CSS iteration:
        
        OLD WAY:
        await page.screenshot("before.png")
        # ... developer makes CSS changes ...
        await page.wait_for_timeout(2000)  # Arbitrary wait
        await page.screenshot("after.png")
        
        NEW WAY:
        await page.screenshot("before.png")
        # ... developer makes CSS changes ...
        css_event = await hmr_detector.wait_for_css_update()  # Precise timing
        await page.screenshot("after.png")
        
        Args:
            timeout: Maximum time to wait for CSS update (seconds)
            
        Returns:
            HMR event dict if CSS update detected, None if timeout
        """
        if not self.is_monitoring:
            self.logger.warning("HMR monitoring not active - cannot wait for CSS updates")
            return None
        
        start_time = time.time()
        initial_event_count = len(self.hmr_events)
        
        self.logger.info(f"⏱️  Waiting for CSS update (timeout: {timeout}s)")
        
        while time.time() - start_time < timeout:
            # Check for new CSS update events
            for event in self.hmr_events[initial_event_count:]:
                if event['is_css_update']:
                    self.logger.info(f"✅ CSS update detected after {time.time() - start_time:.2f}s")
                    return event
            
            # Short sleep to prevent busy waiting
            await asyncio.sleep(0.1)
        
        self.logger.warning(f"⏰ CSS update wait timeout after {timeout}s")
        return None
    
    async def wait_for_build_complete(self, timeout: float = 30.0) -> Optional[Dict]:
        """
        Wait for build completion (useful for more complex changes)
        
        Args:
            timeout: Maximum time to wait for build completion (seconds)
            
        Returns:
            HMR event dict if build completed, None if timeout
        """
        if not self.is_monitoring:
            self.logger.warning("HMR monitoring not active - cannot wait for build completion")
            return None
        
        start_time = time.time()
        initial_event_count = len(self.hmr_events)
        
        self.logger.info(f"⏱️  Waiting for build completion (timeout: {timeout}s)")
        
        build_complete_indicators = ['build_complete', 'build_success', 'css_update', 'hot_update']
        
        while time.time() - start_time < timeout:
            # Check for build completion events
            for event in self.hmr_events[initial_event_count:]:
                if event['event_type'] in build_complete_indicators:
                    self.logger.info(f"✅ Build completed after {time.time() - start_time:.2f}s")
                    return event
            
            await asyncio.sleep(0.1)
        
        self.logger.warning(f"⏰ Build completion wait timeout after {timeout}s")
        return None
    
    async def stop_monitoring(self):
        """Stop HMR monitoring and close WebSocket connection"""
        self.is_monitoring = False
        
        if self.websocket:
            try:
                await self.websocket.close()
                self.logger.info("HMR monitoring stopped")
            except Exception as e:
                self.logger.error(f"Error stopping HMR monitoring: {e}")
        
        self.websocket = None
    
    def get_hmr_status(self) -> Dict[str, Any]:
        """Get current HMR detection and monitoring status"""
        return {
            'framework_detected': self.detected_framework,
            'framework_name': self.hmr_config['name'] if self.hmr_config else None,
            'is_monitoring': self.is_monitoring,
            'websocket_url': self.hmr_config['ws_url'] if self.hmr_config else None,
            'total_events': len(self.hmr_events),
            'css_events': len([e for e in self.hmr_events if e['is_css_update']]),
            'recent_events': self.hmr_events[-5:] if self.hmr_events else []
        }
    
    def get_framework_info(self) -> Dict[str, Any]:
        """Get information about the detected framework"""
        if not self.hmr_config:
            return {'detected': False, 'supported_frameworks': list(self.framework_configs.keys())}
        
        return {
            'detected': True,
            'framework': self.hmr_config['framework'],
            'name': self.hmr_config['name'],
            'websocket_path': self.hmr_config['ws_path'],
            'css_indicators': self.hmr_config['css_indicators'],
            'event_patterns': self.hmr_config['event_patterns']
        }
