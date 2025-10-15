#!/usr/bin/env python3
"""
CursorFlow v2.0.0 Comprehensive Example

This example demonstrates all the breakthrough features introduced in v2.0.0:
- 🔥 Hot Reload Intelligence with framework auto-detection
- 🧠 Advanced Element Intelligence with 7 selector strategies
- 📊 Comprehensive Page Analysis (fonts, animations, resources, storage)
- 🎯 Enhanced Error Context Collection with smart deduplication
- ⚡ Enhanced Browser Data Capture with Playwright traces

Perfect for understanding the complete v2.0.0 capabilities.
"""

import asyncio
import json
import logging
from pathlib import Path
from typing import Dict, Any
from cursorflow import CursorFlow

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def demonstrate_v2_hot_reload_intelligence():
    """
    🔥 v2.0.0 Breakthrough: Hot Reload Intelligence
    
    Demonstrates precision CSS iteration with HMR event detection.
    Works with Vite, Webpack, Next.js, Parcel, and Laravel Mix.
    """
    print("\n🔥 DEMO 1: Hot Reload Intelligence")
    print("=" * 50)
    
    # Connect to development server (auto-detects framework)
    flow = CursorFlow("http://localhost:5173", {"headless": False})
    
    try:
        # Start HMR monitoring with framework auto-detection
        print("🔍 Auto-detecting development framework...")
        await flow.browser.start_hmr_monitoring()
        
        # Get HMR status
        hmr_status = await flow.browser.get_hmr_status()
        if hmr_status['is_monitoring']:
            print(f"✅ HMR monitoring active for: {hmr_status['detected_framework']}")
        else:
            print("⚠️  No HMR framework detected - continuing with standard timing")
        
        # Take baseline screenshot
        print("📸 Capturing baseline...")
        baseline = await flow.execute_and_collect([
            {"navigate": "/app"},
            {"wait_for": "body"},
            {"screenshot": "hmr-baseline"}
        ])
        
        baseline_path = baseline['artifacts']['screenshots'][0]['path']
        print(f"✅ Baseline: {baseline_path}")
        
        # Wait for CSS changes (with HMR precision or fallback)
        print("\n⏳ Waiting for CSS changes...")
        print("   💡 Make some CSS changes in your editor!")
        print("   💡 CursorFlow will detect the exact moment they're applied")
        
        if hmr_status['is_monitoring']:
            # 🔥 v2.0.0 Precision: Wait for exact HMR event
            hmr_event = await flow.browser.wait_for_css_update(timeout=60)
            if hmr_event:
                print(f"🔥 HMR event detected!")
                print(f"   Framework: {hmr_event.get('framework', 'Unknown')}")
                print(f"   Event Type: {hmr_event.get('event_type', 'css_update')}")
                print(f"   Timestamp: {hmr_event.get('timestamp', 'N/A')}")
            else:
                print("⏰ No HMR event detected within timeout")
        else:
            # Fallback: Wait a reasonable amount of time
            print("⏰ Using fallback timing (5 seconds)...")
            await asyncio.sleep(5)
        
        # Capture immediately after changes
        print("📸 Capturing after changes...")
        updated = await flow.execute_and_collect([
            {"screenshot": "hmr-updated"}
        ])
        
        updated_path = updated['artifacts']['screenshots'][0]['path']
        print(f"✅ Updated: {updated_path}")
        
        # Show HMR correlation data
        if 'hmr_status' in updated['artifacts']['screenshots'][0]:
            hmr_data = updated['artifacts']['screenshots'][0]['hmr_status']
            print(f"\n📊 HMR Intelligence:")
            print(f"   Framework: {hmr_data.get('framework', 'Not detected')}")
            print(f"   Events captured: {hmr_data.get('events_count', 0)}")
        
        await flow.browser.stop_hmr_monitoring()
        print("🎉 HMR demonstration completed!")
        
    except Exception as e:
        logger.error(f"HMR demo error: {e}")
        print(f"❌ HMR demo failed: {e}")


