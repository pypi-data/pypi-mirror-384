#!/usr/bin/env python3
"""
CursorFlow Rules Installation Script

Installs CursorFlow usage rules into a user's project for Cursor AI.
Run this in your project directory to enable CursorFlow integration.
"""

import os
import shutil
import json
import datetime
from pathlib import Path
import argparse


def install_cursorflow_rules(project_dir: str = ".", force: bool = False):
    """Install CursorFlow rules and configuration in user's project"""
    
    project_path = Path(project_dir).resolve()
    print(f"🚀 Installing CursorFlow rules in: {project_path}")
    
    # Create .cursor directory if it doesn't exist
    cursor_dir = project_path / ".cursor"
    cursor_dir.mkdir(exist_ok=True)
    
    rules_dir = cursor_dir / "rules"
    rules_dir.mkdir(exist_ok=True)
    
    print(f"📁 Created Cursor rules directory: {rules_dir}")
    
    # Find CursorFlow package location
    try:
        import cursorflow
        package_dir = Path(cursorflow.__file__).parent
        rules_source_dir = package_dir / "rules"
    except ImportError:
        # Fallback: look for rules in current directory structure
        current_dir = Path(__file__).parent
        rules_source_dir = current_dir / "rules"  # Now rules are in cursorflow/rules/
        
    if not rules_source_dir.exists():
        print(f"❌ Could not find CursorFlow rules directory at: {rules_source_dir}")
        return False
    
    # Copy usage rules (always overwrite to ensure latest version)
    usage_rules = [
        "cursorflow-usage.mdc",
        "cursorflow-installation.mdc"
    ]
    
    copied_files = []
    for rule_file in usage_rules:
        source_file = rules_source_dir / rule_file
        target_file = rules_dir / rule_file
        
        if source_file.exists():
            # Check if target already exists before overwriting
            target_exists = target_file.exists()
            # Always overwrite to ensure latest rules on upgrade
            shutil.copy2(source_file, target_file)
            copied_files.append(rule_file)
            action = "Updated" if target_exists else "Installed"
            print(f"✅ {action}: {rule_file}")
        else:
            print(f"⚠️  Rule file not found: {rule_file}")
    
    # Create project-specific .gitignore entries
    create_gitignore_entries(project_path)
    
    # Create or update CursorFlow configuration template
    create_config_template(project_path, force=force)
    
    print(f"\n🎉 CursorFlow rules installation complete!")
    print(f"📋 Processed {len(copied_files)} rule files:")
    for file in copied_files:
        print(f"   - {file}")
    
    # Set up automatic update checking
    setup_update_checking(project_path)
    
    print(f"\n📝 Next steps:")
    print(f"   1. Review .cursorflow/config.json and update for your project")
    print(f"   2. Install Playwright: playwright install chromium")
    print(f"   3. Start using CursorFlow for UI testing and CSS iteration!")
    print(f"\n🔄 Update commands:")
    print(f"   - Check for updates: python -m cursorflow check-updates")
    print(f"   - Update CursorFlow: python -m cursorflow update")
    print(f"   - Install dependencies: python -m cursorflow install-deps")
    
    return True


def create_gitignore_entries(project_path: Path):
    """Add CursorFlow artifacts to .gitignore"""
    
    gitignore_path = project_path / ".gitignore"
    
    cursorflow_entries = """
# CursorFlow artifacts (UI testing framework)
.cursorflow/
*.cursorflow.log
cursorflow_session_*.json
"""
    
    # Check if entries already exist
    existing_content = ""
    if gitignore_path.exists():
        existing_content = gitignore_path.read_text()
    
    if ".cursorflow/" not in existing_content:
        with open(gitignore_path, "a") as f:
            f.write(cursorflow_entries)
        print("✅ Added CursorFlow entries to .gitignore")
    else:
        print("ℹ️  CursorFlow entries already in .gitignore")


def create_config_template(project_path: Path, force: bool = False):
    """Create or update CursorFlow configuration template"""
    
    # Create .cursorflow directory if it doesn't exist
    cursorflow_dir = project_path / ".cursorflow"
    cursorflow_dir.mkdir(exist_ok=True)
    
    config_path = cursorflow_dir / "config.json"
    
    # Get current version
    try:
        import cursorflow
        current_version = getattr(cursorflow, '__version__', '2.2.0')
    except ImportError:
        current_version = '2.2.0'
    
    if config_path.exists():
        if not force:
            print("ℹ️  .cursorflow/config.json already exists (use --force to recreate)")
            # Smart update: only update version and add missing fields
            try:
                with open(config_path) as f:
                    existing_config = json.load(f)
                
                updated = False
                
                # Update version if outdated
                if existing_config.get("_cursorflow_version") != current_version:
                    existing_config["_cursorflow_version"] = current_version
                    updated = True
                
                # Add missing browser section if it doesn't exist (new in v2.0)
                if "browser" not in existing_config:
                    existing_config["browser"] = {
                        "headless": True,
                        "debug_mode": False
                    }
                    updated = True
                    print("✅ Added new 'browser' configuration section")
                
                # Add missing auth session_storage if it doesn't exist
                if "auth" in existing_config and "session_storage" not in existing_config["auth"]:
                    existing_config["auth"]["session_storage"] = ".cursorflow/sessions/"
                    updated = True
                    print("✅ Added 'session_storage' to auth configuration")
                
                if updated:
                    with open(config_path, 'w') as f:
                        json.dump(existing_config, f, indent=2)
                    print(f"✅ Updated config to version {current_version} (preserved user settings)")
                else:
                    print(f"ℹ️  Configuration is current (version {current_version})")
                    
            except Exception as e:
                print(f"⚠️  Could not update config: {e}")
            return
        else:
            print("🔄 Force mode: Recreating configuration (user settings will be lost)")
    
    # Create new config or force recreate
    project_type = detect_project_type(project_path)
    
    config_template = {
        "base_url": get_default_url(project_type),
        "logs": get_default_log_config(project_type),
        "auth": {
            "method": "form",
            "username_selector": "#username",
            "password_selector": "#password", 
            "submit_selector": "#login-button",
            "session_storage": ".cursorflow/sessions/"
        },
        "browser": {
            "headless": True,
            "debug_mode": False
        },
        "_project_type": project_type,
        "_cursorflow_version": current_version
    }
    
    import json
    with open(config_path, "w") as f:
        json.dump(config_template, f, indent=2)
    
    action = "Recreated" if force else "Created"
    print(f"✅ {action} configuration: .cursorflow/config.json")
    print(f"   Detected project type: {project_type}")
    print(f"   CursorFlow version: {current_version}")


