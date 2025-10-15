"""
Configuration Validation

Validates user-provided configuration against Playwright API.
Provides clear error messages with links to documentation.
"""

from typing import Dict, Any, Set
import logging


class ConfigValidationError(Exception):
    """Raised when configuration is invalid"""
    pass


class ConfigValidator:
    """
    Validates CursorFlow and Playwright configuration
    
    Strategy: We don't strictly validate - we warn about likely errors
    and let Playwright do final validation. This keeps us forward-compatible.
    """
    
    # Common browser launch options (for helpful warnings)
    # See: https://playwright.dev/python/docs/api/class-browsertype#browser-type-launch
    KNOWN_BROWSER_OPTIONS = {
        'args', 'channel', 'chromium_sandbox', 'devtools', 'downloads_path',
        'env', 'executable_path', 'firefox_user_prefs', 'handle_sigint',
        'handle_sigterm', 'handle_sighup', 'headless', 'ignore_default_args',
        'proxy', 'slow_mo', 'timeout', 'traces_dir'
    }
    
    # Common context options (for helpful warnings)
    # See: https://playwright.dev/python/docs/api/class-browser#browser-new-context
    KNOWN_CONTEXT_OPTIONS = {
        'accept_downloads', 'base_url', 'bypass_csp', 'color_scheme',
        'device_scale_factor', 'extra_http_headers', 'forced_colors',
        'geolocation', 'has_touch', 'http_credentials', 'ignore_https_errors',
        'is_mobile', 'java_script_enabled', 'locale', 'no_viewport',
        'offline', 'permissions', 'proxy', 'record_har_content',
        'record_har_mode', 'record_har_omit_content', 'record_har_path',
        'record_har_url_filter', 'record_video_dir', 'record_video_size',
        'reduced_motion', 'screen', 'service_workers', 'storage_state',
        'strict_selectors', 'timezone_id', 'user_agent', 'viewport'
    }
    
    @classmethod
    def validate_browser_options(cls, options: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate browser launch options
        
        Args:
            options: User-provided browser options
            
        Returns:
            Validated options (unchanged - just warnings logged)
        """
        logger = logging.getLogger(__name__)
        
        # Warn about unknown options (might be typos)
        for key in options.keys():
            if key not in cls.KNOWN_BROWSER_OPTIONS:
                logger.warning(
                    f"Unknown browser option '{key}' - will pass to Playwright anyway. "
                    f"Check spelling or see: https://playwright.dev/python/docs/api/class-browsertype#browser-type-launch"
                )
        
        # Validate specific option types
        if 'headless' in options and not isinstance(options['headless'], bool):
            raise ConfigValidationError(
                f"'headless' must be boolean, got {type(options['headless']).__name__}: {options['headless']}"
            )
        
        if 'timeout' in options and not isinstance(options['timeout'], (int, float)):
            raise ConfigValidationError(
                f"'timeout' must be number, got {type(options['timeout']).__name__}: {options['timeout']}"
            )
        
        if 'args' in options and not isinstance(options['args'], list):
            raise ConfigValidationError(
                f"'args' must be list of strings, got {type(options['args']).__name__}"
            )
        
        return options
    
    @classmethod
    def validate_context_options(cls, options: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate browser context options
        
        Args:
            options: User-provided context options
            
        Returns:
            Validated options (unchanged - just warnings logged)
        """
        logger = logging.getLogger(__name__)
        
        # Warn about unknown options
        for key in options.keys():
            if key not in cls.KNOWN_CONTEXT_OPTIONS:
                logger.warning(
                    f"Unknown context option '{key}' - will pass to Playwright anyway. "
                    f"Check spelling or see: https://playwright.dev/python/docs/api/class-browser#browser-new-context"
                )
        
        # Validate specific option types
        if 'viewport' in options:
            viewport = options['viewport']
            if not isinstance(viewport, dict):
                raise ConfigValidationError(
                    f"'viewport' must be dict with width/height, got {type(viewport).__name__}"
                )
            if 'width' in viewport and not isinstance(viewport['width'], int):
                raise ConfigValidationError(
                    f"viewport width must be integer, got {type(viewport['width']).__name__}"
                )
            if 'height' in viewport and not isinstance(viewport['height'], int):
                raise ConfigValidationError(
                    f"viewport height must be integer, got {type(viewport['height']).__name__}"
                )
        
        if 'geolocation' in options:
            geo = options['geolocation']
            if not isinstance(geo, dict) or 'latitude' not in geo or 'longitude' not in geo:
                raise ConfigValidationError(
                    f"'geolocation' must be dict with latitude/longitude: "
                    f"{{'latitude': 40.7128, 'longitude': -74.0060}}"
                )
        
        if 'timezone_id' in options and not isinstance(options['timezone_id'], str):
            raise ConfigValidationError(
                f"'timezone_id' must be string like 'America/New_York', got {type(options['timezone_id']).__name__}"
            )
        
        return options
    
    @classmethod
    def get_config_examples(cls) -> str:
        """Get example configurations for documentation"""
        return """
Browser Configuration Examples:

  Enable DevTools (non-headless):
    {
      "headless": false,
      "browser_launch_options": {
        "devtools": true
      }
    }
  
  Use specific Chrome channel:
    {
      "browser_launch_options": {
        "channel": "chrome"
      }
    }
  
  Custom proxy:
    {
      "browser_launch_options": {
        "proxy": {
          "server": "http://myproxy.com:3128",
          "username": "user",
          "password": "pass"
        }
      }
    }

Context Configuration Examples:

  Test in dark mode:
    {
      "context_options": {
        "color_scheme": "dark"
      }
    }
  
  Test with geolocation:
    {
      "context_options": {
        "geolocation": {"latitude": 40.7128, "longitude": -74.0060},
        "permissions": ["geolocation"]
      }
    }
  
  Test offline behavior:
    {
      "context_options": {
        "offline": true
      }
    }
  
  Custom timezone:
    {
      "context_options": {
        "timezone_id": "America/Los_Angeles"
      }
    }
  
  HTTP authentication:
    {
      "context_options": {
        "http_credentials": {
          "username": "admin",
          "password": "secret"
        }
      }
    }

See Playwright documentation for all available options:
  Browser: https://playwright.dev/python/docs/api/class-browsertype#browser-type-launch
  Context: https://playwright.dev/python/docs/api/class-browser#browser-new-context
"""