async def demonstrate_v2_advanced_element_intelligence():
    """
    🧠 v2.0.0: Advanced Element Intelligence
    
    Demonstrates multi-selector strategies and comprehensive accessibility analysis.
    """
    print("\n🧠 DEMO 2: Advanced Element Intelligence")
    print("=" * 50)
    
    flow = CursorFlow("http://localhost:3000", {"headless": True})
    
    try:
        # Capture page with advanced element analysis
        results = await flow.execute_and_collect([
            {"navigate": "/form"},
            {"wait_for": "body"},
            {"screenshot": "element-intelligence"}
        ])
        
        elements = results['artifacts']['screenshots'][0]['dom_analysis']['elements']
        
        print(f"📊 Analyzed {len(elements)} elements with v2.0.0 intelligence")
        print("\n🔍 Sample Element Analysis:")
        
        # Show detailed analysis for first few interactive elements
        interactive_elements = [e for e in elements if e.get('accessibility', {}).get('interactive', False)][:3]
        
        for i, element in enumerate(interactive_elements, 1):
            print(f"\n📍 Element {i}: {element['selector']}")
            
            # 🆕 v2.0.0: Multiple selector strategies
            print("   🎯 Selector Strategies:")
            for strategy, selector in element['selectors'].items():
                print(f"      {strategy}: {selector}")
            
            # 🆕 v2.0.0: Accessibility intelligence
            accessibility = element['accessibility']
            print("   ♿ Accessibility:")
            print(f"      Role: {accessibility.get('role', 'None')}")
            print(f"      Focusable: {accessibility.get('focusable', False)}")
            print(f"      Interactive: {accessibility.get('interactive', False)}")
            print(f"      ARIA Label: {accessibility.get('aria_label', 'None')}")
            
            # 🆕 v2.0.0: Visual context
            visual = element['visual_context']
            visibility = visual['visibility']
            print("   👁️  Visual Context:")
            print(f"      Visible: {visibility['is_visible']}")
            print(f"      In Viewport: {visibility['in_viewport']}")
            print(f"      Opacity: {visibility['opacity']}")
            
            # Bounding box
            bbox = visual['bounding_box']
            print(f"      Position: ({bbox['x']}, {bbox['y']})")
            print(f"      Size: {bbox['width']}x{bbox['height']}")
        
        # Page structure analysis
        page_structure = results['artifacts']['screenshots'][0]['dom_analysis']['pageStructure']
        print(f"\n📊 Page Structure Intelligence:")
        print(f"   Total elements: {page_structure['totalElements']}")
        
        # 🆕 v2.0.0: Accessibility features
        a11y_features = page_structure['accessibilityFeatures']
        print(f"   Accessibility Features:")
        print(f"      Landmark elements: {a11y_features['landmarkElements']}")
        print(f"      Focusable elements: {a11y_features['focusableElements']}")
        print(f"      Interactive elements: {a11y_features['interactiveElements']}")
        print(f"      ARIA labels: {a11y_features['ariaLabels']}")
        
        # 🆕 v2.0.0: Visual features
        visual_features = page_structure['visualFeatures']
        print(f"   Visual Features:")
        print(f"      Visible elements: {visual_features['visibleElements']}")
        print(f"      In-viewport elements: {visual_features['inViewportElements']}")
        print(f"      Layered elements: {visual_features['layeredElements']}")
        
        print("🎉 Advanced element intelligence demonstration completed!")
        
    except Exception as e:
        logger.error(f"Element intelligence demo error: {e}")
        print(f"❌ Element intelligence demo failed: {e}")


