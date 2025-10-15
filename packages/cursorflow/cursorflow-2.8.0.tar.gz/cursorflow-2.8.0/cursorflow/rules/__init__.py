"""
CursorFlow Rules for Cursor AI Integration

This package contains the Cursor rules files that provide guidance
to Cursor AI on how to use CursorFlow effectively.
"""

import os
from pathlib import Path

def get_rules_directory():
    """Get the path to the rules directory"""
    return Path(__file__).parent

def get_rule_files():
    """Get list of available rule files"""
    rules_dir = get_rules_directory()
    return list(rules_dir.glob("*.mdc"))
