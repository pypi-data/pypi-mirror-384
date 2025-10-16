"""
Auto-initialization for CursorFlow

Detects uninitialized projects and offers to set them up automatically.
Makes the setup process seamless for both humans and AI agents.
"""

import os
import sys
from pathlib import Path
from typing import Optional


def is_project_initialized(project_dir: Optional[str] = None) -> bool:
    """
    Check if CursorFlow is initialized in the project
    
    Returns True if:
    - .cursor/rules/ contains CursorFlow rules
    - .cursorflow/config.json exists
    - .cursorflow/ directory exists
    """
    if project_dir is None:
        project_dir = os.getcwd()
    
    project_path = Path(project_dir)
    
    # Check for key indicators
    has_rules = (project_path / ".cursor" / "rules" / "cursorflow-usage.mdc").exists()
    has_config = (project_path / ".cursorflow" / "config.json").exists()
    
    # Need at least rules and config
    return has_rules and has_config


def auto_initialize_if_needed(project_dir: Optional[str] = None, interactive: bool = True) -> bool:
    """
    Auto-initialize CursorFlow in project if not already initialized
    
    Args:
        project_dir: Project directory (defaults to cwd)
        interactive: If True, ask user for confirmation. If False, auto-initialize silently.
        
    Returns:
        True if initialized (or already was), False if user declined or error occurred
    """
    if is_project_initialized(project_dir):
        return True
    
    if project_dir is None:
        project_dir = os.getcwd()
    
    project_path = Path(project_dir)
    
    # If non-interactive (e.g., running via Cursor), just do it
    if not interactive:
        try:
            from .install_cursorflow_rules import install_cursorflow_rules
            return install_cursorflow_rules(project_dir, force=False)
        except Exception as e:
            print(f"⚠️  Auto-initialization failed: {e}", file=sys.stderr)
            print(f"💡 Run manually: cursorflow install-rules", file=sys.stderr)
            return False
    
    # Interactive mode: ask user
    if not sys.stdin.isatty():
        # Non-interactive environment (CI, pipes, etc) - auto-accept
        print("🎯 CursorFlow not initialized. Auto-initializing (non-interactive mode)...")
        response = 'y'
    else:
        print("\n🎯 CursorFlow is not initialized in this project yet.")
        print(f"📁 Project directory: {project_path}")
        print("\nTo use CursorFlow, we need to set up:")
        print("  • Cursor AI rules in .cursor/rules/")
        print("  • Configuration file: .cursorflow/config.json")
        print("  • Artifacts directory: .cursorflow/")
        print("  • .gitignore entries for CursorFlow artifacts")
        
        response = input("\n🚀 Initialize CursorFlow now? [Y/n]: ").strip().lower()
    
    if response in ('', 'y', 'yes'):
        try:
            from .install_cursorflow_rules import install_cursorflow_rules
            success = install_cursorflow_rules(project_dir, force=False)
            
            if success:
                print("\n✅ CursorFlow is ready to use!")
                print("💡 Start testing with: cursorflow test --help")
            
            return success
            
        except Exception as e:
            print(f"\n❌ Initialization failed: {e}", file=sys.stderr)
            print(f"💡 Try manually: cursorflow install-rules", file=sys.stderr)
            return False
    else:
        print("\n⏭️  Skipped initialization.")
        print("💡 Run later with: cursorflow install-rules")
        return False


def get_initialization_warning() -> str:
    """Get a friendly warning message for uninitialized projects"""
    
    return """
╔════════════════════════════════════════════════════════════════╗
║  🎯 CursorFlow Not Initialized                                 ║
╠════════════════════════════════════════════════════════════════╣
║                                                                 ║
║  CursorFlow requires project-specific setup to work properly.  ║
║                                                                 ║
║  Quick fix:                                                     ║
║    cursorflow install-rules                                     ║
║                                                                 ║
║  This creates:                                                  ║
║    • .cursor/rules/ (Cursor AI integration)                     ║
║    • .cursorflow/config.json (project configuration)            ║
║    • .cursorflow/ (artifacts and sessions)                      ║
║    • .gitignore entries                                         ║
║                                                                 ║
╚════════════════════════════════════════════════════════════════╝
"""


def ensure_initialized(project_dir: Optional[str] = None, auto_init: bool = False) -> None:
    """
    Ensure project is initialized, or raise helpful error
    
    Args:
        project_dir: Project directory
        auto_init: If True, automatically initialize without asking
        
    Raises:
        RuntimeError: If not initialized and user declines/can't initialize
    """
    if is_project_initialized(project_dir):
        return
    
    # Try auto-initialization
    interactive = not auto_init and sys.stdin.isatty()
    
    if auto_initialize_if_needed(project_dir, interactive=interactive):
        return
    
    # Failed to initialize
    print(get_initialization_warning(), file=sys.stderr)
    raise RuntimeError(
        "CursorFlow not initialized in this project. "
        "Run: cursorflow install-rules"
    )