async def demonstrate_v2_comprehensive_page_analysis():
    """
    📊 v2.0.0: Comprehensive Page Analysis
    
    Demonstrates font loading, animation tracking, resource analysis, and storage state.
    """
    print("\n📊 DEMO 3: Comprehensive Page Analysis")
    print("=" * 50)
    
    flow = CursorFlow("http://localhost:3000", {"headless": True})
    
    try:
        # Capture page with comprehensive analysis
        results = await flow.execute_and_collect([
            {"navigate": "/dashboard"},
            {"wait_for": "body"},
            {"screenshot": "comprehensive-analysis"}
        ])
        
        screenshot_data = results['artifacts']['screenshots'][0]
        
        # 🆕 v2.0.0: Font Loading Intelligence
        print("🔤 Font Loading Intelligence:")
        font_status = screenshot_data['font_status']
        print(f"   Total fonts: {font_status['totalFonts']}")
        print(f"   Loaded: {font_status['loadedFonts']}")
        print(f"   Loading: {font_status['loadingFonts']}")
        print(f"   Failed: {font_status['failedFonts']}")
        
        if font_status['fontDetails']:
            print("   Font Details:")
            for font in font_status['fontDetails'][:3]:  # Show first 3
                print(f"      {font['family']} {font['weight']}: {font['status']}")
        
        loading_metrics = font_status['loadingMetrics']
        print(f"   Performance: avg {loading_metrics['averageLoadTime']}ms")
        
        # 🆕 v2.0.0: Animation State Tracking
        print("\n🎬 Animation Intelligence:")
        animation_status = screenshot_data['animation_status']
        print(f"   Animated elements: {animation_status['totalAnimatedElements']}")
        print(f"   Running animations: {animation_status['runningAnimations']}")
        print(f"   Paused animations: {animation_status['pausedAnimations']}")
        print(f"   Finished animations: {animation_status['finishedAnimations']}")
        print(f"   Active transitions: {animation_status['runningTransitions']}")
        
        if animation_status['animationDetails']:
            print("   Animation Details:")
            for anim in animation_status['animationDetails'][:2]:  # Show first 2
                print(f"      {anim['name']}: {anim['duration']}ms, {anim['playState']}")
        
        # 🆕 v2.0.0: Resource Loading Analysis
        print("\n📦 Resource Intelligence:")
        resource_status = screenshot_data['resource_status']
        print(f"   Total resources: {resource_status['totalResources']}")
        print(f"   By type: {resource_status['resourcesByType']}")
        
        performance = resource_status['loadingPerformance']
        print(f"   Performance:")
        print(f"      Fastest: {performance['fastestResource']['name']} ({performance['fastestResource']['loadTime']}ms)")
        print(f"      Slowest: {performance['slowestResource']['name']} ({performance['slowestResource']['loadTime']}ms)")
        print(f"      Average: {performance['averageLoadTime']}ms")
        print(f"      Total size: {performance['totalSize']:,} bytes")
        
        if resource_status['criticalResources']:
            print(f"   Critical resources: {len(resource_status['criticalResources'])}")
        
        # 🆕 v2.0.0: Storage State Analysis
        print("\n💾 Storage Intelligence:")
        storage_status = screenshot_data['storage_status']
        
        local_storage = storage_status['localStorage']
        print(f"   localStorage: {local_storage['itemCount']} items ({local_storage['estimatedSize']} bytes)")
        if local_storage['keys']:
            print(f"      Keys: {', '.join(local_storage['keys'][:3])}{'...' if len(local_storage['keys']) > 3 else ''}")
        
        session_storage = storage_status['sessionStorage']
        print(f"   sessionStorage: {session_storage['itemCount']} items ({session_storage['estimatedSize']} bytes)")
        
        cookies = storage_status['cookies']
        print(f"   Cookies: {cookies['count']} cookies ({cookies['estimatedSize']} bytes)")
        
        indexeddb = storage_status['indexedDB']
        print(f"   IndexedDB: {'Available' if indexeddb['available'] else 'Not available'}")
        if indexeddb['available'] and indexeddb.get('databases'):
            print(f"      Databases: {', '.join(indexeddb['databases'])}")
        
        print("🎉 Comprehensive page analysis demonstration completed!")
        
    except Exception as e:
        logger.error(f"Comprehensive analysis demo error: {e}")
        print(f"❌ Comprehensive analysis demo failed: {e}")


