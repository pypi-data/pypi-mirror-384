#!/usr/bin/env python3
"""
Hot Reload CSS Iteration Example

Demonstrates how CursorFlow takes advantage of hot reload environments
for rapid CSS iteration without page reloads.

This example shows:
1. Setting up persistent browser sessions
2. Using hot reload for faster CSS iterations
3. Maintaining application state between changes
4. Automatic detection of hot reload capabilities
5. Session management and optimization
"""

import asyncio
import json
from pathlib import Path

# Add cursorflow to path for example
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from cursorflow.core.cursorflow import CursorFlow


async def demonstrate_hot_reload_css_iteration():
    """
    Demonstrate CSS iteration with hot reload support
    
    This example assumes you have a development server running with hot reload
    (e.g., React with webpack HMR, Vite, or similar)
    """
    
    print("🚀 CursorFlow Hot Reload CSS Iteration Demo")
    print("=" * 60)
    
    # Configuration for hot reload environment
    config = {
        "base_url": "http://localhost:3000",  # Your dev server
        "log_config": {
            "source": "local",
            "paths": ["logs/app.log", ".next/trace.log"]
        },
        "browser_config": {
            "headless": False,  # Show browser for demonstration
            "debug_mode": True,
            "hot_reload_enabled": True,
            "keep_alive": True
        }
    }
    
    # Initialize CursorFlow
    flow = CursorFlow(
        base_url=config["base_url"],
        log_config=config["log_config"],
        browser_config=config["browser_config"]
    )
    
    try:
        print("\n📋 Step 1: Setting up persistent session for hot reload")
        
        # Base actions to set up the page
        base_actions = [
            {"navigate": "/dashboard"},  # Navigate to your component
            {"wait_for": "#main-content"},  # Wait for component to load
            {"screenshot": "baseline"}  # Capture initial state
        ]
        
        # CSS changes to test (these would come from Cursor's analysis)
        css_changes = [
            {
                "name": "improve-spacing",
                "css": """
                    .dashboard-container {
                        gap: 2rem;
                        padding: 1.5rem;
                    }
                    .card {
                        margin-bottom: 1rem;
                    }
                """,
                "rationale": "Improve visual hierarchy with better spacing"
            },
            {
                "name": "enhance-cards",
                "css": """
                    .dashboard-container {
                        gap: 2rem;
                        padding: 1.5rem;
                    }
                    .card {
                        margin-bottom: 1rem;
                        border-radius: 8px;
                        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                        transition: transform 0.2s ease;
                    }
                    .card:hover {
                        transform: translateY(-2px);
                    }
                """,
                "rationale": "Add visual polish with shadows and hover effects"
            },
            {
                "name": "responsive-layout",
                "css": """
                    .dashboard-container {
                        gap: 2rem;
                        padding: 1.5rem;
                        display: grid;
                        grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
                    }
                    .card {
                        margin-bottom: 1rem;
                        border-radius: 8px;
                        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                        transition: transform 0.2s ease;
                    }
                    .card:hover {
                        transform: translateY(-2px);
                    }
                    
                    @media (max-width: 768px) {
                        .dashboard-container {
                            gap: 1rem;
                            padding: 1rem;
                            grid-template-columns: 1fr;
                        }
                    }
                """,
                "rationale": "Make layout responsive across devices"
            }
        ]
        
        # Session options for persistent hot reload
        session_options = {
            "session_id": "dashboard_iteration_session",
            "reuse_session": True,  # Reuse existing session if available
            "hot_reload": True,     # Enable hot reload detection and usage
            "keep_session_alive": True  # Keep session alive after iteration
        }
        
        print(f"🔥 Starting CSS iteration with {len(css_changes)} changes...")
        print("   → Persistent session will be maintained")
        print("   → Hot reload will be detected and used automatically")
        print("   → Application state will be preserved")
        
        # Execute persistent CSS iteration
        results = await flow.css_iteration_persistent(
            base_actions=base_actions,
            css_changes=css_changes,
            session_options=session_options
        )
        
        # Display results
        print("\n📊 Results Summary:")
        print(f"   ✅ Success: {results.get('success', False)}")
        print(f"   🎯 Session ID: {results.get('session_id', 'N/A')}")
        print(f"   ⏱️  Execution Time: {results.get('execution_time', 0):.2f} seconds")
        print(f"   🔥 Hot Reload Used: {results.get('hot_reload_used', False)}")
        
        # Session information
        session_info = results.get("session_info", {})
        if session_info:
            print(f"\n🔧 Session Information:")
            print(f"   📈 Iteration Count: {session_info.get('iteration_count', 0)}")
            print(f"   🕐 Session Age: {session_info.get('age_seconds', 0):.0f} seconds")
            print(f"   🔥 Hot Reload Available: {session_info.get('hot_reload_available', False)}")
            print(f"   🌐 Current URL: {session_info.get('current_url', 'N/A')}")
        
        # Iteration results
        iterations = results.get("iterations", [])
        print(f"\n🎨 CSS Iteration Results ({len(iterations)} iterations):")
        
        for i, iteration in enumerate(iterations):
            status = "✅" if iteration.get("success", False) else "❌"
            method = "🔥 Hot Reload" if iteration.get("hot_reload_used", False) else "🔄 Standard"
            errors = len(iteration.get("console_errors", []))
            
            print(f"   {status} {iteration.get('name', f'Iteration {i+1}')}")
            print(f"      Method: {method}")
            print(f"      Console Errors: {errors}")
            if iteration.get("screenshot"):
                print(f"      Screenshot: {iteration.get('screenshot')}")
        
        # Recommendations
        recommendations = results.get("recommended_actions", [])
        if recommendations:
            print(f"\n💡 Recommendations:")
            for rec in recommendations:
                print(f"   🎯 {rec.get('action', 'Unknown')}: {rec.get('description', 'No description')}")
        
        # Session management
        session_context = results.get("session_context", {})
        if session_context:
            print(f"\n🔧 Session Management:")
            if session_context.get("session_persistent", False):
                print("   ✅ Session is persistent and ready for next iteration")
                if session_context.get("hot_reload_available", False):
                    print("   🔥 Hot reload is available and working")
                else:
                    print("   ⚠️  Hot reload not detected - consider setting up HMR")
            
            print(f"   📊 Session Stats:")
            print(f"      - Age: {session_context.get('session_age_seconds', 0):.0f} seconds")
            print(f"      - Iterations: {session_context.get('iteration_count', 0)}")
            print(f"      - Reused: {session_context.get('session_reused', False)}")
        
        # Persistent analysis
        persistent_analysis = results.get("persistent_analysis", {})
        if persistent_analysis:
            hot_reload_analysis = persistent_analysis.get("hot_reload_effectiveness", {})
            speed_metrics = persistent_analysis.get("iteration_speed_metrics", {})
            
            print(f"\n⚡ Performance Analysis:")
            if hot_reload_analysis:
                print(f"   🔥 Hot Reload Usage: {hot_reload_analysis.get('hot_reload_usage_rate', 0)*100:.0f}%")
                print(f"   💨 Quality: {hot_reload_analysis.get('hot_reload_quality', 'unknown')}")
            
            if speed_metrics:
                print(f"   ⏱️  Avg Iteration Time: {speed_metrics.get('average_iteration_time', 0):.2f}s")
                print(f"   🚀 Iterations/Minute: {speed_metrics.get('iterations_per_minute', 0):.1f}")
        
        # Show session continuation example
        print(f"\n🔄 Next Steps:")
        session_management = results.get("session_management", {})
        if session_management.get("keep_session_alive", False):
            print("   ✅ Session is being kept alive for next iteration")
            print("   🎯 You can continue with more CSS changes without reloading")
            print("   💡 Use the same session_id for instant continuation")
            
            # Example of continuing the session
            print(f"\n📝 Example: Continue with same session:")
            print(f"""
            # Continue iterating with the same session
            more_css_changes = [{{
                "name": "fine-tune-spacing",
                "css": ".card {{ padding: 1.25rem; }}",
                "rationale": "Fine-tune card padding"
            }}]
            
            results = await flow.css_iteration_persistent(
                base_actions=[],  # No base actions needed - session already set up
                css_changes=more_css_changes,
                session_options={{
                    "session_id": "{results.get('session_id', 'dashboard_iteration_session')}",
                    "reuse_session": True,  # Continue existing session
                    "hot_reload": True
                }}
            )
            """)
        
        # Save results for reference
        results_file = Path.cwd() / ".cursorflow" / "artifacts" / "hot_reload_demo_results.json"
        results_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Remove non-serializable objects for JSON saving
        serializable_results = {k: v for k, v in results.items() if k != "session_info"}
        
        with open(results_file, 'w') as f:
            json.dump(serializable_results, f, indent=2)
        
        print(f"\n💾 Results saved to: {results_file}")
        
        # Session information
        session_info_result = await flow.get_persistent_session_info()
        if session_info_result:
            print(f"\n📋 Active Session Info:")
            print(f"   ID: {session_info_result.get('session_id', 'N/A')}")
            print(f"   Active: {session_info_result.get('is_active', False)}")
            print(f"   Hot Reload: {session_info_result.get('hot_reload_available', False)}")
        
        return results
        
    except Exception as e:
        print(f"\n❌ Error during CSS iteration: {e}")
        return None
    
    finally:
        # Optionally clean up session (or keep it alive for next iteration)
        cleanup_session = False  # Set to True to clean up immediately
        
        if cleanup_session:
            print(f"\n🧹 Cleaning up session...")
            await flow.cleanup_persistent_session(save_state=True)
        else:
            print(f"\n✅ Session kept alive for future iterations")


