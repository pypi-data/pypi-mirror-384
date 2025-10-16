"""
CursorFlow Update Manager

Handles automatic updates, dependency management, and rule synchronization
across projects. Ensures CursorFlow stays current everywhere it's used.
"""

import asyncio
import json
import subprocess
import sys
import urllib.request
import urllib.error
from pathlib import Path
from typing import Dict, List, Optional, Any
import logging
import shutil
import tempfile
import zipfile


class CursorFlowUpdater:
    """
    Comprehensive update manager for CursorFlow
    
    Handles:
    - Package updates via pip
    - Rule synchronization across projects
    - Dependency installation
    - Configuration migration
    - Rollback capabilities
    """
    
    def __init__(self, project_dir: str = "."):
        self.project_dir = Path(project_dir).resolve()
        self.logger = logging.getLogger(__name__)
        
        # Update configuration
        self.update_config = {
            "check_interval_hours": 24,
            "auto_update": False,
            "include_prereleases": False,
            "backup_before_update": True
        }
        
        # Load existing update preferences
        self._load_update_preferences()
        
        # GitHub repository info
        self.repo_info = {
            "owner": "haley-marketing-group",
            "repo": "cursorflow",
            "api_base": "https://api.github.com/repos/haley-marketing-group/cursorflow"
        }
    
    async def check_for_updates(self, silent: bool = False) -> Dict[str, Any]:
        """
        Check for CursorFlow updates
        
        Args:
            silent: If True, don't print status messages
            
        Returns:
            Update information dictionary
        """
        if not silent:
            print("🔍 Checking for CursorFlow updates...")
        
        try:
            # Get current version
            current_version = self._get_current_version()
            
            # Get latest version from PyPI
            latest_version = await self._get_latest_pypi_version()
            
            # Get latest rules version from GitHub
            latest_rules_version = await self._get_latest_rules_version()
            current_rules_version = self._get_current_rules_version()
            
            update_info = {
                "current_version": current_version,
                "latest_version": latest_version,
                "version_update_available": self._is_newer_version(latest_version, current_version),
                "current_rules_version": current_rules_version,
                "latest_rules_version": latest_rules_version,
                "rules_update_available": self._is_newer_version(latest_rules_version, current_rules_version),
                "dependencies_current": await self._check_dependencies(),
                "last_check": self._get_current_timestamp()
            }
            
            # Save last check info
            self._save_update_info(update_info)
            
            if not silent:
                self._display_update_status(update_info)
            
            return update_info
            
        except Exception as e:
            self.logger.error(f"Update check failed: {e}")
            return {"error": str(e), "last_check": self._get_current_timestamp()}
    
    async def update_cursorflow(self, force: bool = False) -> bool:
        """
        Update CursorFlow package and rules
        
        Args:
            force: Force update even if no updates available
            
        Returns:
            True if update successful, False otherwise
        """
        print("🚀 Starting CursorFlow update process...")
        
        try:
            # Check what needs updating
            update_info = await self.check_for_updates(silent=True)
            
            if not force and not (update_info.get("version_update_available") or 
                                update_info.get("rules_update_available")):
                print("✅ CursorFlow is already up to date!")
                return True
            
            # Create backup if enabled
            if self.update_config.get("backup_before_update", True):
                backup_path = await self._create_backup()
                print(f"📦 Backup created: {backup_path}")
            
            success = True
            
            # Update package if needed
            if force or update_info.get("version_update_available"):
                print("📥 Updating CursorFlow package...")
                if await self._update_package():
                    print("✅ Package updated successfully")
                else:
                    print("❌ Package update failed")
                    success = False
            
            # Update rules if needed  
            if force or update_info.get("rules_update_available"):
                print("📝 Updating CursorFlow rules...")
                if await self._update_rules():
                    print("✅ Rules updated successfully")
                else:
                    print("❌ Rules update failed")
                    success = False
            
            # Update dependencies
            print("🔧 Checking dependencies...")
            if await self._update_dependencies():
                print("✅ Dependencies updated")
            else:
                print("⚠️  Some dependency updates failed")
            
            # Update configuration if needed
            if await self._migrate_configuration():
                print("✅ Configuration updated")
            
            # Verify installation
            if await self._verify_installation():
                print("🎉 CursorFlow update completed successfully!")
                return success
            else:
                print("❌ Update verification failed")
                return False
                
        except Exception as e:
            self.logger.error(f"Update failed: {e}")
            print(f"❌ Update failed: {e}")
            return False
    
    async def install_dependencies(self) -> bool:
        """Install all required dependencies"""
        print("🔧 Installing CursorFlow dependencies...")
        
        dependencies = [
            "playwright>=1.40.0",
            "paramiko>=3.0.0", 
            "watchdog>=3.0.0",
            "click>=8.0.0",
            "rich>=13.0.0"
        ]
        
        try:
            # Install Python dependencies
            for dep in dependencies:
                print(f"   Installing {dep}...")
                result = subprocess.run([
                    sys.executable, "-m", "pip", "install", dep
                ], capture_output=True, text=True)
                
                if result.returncode != 0:
                    print(f"   ❌ Failed to install {dep}: {result.stderr}")
                    return False
                else:
                    print(f"   ✅ {dep} installed")
            
            # Install Playwright browsers
            print("   Installing Playwright browsers...")
            result = subprocess.run([
                sys.executable, "-m", "playwright", "install", "chromium"
            ], capture_output=True, text=True)
            
            if result.returncode != 0:
                print(f"   ⚠️  Playwright browser install failed: {result.stderr}")
                print("   You may need to run: playwright install chromium")
            else:
                print("   ✅ Playwright browsers installed")
            
            return True
            
        except Exception as e:
            print(f"❌ Dependency installation failed: {e}")
            return False
    
    async def update_project_rules(self, force: bool = False) -> bool:
        """Update rules in current project"""
        print("📝 Updating project rules...")
        
        try:
            # Download latest rules
            rules_dir = self.project_dir / ".cursor" / "rules"
            rules_dir.mkdir(parents=True, exist_ok=True)
            
            rules_to_update = [
                "cursorflow-usage.mdc",
                "cursorflow-installation.mdc"
            ]
            
            for rule_file in rules_to_update:
                print(f"   Updating {rule_file}...")
                
                # Download from GitHub
                url = f"https://raw.githubusercontent.com/haley-marketing-group/cursorflow/main/rules/{rule_file}"
                
                try:
                    with urllib.request.urlopen(url) as response:
                        content = response.read().decode('utf-8')
                    
                    # Write to project
                    rule_path = rules_dir / rule_file
                    with open(rule_path, 'w') as f:
                        f.write(content)
                    
                    print(f"   ✅ {rule_file} updated")
                    
                except urllib.error.URLError as e:
                    print(f"   ❌ Failed to download {rule_file}: {e}")
                    return False
            
            # Update rules version tracking
            self._save_rules_version()
            
            return True
            
        except Exception as e:
            print(f"❌ Rules update failed: {e}")
            return False
    
    def _get_current_version(self) -> str:
        """Get currently installed CursorFlow version"""
        try:
            import cursorflow
            return getattr(cursorflow, '__version__', '0.0.0')
        except ImportError:
            return '0.0.0'
    
    async def _get_latest_pypi_version(self) -> str:
        """Get latest version from PyPI"""
        try:
            url = "https://pypi.org/pypi/cursorflow/json"
            with urllib.request.urlopen(url) as response:
                data = json.loads(response.read())
            return data["info"]["version"]
        except Exception:
            return "0.0.0"
    
    async def _get_latest_rules_version(self) -> str:
        """Get latest rules version from GitHub"""
        try:
            url = f"{self.repo_info['api_base']}/releases/latest"
            with urllib.request.urlopen(url) as response:
                data = json.loads(response.read())
            return data["tag_name"].lstrip('v')
        except Exception:
            return "0.0.0"
    
    def _get_current_rules_version(self) -> str:
        """Get current rules version in project"""
        version_file = self.project_dir / ".cursorflow" / "rules_version.json"
        if version_file.exists():
            try:
                with open(version_file) as f:
                    data = json.load(f)
                return data.get("version", "0.0.0")
            except Exception:
                pass
        return "0.0.0"
    
    def _is_newer_version(self, latest: str, current: str) -> bool:
        """Compare version strings"""
        try:
            latest_parts = [int(x) for x in latest.split('.')]
            current_parts = [int(x) for x in current.split('.')]
            
            # Pad shorter version with zeros
            max_len = max(len(latest_parts), len(current_parts))
            latest_parts.extend([0] * (max_len - len(latest_parts)))
            current_parts.extend([0] * (max_len - len(current_parts)))
            
            return latest_parts > current_parts
        except Exception:
            return False
    
    async def _check_dependencies(self) -> bool:
        """Check if all dependencies are current"""
        try:
            import playwright
            import paramiko
            import watchdog
            return True
        except ImportError:
            return False
    
    async def _update_package(self) -> bool:
        """Update CursorFlow package via pip"""
        try:
            result = subprocess.run([
                sys.executable, "-m", "pip", "install", "--upgrade", "cursorflow"
            ], capture_output=True, text=True)
            
            return result.returncode == 0
        except Exception:
            return False
    
    async def _update_rules(self) -> bool:
        """Update rules from installed package"""
        print("📝 Updating CursorFlow rules from installed package...")
        
        try:
            # Use the install_cursorflow_rules function to get latest rules from package
            from .install_cursorflow_rules import install_cursorflow_rules
            
            # Install rules from the newly updated package
            success = install_cursorflow_rules(str(self.project_dir))
            
            if success:
                print("✅ Rules updated from installed package")
                return True
            else:
                print("❌ Failed to update rules from package")
                return False
                
        except Exception as e:
            self.logger.error(f"Rules update failed: {e}")
            print(f"❌ Rules update failed: {e}")
            return False
    
    async def _update_dependencies(self) -> bool:
        """Update all dependencies"""
        return await self.install_dependencies()
    
    async def _migrate_configuration(self) -> bool:
        """Migrate configuration to new format if needed"""
        config_file = self.project_dir / ".cursorflow" / "config.json"
        
        if not config_file.exists():
            return True
        
        try:
            with open(config_file) as f:
                config = json.load(f)
            
            # Add new fields if missing
            updated = False
            
            if "_cursorflow_version" not in config:
                config["_cursorflow_version"] = self._get_current_version()
                updated = True
            
            if "browser" not in config:
                config["browser"] = {"headless": True, "debug_mode": False}
                updated = True
            
            if updated:
                with open(config_file, 'w') as f:
                    json.dump(config, f, indent=2)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Configuration migration failed: {e}")
            return False
    
    async def _verify_installation(self) -> bool:
        """Verify that CursorFlow is working after update"""
        try:
            # Try importing
            import cursorflow
            
            # Check core components
            from cursorflow import CursorFlow
            from cursorflow.core.css_iterator import CSSIterator
            
            return True
        except Exception:
            return False
    
    async def _create_backup(self) -> str:
        """Create backup of current installation"""
        backup_dir = self.project_dir / ".cursorflow" / "backups"
        backup_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = self._get_current_timestamp()
        backup_name = f"backup_{timestamp}"
        backup_path = backup_dir / backup_name
        
        # Backup configuration and rules
        config_file = self.project_dir / ".cursorflow" / "config.json"
        if config_file.exists():
            shutil.copy2(
                config_file,
                backup_path.with_suffix('.config.json')
            )
        
        rules_dir = self.project_dir / ".cursor" / "rules"
        if rules_dir.exists():
            shutil.copytree(rules_dir, backup_path.with_suffix('.rules'), dirs_exist_ok=True)
        
        return str(backup_path)
    
    def _load_update_preferences(self):
        """Load update preferences from project"""
        prefs_file = self.project_dir / ".cursorflow" / "update_preferences.json"
        if prefs_file.exists():
            try:
                with open(prefs_file) as f:
                    prefs = json.load(f)
                self.update_config.update(prefs)
            except Exception:
                pass
    
    def _save_update_info(self, update_info: Dict):
        """Save update check information"""
        info_dir = self.project_dir / ".cursorflow"
        info_dir.mkdir(exist_ok=True)
        
        info_file = info_dir / "update_info.json"
        with open(info_file, 'w') as f:
            json.dump(update_info, f, indent=2)
    
    def _save_rules_version(self):
        """Save current rules version"""
        version_dir = self.project_dir / ".cursorflow"
        version_dir.mkdir(exist_ok=True)
        
        version_file = version_dir / "rules_version.json"
        with open(version_file, 'w') as f:
            json.dump({
                "version": self._get_current_version(),
                "updated": self._get_current_timestamp()
            }, f, indent=2)
    
    def _get_current_timestamp(self) -> str:
        """Get current timestamp string"""
        import datetime
        return datetime.datetime.now().isoformat()
    
    def _display_update_status(self, update_info: Dict):
        """Display update status to user"""
        current_version = update_info.get("current_version", "unknown")
        latest_version = update_info.get("latest_version", "unknown")
        
        print(f"📦 Current version: {current_version}")
        print(f"🌟 Latest version: {latest_version}")
        
        if update_info.get("version_update_available"):
            print("🔄 Package update available!")
        
        if update_info.get("rules_update_available"):
            print("📝 Rules update available!")
        
        if not update_info.get("dependencies_current"):
            print("🔧 Dependency updates needed!")
        
        if not (update_info.get("version_update_available") or 
                update_info.get("rules_update_available")):
            print("✅ CursorFlow is up to date!")