async def demonstrate_v2_enhanced_error_context():
    """
    🎯 v2.0.0: Enhanced Error Context Collection
    
    Demonstrates smart error diagnostics with screenshot deduplication.
    """
    print("\n🎯 DEMO 4: Enhanced Error Context Collection")
    print("=" * 50)
    
    flow = CursorFlow("http://localhost:3000", {"headless": True})
    
    try:
        # Initialize browser
        await flow.browser.initialize()
        
        # Simulate multiple errors in quick succession
        errors = [
            {"type": "validation_error", "field": "email", "message": "Invalid email format"},
            {"type": "validation_error", "field": "password", "message": "Password too short"},
            {"type": "network_error", "request": "/api/login", "status": 500}
        ]
        
        print("🔍 Simulating multiple errors with smart context collection...")
        
        for i, error in enumerate(errors, 1):
            print(f"\n📍 Error {i}: {error['type']}")
            
            # 🆕 v2.0.0: Smart error context with deduplication
            context = await flow.browser.capture_interaction_error_context(
                action_description=f"Handle {error['type']} for {error.get('field', error.get('request', 'unknown'))}",
                error_details=error
            )
            
            # Analyze screenshot info
            screenshot_info = context['screenshot_info']
            print(f"   📸 Screenshot: {Path(screenshot_info['path']).name}")
            print(f"   📸 Reused: {screenshot_info['is_reused']}")
            
            if screenshot_info['is_reused']:
                print(f"   📸 Reason: {screenshot_info['reason']}")
                if 'shared_with_errors' in screenshot_info:
                    print(f"   📸 Shared with: {screenshot_info['shared_with_errors']} errors")
            
            # Context richness
            print(f"   🔍 DOM snapshot: {'Available' if context['dom_snapshot'] else 'None'}")
            print(f"   🌐 Network context: {len(context['network_context'])} requests")
            print(f"   📝 Console context: {len(context['console_context'])} entries")
            print(f"   🎯 Recent actions: {len(context['recent_actions'])} actions")
            print(f"   👁️  Element visibility: {len(context['element_visibility_map'])} elements")
            
            # Show recent actions if any
            if context['recent_actions']:
                print("   Recent actions:")
                for action in context['recent_actions'][-2:]:  # Show last 2
                    print(f"      {action['action_type']}: {action.get('details', {})}")
        
        # Get summary of all error contexts
        summary = await flow.browser.get_error_context_summary()
        print(f"\n📊 Error Context Summary:")
        print(f"   Total errors collected: {summary['total_errors_collected']}")
        print(f"   Unique screenshots: {summary['total_diagnostic_screenshots']}")
        print(f"   Deduplication rate: {summary['screenshot_deduplication_rate']}")
        print(f"   Error types: {', '.join(summary['unique_error_types'])}")
        
        print("🎉 Enhanced error context demonstration completed!")
        
    except Exception as e:
        logger.error(f"Error context demo error: {e}")
        print(f"❌ Error context demo failed: {e}")


async def demonstrate_v2_enhanced_browser_data_capture():
    """
    ⚡ v2.0.0: Enhanced Browser Data Capture
    
    Demonstrates Playwright trace integration and advanced network analysis.
    """
    print("\n⚡ DEMO 5: Enhanced Browser Data Capture")
    print("=" * 50)
    
    flow = CursorFlow("http://localhost:3000", {"headless": True})
    
    try:
        # Start trace recording
        print("🎬 Starting Playwright trace recording...")
        trace_path = await flow.browser.trace_manager.start_trace(
            flow.browser.context, 
            "v2_demo_session"
        )
        print(f"✅ Trace recording started")
        
        # Perform actions with enhanced data capture
        results = await flow.execute_and_collect([
            {"navigate": "/api-test"},
            {"wait_for": "body"},
            {"click": "#fetch-data"},
            {"wait": 2},
            {"screenshot": "enhanced-capture"}
        ])
        
        # Stop trace recording
        final_trace_path = await flow.browser.trace_manager.stop_trace(flow.browser.context)
        print(f"✅ Trace saved: {final_trace_path}")
        
        # Analyze enhanced data
        screenshot_data = results['artifacts']['screenshots'][0]
        
        # 🆕 v2.0.0: Enhanced network data
        print("\n🌐 Enhanced Network Intelligence:")
        network_data = screenshot_data['network_data']
        print(f"   Total requests: {len(network_data['requests'])}")
        
        for request in network_data['requests'][:3]:  # Show first 3
            print(f"   📡 {request['method']} {request['url']}")
            print(f"      Status: {request['status']}")
            print(f"      Size: {request.get('response_size', 'Unknown')} bytes")
            
            # 🆕 v2.0.0: Error analysis
            if 'error_analysis' in request:
                error_analysis = request['error_analysis']
                print(f"      Category: {error_analysis['category']}")
                if error_analysis.get('cause'):
                    print(f"      Cause: {error_analysis['cause']}")
        
        # 🆕 v2.0.0: Performance metrics with reliability
        print("\n⚡ Performance Intelligence:")
        performance = screenshot_data['performance_data']
        
        # Navigation timing
        navigation = performance['navigation']
        print(f"   Navigation:")
        print(f"      DOM Content Loaded: {navigation.get('domContentLoaded', 'N/A')}ms")
        print(f"      Load Complete: {navigation.get('loadComplete', 'N/A')}ms")
        
        # Paint timing
        paint = performance['paint']
        print(f"   Paint:")
        print(f"      First Paint: {paint.get('firstPaint', 'N/A')}ms")
        print(f"      First Contentful Paint: {paint.get('firstContentfulPaint', 'N/A')}ms")
        
        # 🆕 v2.0.0: Reliability indicators
        if '_reliability' in performance:
            reliability = performance['_reliability']
            print(f"   Reliability:")
            print(f"      Navigation timing: {reliability.get('navigation_timing', 'Unknown')}")
            print(f"      Paint timing: {reliability.get('paint_timing', 'Unknown')}")
            if reliability.get('note'):
                print(f"      Note: {reliability['note']}")
        
        # Console data with correlation
        print(f"\n📝 Console Intelligence:")
        console_data = screenshot_data['console_data']
        print(f"   Total entries: {len(console_data['logs'])}")
        
        # Show errors and warnings
        errors = [log for log in console_data['logs'] if log['level'] == 'error']
        warnings = [log for log in console_data['logs'] if log['level'] == 'warning']
        print(f"   Errors: {len(errors)}")
        print(f"   Warnings: {len(warnings)}")
        
        if errors:
            print("   Recent errors:")
            for error in errors[-2:]:  # Show last 2 errors
                print(f"      {error['message'][:80]}{'...' if len(error['message']) > 80 else ''}")
        
        print("🎉 Enhanced browser data capture demonstration completed!")
        
    except Exception as e:
        logger.error(f"Enhanced data capture demo error: {e}")
        print(f"❌ Enhanced data capture demo failed: {e}")