def detect_project_type(project_path: Path) -> str:
    """Detect project type for better defaults"""
    
    if (project_path / "package.json").exists():
        package_json = project_path / "package.json"
        try:
            import json
            with open(package_json) as f:
                package_data = json.load(f)
            
            dependencies = package_data.get("dependencies", {})
            dev_dependencies = package_data.get("devDependencies", {})
            all_deps = {**dependencies, **dev_dependencies}
            
            if "next" in all_deps:
                return "nextjs"
            elif "react" in all_deps:
                return "react"
            elif "vue" in all_deps:
                return "vue"
            else:
                return "nodejs"
        except:
            return "nodejs"
    
    elif (project_path / "manage.py").exists():
        return "django"
    
    elif (project_path / "composer.json").exists():
        return "php"
    
    elif (project_path / "Gemfile").exists():
        return "rails"
    
    elif any((project_path / f).exists() for f in ["*.pl", "*.pm"]):
        return "perl"
    
    else:
        return "generic"


def get_default_url(project_type: str) -> str:
    """Get default development server URL"""
    
    defaults = {
        "nextjs": "http://localhost:3000",
        "react": "http://localhost:3000",
        "vue": "http://localhost:8080",
        "nodejs": "http://localhost:3000",
        "django": "http://localhost:8000",
        "php": "http://localhost:8080",
        "rails": "http://localhost:3000",
        "perl": "http://localhost:8080",
        "generic": "http://localhost:3000"
    }
    
    return defaults.get(project_type, "http://localhost:3000")


def get_default_log_config(project_type: str) -> dict:
    """Get default log configuration"""
    
    log_configs = {
        "nextjs": {"source": "local", "paths": [".next/trace.log", "logs/app.log"]},
        "react": {"source": "local", "paths": ["logs/app.log", "console.log"]},
        "vue": {"source": "local", "paths": ["logs/app.log"]},
        "nodejs": {"source": "local", "paths": ["logs/app.log", "npm-debug.log"]},
        "django": {"source": "local", "paths": ["logs/django.log", "logs/debug.log"]},
        "php": {"source": "local", "paths": ["storage/logs/laravel.log", "logs/error.log"]},
        "rails": {"source": "local", "paths": ["log/development.log", "log/test.log"]},
        "perl": {"source": "ssh", "host": "staging-server", "paths": ["/var/log/httpd/error_log"]},
        "generic": {"source": "local", "paths": ["logs/app.log"]}
    }
    
    return log_configs.get(project_type, {"source": "local", "paths": ["logs/app.log"]})


def setup_update_checking(project_path: Path):
    """Set up automatic update checking configuration"""
    
    cursorflow_dir = project_path / ".cursorflow"
    cursorflow_dir.mkdir(exist_ok=True)
    
    # Create update preferences
    update_prefs = {
        "check_interval_hours": 24,
        "auto_update": False,
        "include_prereleases": False,
        "backup_before_update": True,
        "last_check": None
    }
    
    prefs_file = cursorflow_dir / "update_preferences.json"
    with open(prefs_file, 'w') as f:
        json.dump(update_prefs, f, indent=2)
    
    # Create initial version tracking
    try:
        import cursorflow
        current_version = getattr(cursorflow, '__version__', '2.2.0')
    except ImportError:
        current_version = '2.2.0'
    
    version_info = {
        "installed_version": current_version,
        "rules_version": current_version,
        "installation_date": str(datetime.datetime.now().isoformat())
    }
    
    version_file = cursorflow_dir / "version_info.json"
    with open(version_file, 'w') as f:
        json.dump(version_info, f, indent=2)
    
    print("✅ Update checking configured")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Install CursorFlow rules in a project")
    parser.add_argument("--project-dir", default=".", help="Project directory (default: current directory)")
    
    args = parser.parse_args()
    
    success = install_cursorflow_rules(args.project_dir)
    exit(0 if success else 1)
