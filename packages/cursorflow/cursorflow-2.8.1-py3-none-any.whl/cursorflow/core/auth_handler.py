"""
Authentication Handler

Universal authentication support with session persistence.
Handles form-based login, cookie auth, header auth without framework complexity.
"""

import asyncio
import json
import time
from typing import Dict, List, Optional, Any
from pathlib import Path
import logging


class AuthHandler:
    """
    Universal authentication handler - works with any web technology
    
    Supports multiple auth methods with session persistence for faster testing.
    NO FRAMEWORK ASSUMPTIONS - pure universal patterns.
    """
    
    def __init__(self, auth_config: Dict):
        """
        Initialize authentication handler
        
        Args:
            auth_config: {
                "method": "form|cookies|headers",
                "username_selector": "#username",
                "password_selector": "#password", 
                "submit_selector": "#login-button",
                "username": "test_user",
                "password": "test_pass",
                "session_storage": "sessions/"
            }
        """
        self.config = auth_config
        self.method = auth_config.get("method", "form")
        self.logger = logging.getLogger(__name__)
        
        # Create session storage in user's project under .cursorflow
        session_dir = auth_config.get("session_storage", ".cursorflow/sessions/")
        if not Path(session_dir).is_absolute():
            session_dir = Path.cwd() / session_dir
        session_dir = Path(session_dir)
        session_dir.mkdir(parents=True, exist_ok=True)
        self.session_dir = session_dir
    
    async def authenticate(
        self, 
        page, 
        session_options: Optional[Dict] = None
    ) -> bool:
        """
        Authenticate user with session management
        
        Args:
            page: Playwright page object
            session_options: {
                "reuse_session": True,
                "save_session": True,
                "fresh_session": False,
                "session_name": "test_session",
                "debug": False
            }
            
        Returns:
            True if authentication successful, False otherwise
        """
        session_options = session_options or {}
        session_name = session_options.get("session_name", "default")
        debug = session_options.get("debug", False)
        
        try:
            # Try to reuse existing session if requested
            if (session_options.get("reuse_session", True) and 
                not session_options.get("fresh_session", False)):
                
                if await self._restore_session(page, session_name, debug=debug):
                    self.logger.info("✅ Reused existing authentication session")
                    return True
            
            # Perform fresh authentication
            self.logger.info("🔐 Performing fresh authentication...")
            success = await self._perform_authentication(page)
            
            # Save session if requested and successful
            if success and session_options.get("save_session", True):
                await self._save_session(page, session_name)
                
            return success
            
        except Exception as e:
            self.logger.error(f"Authentication failed: {e}")
            return False
    
    async def _restore_session(self, page, session_name: str, debug: bool = False) -> bool:
        """
        Try to restore a saved session
        
        CRITICAL: localStorage can only be set after navigating to the domain.
        This method navigates to the base URL first, then injects storage.
        """
        try:
            session_file = self.session_dir / f"{session_name}_session.json"
            
            if not session_file.exists():
                if debug:
                    self.logger.info(f"🔍 [Session Debug] Session file not found: {session_file}")
                return False
            
            with open(session_file, 'r') as f:
                session_data = json.load(f)
            
            if debug:
                self.logger.info(f"🔍 [Session Debug] Loaded session: {session_name}")
                self.logger.info(f"   • Cookies: {len(session_data.get('cookies', []))}")
                self.logger.info(f"   • localStorage items: {len(session_data.get('localStorage', {}))}")
                self.logger.info(f"   • sessionStorage items: {len(session_data.get('sessionStorage', {}))}")
            
            # Step 1: Restore cookies (can be done before navigation)
            if "cookies" in session_data:
                await page.context.add_cookies(session_data["cookies"])
                if debug:
                    self.logger.info(f"✅ [Session Debug] Added {len(session_data['cookies'])} cookies")
            
            # Step 2: CRITICAL - Navigate to base URL to establish domain context
            # localStorage can only be set for a page that's loaded from that domain
            base_url = session_data.get("url") or session_data.get("base_url")
            if base_url:
                # Extract just the domain if we have a full URL
                from urllib.parse import urlparse
                parsed = urlparse(base_url)
                domain_url = f"{parsed.scheme}://{parsed.netloc}"
                
                if debug:
                    self.logger.info(f"🔍 [Session Debug] Navigating to domain: {domain_url}")
                
                await page.goto(domain_url, wait_until="domcontentloaded", timeout=10000)
            else:
                self.logger.warning(f"⚠️  Session {session_name} has no URL - localStorage may not work")
            
            # Step 3: Restore localStorage (now that we have domain context)
            if "localStorage" in session_data and session_data["localStorage"]:
                if debug:
                    self.logger.info(f"🔍 [Session Debug] Injecting localStorage...")
                
                await page.evaluate("""
                    (storage) => {
                        Object.entries(storage).forEach(([key, value]) => {
                            localStorage.setItem(key, value);
                        });
                    }
                """, session_data["localStorage"])
                
                if debug:
                    # Verify localStorage was set
                    injected_keys = await page.evaluate("() => Object.keys(localStorage)")
                    self.logger.info(f"✅ [Session Debug] localStorage injected: {len(injected_keys)} keys")
                    for key in list(session_data["localStorage"].keys())[:3]:  # Show first 3
                        self.logger.info(f"   • {key}: {str(session_data['localStorage'][key])[:50]}...")
            
            # Step 4: Restore sessionStorage
            if "sessionStorage" in session_data and session_data["sessionStorage"]:
                if debug:
                    self.logger.info(f"🔍 [Session Debug] Injecting sessionStorage...")
                
                await page.evaluate("""
                    (storage) => {
                        Object.entries(storage).forEach(([key, value]) => {
                            sessionStorage.setItem(key, value);
                        });
                    }
                """, session_data["sessionStorage"])
                
                if debug:
                    injected_keys = await page.evaluate("() => Object.keys(sessionStorage)")
                    self.logger.info(f"✅ [Session Debug] sessionStorage injected: {len(injected_keys)} keys")
            
            # Step 5: Validate session is still valid
            is_valid = await self._validate_session(page)
            
            if is_valid:
                self.logger.info(f"✅ Successfully restored session: {session_name}")
                return True
            else:
                self.logger.info(f"⚠️  Restored session {session_name} is no longer valid")
                if debug:
                    self.logger.info(f"🔍 [Session Debug] Session validation failed - session may have expired")
                # Clean up invalid session
                session_file.unlink(missing_ok=True)
                return False
                
        except Exception as e:
            self.logger.warning(f"❌ Session restoration failed: {e}")
            if debug:
                import traceback
                self.logger.error(f"🔍 [Session Debug] Full traceback:\n{traceback.format_exc()}")
            return False
    
    async def _save_session(self, page, session_name: str):
        """Save current session for reuse"""
        try:
            session_file = self.session_dir / f"{session_name}_session.json"
            
            # Get browser storage state
            storage_state = await page.context.storage_state()
            
            # Get local storage
            local_storage = await page.evaluate("""
                () => {
                    const storage = {};
                    for (let i = 0; i < localStorage.length; i++) {
                        const key = localStorage.key(i);
                        storage[key] = localStorage.getItem(key);
                    }
                    return storage;
                }
            """)
            
            # Get session storage
            session_storage = await page.evaluate("""
                () => {
                    const storage = {};
                    for (let i = 0; i < sessionStorage.length; i++) {
                        const key = sessionStorage.key(i);
                        storage[key] = sessionStorage.getItem(key);
                    }
                    return storage;
                }
            """)
            
            # Extract base URL from current page URL
            from urllib.parse import urlparse
            parsed = urlparse(page.url)
            base_url = f"{parsed.scheme}://{parsed.netloc}"
            
            session_data = {
                "timestamp": time.time(),
                "method": self.method,
                "cookies": storage_state.get("cookies", []),
                "localStorage": local_storage,
                "sessionStorage": session_storage,
                "url": page.url,
                "base_url": base_url,  # Added for proper localStorage restoration
                "captured_at": time.strftime("%Y-%m-%d %H:%M:%S")
            }
            
            with open(session_file, 'w') as f:
                json.dump(session_data, f, indent=2)
            
            self.logger.info(f"💾 Session saved: {session_name}")
            
        except Exception as e:
            self.logger.warning(f"Session save failed: {e}")
    
    async def _perform_authentication(self, page) -> bool:
        """Perform authentication based on configured method"""
        
        if self.method == "form":
            return await self._form_authentication(page)
        elif self.method == "cookies":
            return await self._cookie_authentication(page)
        elif self.method == "headers":
            return await self._header_authentication(page)
        else:
            self.logger.error(f"Unsupported authentication method: {self.method}")
            return False
    
    async def _form_authentication(self, page) -> bool:
        """Perform form-based authentication"""
        try:
            username = self.config.get("username")
            password = self.config.get("password")
            username_selector = self.config.get("username_selector", "#username")
            password_selector = self.config.get("password_selector", "#password")
            submit_selector = self.config.get("submit_selector", "#login-button")
            
            if not username or not password:
                self.logger.error("Username and password required for form authentication")
                return False
            
            # Wait for login form
            await page.wait_for_selector(username_selector, timeout=10000)
            
            # Fill username
            await page.fill(username_selector, username)
            self.logger.debug(f"Filled username: {username_selector}")
            
            # Fill password
            await page.fill(password_selector, password)
            self.logger.debug(f"Filled password: {password_selector}")
            
            # Submit form
            await page.click(submit_selector)
            self.logger.debug(f"Clicked submit: {submit_selector}")
            
            # Wait for navigation or success indicator
            try:
                await page.wait_for_load_state("networkidle", timeout=10000)
            except:
                # If no navigation, wait a bit for any AJAX auth
                await page.wait_for_timeout(3000)
            
            # Validate authentication success
            is_authenticated = await self._validate_authentication(page)
            
            if is_authenticated:
                self.logger.info("✅ Form authentication successful")
                return True
            else:
                self.logger.warning("❌ Form authentication failed")
                return False
                
        except Exception as e:
            self.logger.error(f"Form authentication error: {e}")
            return False
    
    async def _cookie_authentication(self, page) -> bool:
        """Perform cookie-based authentication"""
        try:
            cookies = self.config.get("cookies", [])
            
            if not cookies:
                self.logger.error("No cookies provided for cookie authentication")
                return False
            
            # Add cookies to context
            await page.context.add_cookies(cookies)
            self.logger.info(f"Added {len(cookies)} authentication cookies")
            
            # Refresh page to apply cookies
            await page.reload()
            await page.wait_for_load_state("networkidle")
            
            # Validate authentication
            is_authenticated = await self._validate_authentication(page)
            
            if is_authenticated:
                self.logger.info("✅ Cookie authentication successful")
                return True
            else:
                self.logger.warning("❌ Cookie authentication failed")
                return False
                
        except Exception as e:
            self.logger.error(f"Cookie authentication error: {e}")
            return False
    
    async def _header_authentication(self, page) -> bool:
        """Perform header-based authentication"""
        try:
            headers = self.config.get("headers", {})
            
            if not headers:
                self.logger.error("No headers provided for header authentication")
                return False
            
            # Set extra HTTP headers
            await page.set_extra_http_headers(headers)
            self.logger.info(f"Set {len(headers)} authentication headers")
            
            # Refresh page to apply headers
            await page.reload()
            await page.wait_for_load_state("networkidle")
            
            # Validate authentication
            is_authenticated = await self._validate_authentication(page)
            
            if is_authenticated:
                self.logger.info("✅ Header authentication successful")
                return True
            else:
                self.logger.warning("❌ Header authentication failed")
                return False
                
        except Exception as e:
            self.logger.error(f"Header authentication error: {e}")
            return False
    
    async def _validate_authentication(self, page) -> bool:
        """Validate that authentication was successful"""
        try:
            # Universal authentication validation strategies
            
            # Strategy 1: Check for common auth failure indicators
            auth_failure_selectors = [
                ".error", ".alert-danger", ".login-error", 
                "#error", "#login-error", "[data-testid='error']"
            ]
            
            for selector in auth_failure_selectors:
                try:
                    error_element = await page.wait_for_selector(selector, timeout=1000)
                    if error_element:
                        error_text = await error_element.text_content()
                        if error_text and any(word in error_text.lower() for word in ["error", "invalid", "failed", "incorrect"]):
                            self.logger.warning(f"Authentication error detected: {error_text}")
                            return False
                except:
                    continue
            
            # Strategy 2: Check for common success indicators
            success_indicators = self.config.get("success_indicators", [
                "dashboard", "profile", "logout", "welcome", "user", "account"
            ])
            
            page_content = await page.content()
            page_content_lower = page_content.lower()
            
            success_count = sum(1 for indicator in success_indicators if indicator in page_content_lower)
            
            # Strategy 3: Check URL changes
            current_url = page.url
            login_urls = ["/login", "/signin", "/auth"]
            
            url_indicates_success = not any(login_url in current_url.lower() for login_url in login_urls)
            
            # Strategy 4: Check for auth-specific elements
            auth_selectors = self.config.get("auth_check_selectors", [])
            auth_elements_found = 0
            
            for selector in auth_selectors:
                try:
                    element = await page.wait_for_selector(selector, timeout=1000)
                    if element:
                        auth_elements_found += 1
                except:
                    continue
            
            # Determine authentication success
            is_authenticated = (
                success_count >= 2 or  # Multiple success indicators
                url_indicates_success or  # URL changed from login page
                auth_elements_found > 0  # Found auth-specific elements
            )
            
            self.logger.debug(f"Auth validation - success_count: {success_count}, url_ok: {url_indicates_success}, auth_elements: {auth_elements_found}")
            
            return is_authenticated
            
        except Exception as e:
            self.logger.error(f"Authentication validation error: {e}")
            return False
    
    async def _validate_session(self, page) -> bool:
        """Validate that a restored session is still valid"""
        # Use the same validation logic as fresh authentication
        return await self._validate_authentication(page)
    
    def get_session_info(self, session_name: str = "default") -> Optional[Dict]:
        """Get information about a saved session"""
        try:
            session_file = self.session_dir / f"{session_name}_session.json"
            
            if not session_file.exists():
                return None
            
            with open(session_file, 'r') as f:
                session_data = json.load(f)
            
            return {
                "session_name": session_name,
                "timestamp": session_data.get("timestamp"),
                "method": session_data.get("method"),
                "url": session_data.get("url"),
                "cookies_count": len(session_data.get("cookies", [])),
                "has_local_storage": bool(session_data.get("localStorage")),
                "has_session_storage": bool(session_data.get("sessionStorage"))
            }
            
        except Exception as e:
            self.logger.error(f"Session info retrieval failed: {e}")
            return None
    
    def clear_session(self, session_name: str = "default"):
        """Clear a saved session"""
        try:
            session_file = self.session_dir / f"{session_name}_session.json"
            session_file.unlink(missing_ok=True)
            self.logger.info(f"Cleared session: {session_name}")
            
        except Exception as e:
            self.logger.error(f"Session clearing failed: {e}")
    
    def list_sessions(self) -> List[str]:
        """List all saved sessions"""
        try:
            sessions = []
            for session_file in self.session_dir.glob("*_session.json"):
                session_name = session_file.stem.replace("_session", "")
                sessions.append(session_name)
            return sessions
            
        except Exception as e:
            self.logger.error(f"Session listing failed: {e}")
            return []
