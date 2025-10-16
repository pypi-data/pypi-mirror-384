"""
Action Format Validation

Validates action dictionaries before execution to provide clear error messages.
"""

from typing import Dict, Any, List, Optional


class ActionValidationError(Exception):
    """Raised when action format is invalid"""
    pass


class ActionValidator:
    """
    Validates action format before execution
    
    Actions should be dictionaries with a single key indicating the action type,
    or have an explicit 'type' key.
    
    Valid formats:
        {"click": ".selector"}
        {"click": {"selector": ".element"}}
        {"type": "click", "selector": ".element"}
        {"navigate": "/path"}
        {"wait": 2}
    """
    
    # CursorFlow-specific action types (not direct Playwright methods)
    CURSORFLOW_ACTION_TYPES = {
        'navigate', 'screenshot', 'capture', 'authenticate'
    }
    
    # Common Playwright Page methods (for documentation/validation)
    COMMON_PLAYWRIGHT_ACTIONS = {
        'click', 'dblclick', 'hover', 'focus', 'blur',
        'fill', 'type', 'press', 'select_option', 
        'check', 'uncheck', 'set_checked',
        'drag_and_drop', 'tap',
        'wait', 'wait_for_selector', 'wait_for_timeout', 'wait_for_load_state',
        'goto', 'reload', 'go_back', 'go_forward',
        'scroll', 'set_viewport_size', 'bring_to_front',
        'evaluate', 'evaluate_handle', 'query_selector'
    }
    
    # All known valid actions (CursorFlow + Playwright)
    # Note: This is not exhaustive - we pass through to Playwright dynamically
    KNOWN_ACTION_TYPES = CURSORFLOW_ACTION_TYPES | COMMON_PLAYWRIGHT_ACTIONS
    
    @classmethod
    def validate(cls, action: Any) -> Dict[str, Any]:
        """
        Validate action format and return normalized action
        
        Args:
            action: The action to validate (should be dict)
            
        Returns:
            Validated and normalized action dict
            
        Raises:
            ActionValidationError: If action format is invalid
        """
        # Check if action is a dict
        if not isinstance(action, dict):
            raise ActionValidationError(
                f"Action must be a dictionary, got {type(action).__name__}: {action}\n"
                f"Expected format: {{'click': '.selector'}} or {{'type': 'click', 'selector': '.element'}}"
            )
        
        # Check if action is empty
        if not action:
            raise ActionValidationError(
                "Action dictionary is empty\n"
                f"Expected format: {{'click': '.selector'}}"
            )
        
        # Get action type
        action_type = cls._extract_action_type(action)
        
        # Validate action type (permissive - warns for unknown, doesn't block)
        if action_type not in cls.KNOWN_ACTION_TYPES:
            # Log warning but allow it (might be valid Playwright method)
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(
                f"Unknown action type '{action_type}' - will attempt to pass through to Playwright. "
                f"Common actions: {', '.join(sorted(list(cls.COMMON_PLAYWRIGHT_ACTIONS)[:10]))}... "
                f"See: https://playwright.dev/python/docs/api/class-page"
            )
        
        return action
    
    @classmethod
    def _extract_action_type(cls, action: dict) -> str:
        """
        Extract action type from action dict
        
        Supports:
            {"type": "click", "selector": ".btn"}  # Explicit type key with string value
            {"click": ".selector"}                  # Action type is the key
            {"click": {"selector": ".btn"}}        # Action type with config dict
            {"type": {"selector": "#field"}}       # 'type' as action (typing), not explicit type
        """
        # Check if 'type' key exists AND has a string value (explicit type specification)
        # If type key has a dict value, it's the action itself (typing action)
        if 'type' in action and isinstance(action['type'], str):
            return action['type']
        
        # Otherwise, first key is the action type
        keys = list(action.keys())
        if not keys:
            raise ActionValidationError("Action has no keys")
        
        action_type = keys[0]
        
        # First key should be the action type (string)
        if not isinstance(action_type, str):
            raise ActionValidationError(
                f"Action type must be a string, got {type(action_type).__name__}: {action_type}"
            )
        
        return action_type
    
    @classmethod
    def validate_list(cls, actions: Any) -> List[Dict[str, Any]]:
        """
        Validate list of actions
        
        Args:
            actions: Should be a list of action dicts
            
        Returns:
            List of validated actions
            
        Raises:
            ActionValidationError: If format is invalid
        """
        if not isinstance(actions, list):
            raise ActionValidationError(
                f"Actions must be a list, got {type(actions).__name__}: {actions}\n"
                f"Expected format: [{{'click': '.btn'}}, {{'wait': 2}}]"
            )
        
        if not actions:
            raise ActionValidationError(
                "Actions list is empty\n"
                f"Expected at least one action like: [{{'navigate': '/'}}]"
            )
        
        validated = []
        for i, action in enumerate(actions):
            try:
                validated.append(cls.validate(action))
            except ActionValidationError as e:
                raise ActionValidationError(
                    f"Invalid action at index {i}: {e}"
                )
        
        return validated
    
    @classmethod
    def get_example_actions(cls) -> str:
        """Get example action formats for help text"""
        return """
Action Format Examples:

  Common CursorFlow actions:
    {"navigate": "/dashboard"}
    {"click": ".button"}
    {"screenshot": "page-loaded"}
  
  Any Playwright Page method:
    {"hover": ".menu-item"}
    {"dblclick": ".editable"}
    {"press": "Enter"}
    {"drag_and_drop": {"source": ".item", "target": ".dropzone"}}
    {"focus": "#input"}
    {"check": "#checkbox"}
    {"evaluate": "window.scrollTo(0, 100)"}
  
  See full Playwright API:
    https://playwright.dev/python/docs/api/class-page
  
  CursorFlow passes actions directly to Playwright, giving you access
  to 94+ methods without artificial limitations.
  
  Complete workflow:
    [
      {"navigate": "/login"},
      {"fill": {"selector": "#username", "value": "admin"}},
      {"fill": {"selector": "#password", "value": "pass123"}},
      {"click": "#submit"},
      {"wait_for_selector": ".dashboard"},
      {"screenshot": "logged-in"}
    ]
"""