async def demonstrate_session_management():
    """
    Demonstrate advanced session management features
    """
    
    print("\n" + "=" * 60)
    print("🔧 Session Management Demo")
    print("=" * 60)
    
    from cursorflow.core.persistent_session import get_session_manager
    
    session_manager = get_session_manager()
    
    # List all active sessions
    sessions = await session_manager.list_sessions()
    print(f"\n📋 Active Sessions ({len(sessions)}):")
    
    for session in sessions:
        print(f"   🔗 {session.get('session_id', 'N/A')}")
        print(f"      Age: {session.get('age_seconds', 0):.0f}s")
        print(f"      Hot Reload: {session.get('hot_reload_available', False)}")
        print(f"      Iterations: {session.get('iteration_count', 0)}")
        print()
    
    # Cleanup stale sessions
    print("🧹 Cleaning up stale sessions...")
    await session_manager.cleanup_stale_sessions()
    
    print("✅ Session management demo complete")


if __name__ == "__main__":
    print("🎯 CursorFlow Hot Reload CSS Iteration Example")
    print()
    print("This example demonstrates how CursorFlow takes advantage of hot reload")
    print("environments for rapid CSS iteration without page reloads.")
    print()
    print("Prerequisites:")
    print("  1. Development server running on http://localhost:3000")
    print("  2. Hot reload enabled (webpack HMR, Vite, etc.)")
    print("  3. A page/component at /dashboard")
    print()
    
    choice = input("Continue with demo? (y/n): ").lower().strip()
    if choice == 'y':
        try:
            results = asyncio.run(demonstrate_hot_reload_css_iteration())
            
            if results and results.get("success"):
                print("\n🎉 Demo completed successfully!")
                
                # Ask about session management demo
                choice = input("\nRun session management demo? (y/n): ").lower().strip()
                if choice == 'y':
                    asyncio.run(demonstrate_session_management())
            else:
                print("\n⚠️  Demo completed with issues - check your development server setup")
                
        except KeyboardInterrupt:
            print("\n\n🛑 Demo interrupted by user")
        except Exception as e:
            print(f"\n❌ Demo failed: {e}")
    else:
        print("Demo cancelled.")