async def check_updates(project_dir: str = ".") -> Dict[str, Any]:
    """Convenience function to check for updates"""
    updater = CursorFlowUpdater(project_dir)
    return await updater.check_for_updates()


async def update_cursorflow(project_dir: str = ".", force: bool = False) -> bool:
    """Convenience function to update CursorFlow"""
    updater = CursorFlowUpdater(project_dir)
    return await updater.update_cursorflow(force=force)


async def install_dependencies(project_dir: str = ".") -> bool:
    """Convenience function to install dependencies"""
    updater = CursorFlowUpdater(project_dir)
    return await updater.install_dependencies()


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="CursorFlow Update Manager")
    parser.add_argument("--check", action="store_true", help="Check for updates")
    parser.add_argument("--update", action="store_true", help="Update CursorFlow")
    parser.add_argument("--install-deps", action="store_true", help="Install dependencies")
    parser.add_argument("--force", action="store_true", help="Force update")
    parser.add_argument("--project-dir", default=".", help="Project directory")
    
    args = parser.parse_args()
    
    if args.check:
        result = asyncio.run(check_updates(args.project_dir))
        print(json.dumps(result, indent=2))
    elif args.update:
        success = asyncio.run(update_cursorflow(args.project_dir, force=args.force))
        sys.exit(0 if success else 1)
    elif args.install_deps:
        success = asyncio.run(install_dependencies(args.project_dir))
        sys.exit(0 if success else 1)
    else:
        parser.print_help()
