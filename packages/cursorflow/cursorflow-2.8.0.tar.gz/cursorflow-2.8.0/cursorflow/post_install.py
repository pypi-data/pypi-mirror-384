#!/usr/bin/env python3
"""
Post-install message for CursorFlow

Shows important setup instructions after pip install.
"""

def show_post_install_message():
    """Display post-install instructions"""
    
    message = """
╔══════════════════════════════════════════════════════════════════════╗
║                                                                      ║
║  ✅ CursorFlow installed successfully!                               ║
║                                                                      ║
║  📋 IMPORTANT: One more step to enable CursorFlow in your project   ║
║                                                                      ║
║  Run this in your project directory:                                ║
║                                                                      ║
║    cd /path/to/your/project                                         ║
║    cursorflow install-rules                                         ║
║                                                                      ║
║  This creates:                                                       ║
║    • Cursor AI integration rules                                    ║
║    • Project-specific configuration                                 ║
║    • Artifacts directory structure                                  ║
║                                                                      ║
║  💡 Then install browser dependencies:                              ║
║                                                                      ║
║    playwright install chromium                                      ║
║                                                                      ║
║  🚀 After that, you can start testing:                              ║
║                                                                      ║
║    cursorflow test --base-url http://localhost:3000 --path /        ║
║                                                                      ║
║  📚 Documentation: https://github.com/haley-marketing-group/cursorflow ║
║                                                                      ║
╚══════════════════════════════════════════════════════════════════════╝
"""
    
    print(message)


if __name__ == "__main__":
    show_post_install_message()

