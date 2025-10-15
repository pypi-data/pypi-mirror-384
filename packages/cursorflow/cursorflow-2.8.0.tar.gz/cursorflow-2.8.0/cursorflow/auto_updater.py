"""
CursorFlow Auto-Update Integration

Automatic update checking and notification system for seamless
CursorFlow maintenance across projects.
"""

import asyncio
import json
import time
from pathlib import Path
from typing import Dict, Optional
import logging
from .updater import CursorFlowUpdater


class AutoUpdateManager:
    """
    Manages automatic update checking and notifications
    
    Integrates with CursorFlow initialization to check for updates
    periodically and notify users of available updates.
    """
    
    def __init__(self, project_dir: str = "."):
        self.project_dir = Path(project_dir).resolve()
        self.logger = logging.getLogger(__name__)
        self.updater = CursorFlowUpdater(str(self.project_dir))
        
        # Load preferences
        self.preferences = self._load_preferences()
    
    async def check_if_update_needed(self) -> Optional[Dict]:
        """
        Check if an update check is needed based on interval
        
        Returns:
            Update info if check was performed, None if not needed
        """
        try:
            # Check if enough time has passed
            if not self._should_check_for_updates():
                return None
            
            # Perform update check
            update_info = await self.updater.check_for_updates(silent=True)
            
            # Update last check time
            self._update_last_check_time()
            
            return update_info
            
        except Exception as e:
            self.logger.error(f"Auto-update check failed: {e}")
            return None
    
    async def notify_if_updates_available(self) -> bool:
        """
        Check for updates and notify if available
        
        Returns:
            True if updates are available, False otherwise
        """
        update_info = await self.check_if_update_needed()
        
        if not update_info:
            return False
        
        has_updates = (
            update_info.get("version_update_available", False) or
            update_info.get("rules_update_available", False) or
            not update_info.get("dependencies_current", True)
        )
        
        if has_updates:
            self._display_update_notification(update_info)
            return True
        
        return False
    
    def _should_check_for_updates(self) -> bool:
        """Check if enough time has passed for update check"""
        interval_hours = self.preferences.get("check_interval_hours", 24)
        last_check = self.preferences.get("last_check")
        
        if not last_check:
            return True
        
        try:
            last_check_time = time.fromisoformat(last_check)
            current_time = time.time()
            hours_elapsed = (current_time - last_check_time) / 3600
            
            return hours_elapsed >= interval_hours
        except Exception:
            return True
    
    def _load_preferences(self) -> Dict:
        """Load update preferences"""
        prefs_file = self.project_dir / ".cursorflow" / "update_preferences.json"
        
        if prefs_file.exists():
            try:
                with open(prefs_file) as f:
                    return json.load(f)
            except Exception:
                pass
        
        # Default preferences
        return {
            "check_interval_hours": 24,
            "auto_update": False,
            "include_prereleases": False,
            "backup_before_update": True,
            "last_check": None
        }
    
    def _update_last_check_time(self):
        """Update the last check timestamp"""
        prefs_file = self.project_dir / ".cursorflow" / "update_preferences.json"
        prefs_file.parent.mkdir(exist_ok=True)
        
        self.preferences["last_check"] = time.time()
        
        with open(prefs_file, 'w') as f:
            json.dump(self.preferences, f, indent=2)
    
    def _display_update_notification(self, update_info: Dict):
        """Display update notification"""
        print("\n" + "="*60)
        print("🔄 CursorFlow Updates Available!")
        print("="*60)
        
        if update_info.get("version_update_available"):
            current = update_info.get("current_version", "unknown")
            latest = update_info.get("latest_version", "unknown")
            print(f"📦 Package update: {current} → {latest}")
        
        if update_info.get("rules_update_available"):
            print("📝 Rules update available")
        
        if not update_info.get("dependencies_current"):
            print("🔧 Dependency updates available")
        
        print("\n💡 Update commands:")
        print("   cursorflow update              # Update everything")
        print("   cursorflow check-updates       # Check status")
        print("   cursorflow install-deps        # Update dependencies only")
        
        print("\n⚙️  To disable these notifications:")
        print("   Edit .cursorflow/update_preferences.json")
        print("   Set 'check_interval_hours' to 0")
        print("="*60)


async def check_for_updates_on_startup(project_dir: str = ".") -> bool:
    """
    Check for updates during CursorFlow startup
    
    Args:
        project_dir: Project directory path
        
    Returns:
        True if updates are available, False otherwise
    """
    try:
        manager = AutoUpdateManager(project_dir)
        return await manager.notify_if_updates_available()
    except Exception:
        return False


def integrate_with_cursorflow():
    """
    Integration point for CursorFlow main class
    
    Add this to CursorFlow.__init__ to enable auto-update checking
    """
    
    # Check for updates asynchronously in background
    async def background_update_check():
        try:
            await check_for_updates_on_startup()
        except Exception:
            pass  # Silent failure for background task
    
    # Schedule background check
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # If loop is already running, schedule as task
            loop.create_task(background_update_check())
        else:
            # If no loop running, run briefly
            asyncio.run(background_update_check())
    except Exception:
        pass  # Silent failure


class UpdateScheduler:
    """
    Schedules periodic update checks during CursorFlow usage
    """
    
    def __init__(self, project_dir: str = "."):
        self.project_dir = project_dir
        self.manager = AutoUpdateManager(project_dir)
        self._check_task = None
    
    def start_periodic_checking(self, interval_minutes: int = 60):
        """Start periodic update checking"""
        if self._check_task and not self._check_task.done():
            return  # Already running
        
        async def periodic_check():
            while True:
                try:
                    await self.manager.check_if_update_needed()
                    await asyncio.sleep(interval_minutes * 60)
                except asyncio.CancelledError:
                    break
                except Exception:
                    await asyncio.sleep(interval_minutes * 60)
        
        self._check_task = asyncio.create_task(periodic_check())
    
    def stop_periodic_checking(self):
        """Stop periodic update checking"""
        if self._check_task and not self._check_task.done():
            self._check_task.cancel()


# Singleton scheduler for global use
_global_scheduler = None


def get_update_scheduler(project_dir: str = ".") -> UpdateScheduler:
    """Get or create global update scheduler"""
    global _global_scheduler
    
    if _global_scheduler is None:
        _global_scheduler = UpdateScheduler(project_dir)
    
    return _global_scheduler