async def main():
    """
    CursorFlow v2.0.0 Complete Demonstration
    
    Showcases all breakthrough features introduced in v2.0.0.
    """
    print("🚀 CursorFlow v2.0.0 Comprehensive Demonstration")
    print("=" * 60)
    print("This demo showcases all breakthrough v2.0.0 features:")
    print("🔥 Hot Reload Intelligence")
    print("🧠 Advanced Element Intelligence") 
    print("📊 Comprehensive Page Analysis")
    print("🎯 Enhanced Error Context Collection")
    print("⚡ Enhanced Browser Data Capture")
    print("=" * 60)
    
    # Run all demonstrations
    demos = [
        ("Hot Reload Intelligence", demonstrate_v2_hot_reload_intelligence),
        ("Advanced Element Intelligence", demonstrate_v2_advanced_element_intelligence),
        ("Comprehensive Page Analysis", demonstrate_v2_comprehensive_page_analysis),
        ("Enhanced Error Context", demonstrate_v2_enhanced_error_context),
        ("Enhanced Browser Data Capture", demonstrate_v2_enhanced_browser_data_capture)
    ]
    
    completed_demos = []
    failed_demos = []
    
    for demo_name, demo_func in demos:
        try:
            await demo_func()
            completed_demos.append(demo_name)
        except Exception as e:
            logger.error(f"Demo '{demo_name}' failed: {e}")
            failed_demos.append(demo_name)
    
    # Summary
    print(f"\n🎉 DEMONSTRATION SUMMARY")
    print("=" * 30)
    print(f"✅ Completed demos: {len(completed_demos)}")
    for demo in completed_demos:
        print(f"   ✅ {demo}")
    
    if failed_demos:
        print(f"\n❌ Failed demos: {len(failed_demos)}")
        for demo in failed_demos:
            print(f"   ❌ {demo}")
    
    print(f"\n🌟 CursorFlow v2.0.0 Features Demonstrated!")
    print("Check .cursorflow/artifacts/ for all captured data.")
    print("\nNext steps:")
    print("1. Review captured screenshots and data")
    print("2. Try the HMR workflow with your development server")
    print("3. Explore the comprehensive element analysis")
    print("4. Use the enhanced error context for debugging")
    print("\n🚀 Ready to revolutionize your AI-driven development workflow!")


if __name__ == "__main__":
    # Run the comprehensive demonstration
    asyncio.run(main())
