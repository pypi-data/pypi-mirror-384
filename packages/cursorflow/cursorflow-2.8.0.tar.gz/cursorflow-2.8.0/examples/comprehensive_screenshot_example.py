"""
CursorFlow v2.0.0 Comprehensive Screenshot Analysis Example

Demonstrates the enhanced comprehensive data capture in v2.0.0.
Every screenshot now includes:
- 🆕 Advanced Element Intelligence with 7 selector strategies
- 🆕 Font Loading Analysis
- 🆕 Animation State Tracking  
- 🆕 Resource Loading Intelligence
- 🆕 Storage State Analysis
- 🆕 HMR Event Correlation (when available)
- Enhanced DOM structure, CSS properties, network activity, console logs, and performance metrics

Perfect for understanding the complete v2.0.0 data collection capabilities.
"""

import asyncio
import json
from pathlib import Path
import sys

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from cursorflow.core.cursorflow import CursorFlow


async def demonstrate_comprehensive_screenshot():
    """
    Show how every screenshot now captures comprehensive page data
    """
    print("🔬 CursorFlow v2.0.0 Comprehensive Screenshot Analysis Demo")
    print("=" * 70)
    
    # Initialize CursorFlow
    flow = CursorFlow(
        base_url="http://localhost:3000",
        log_config={'source': 'local', 'paths': ['logs/app.log']},
        browser_config={'headless': True}
    )
    
    # Execute a simple test with screenshots
    results = await flow.execute_and_collect([
        {"navigate": "/dashboard"},
        {"wait_for": "#main-content"},
        {"screenshot": "dashboard_loaded"},  # This now captures EVERYTHING
        {"click": "#refresh-button"},
        {"wait": 2},
        {"screenshot": "after_refresh"}      # This too captures EVERYTHING
    ])
    
    print("✅ Test completed with comprehensive data capture")
    print(f"📊 Timeline events: {len(results.get('timeline', []))}")
    
    # Show what comprehensive data we captured
    artifacts = results.get('artifacts', {})
    screenshots = artifacts.get('screenshots', [])
    
    for i, screenshot in enumerate(screenshots):
        if isinstance(screenshot, dict):  # New comprehensive format
            print(f"\n📸 Screenshot {i+1}: {screenshot['name']}")
            print(f"   Visual: {screenshot['screenshot_path']}")
            print(f"   Data: {screenshot.get('comprehensive_data_path', 'N/A')}")
            
            # Show summary of captured data
            if 'analysis_summary' in screenshot:
                summary = screenshot['analysis_summary']
                print(f"   📊 Analysis Summary:")
                print(f"      DOM Elements: {summary.get('page_health', {}).get('dom_elements_count', 0)}")
                print(f"      Console Errors: {summary.get('page_health', {}).get('error_count', 0)}")
                print(f"      Network Requests: {summary.get('technical_metrics', {}).get('total_network_requests', 0)}")
                print(f"      Performance Score: {summary.get('quality_indicators', {}).get('performance_score', 0)}/100")
                print(f"      Overall Health: {summary.get('quality_indicators', {}).get('overall_health', 'unknown')}")
            
            # Show DOM structure insights
            if 'dom_analysis' in screenshot:
                dom = screenshot['dom_analysis']
                page_structure = dom.get('pageStructure', {})
                print(f"   🏗️  Page Structure:")
                print(f"      Has Header: {page_structure.get('hasHeader', False)}")
                print(f"      Has Navigation: {page_structure.get('hasNavigation', False)}")
                print(f"      Has Main Content: {page_structure.get('hasMainContent', False)}")
                print(f"      Interactive Elements: {page_structure.get('interactiveElements', 0)}")
            
            # Show network activity
            if 'network_data' in screenshot:
                network = screenshot['network_data']
                network_summary = network.get('network_summary', {})
                print(f"   🌐 Network Activity:")
                print(f"      Total Requests: {network_summary.get('total_requests', 0)}")
                print(f"      Failed Requests: {network_summary.get('failed_requests', 0)}")
                print(f"      Avg Response Time: {network_summary.get('average_response_time', 0):.1f}ms")
                print(f"      Data Transferred: {network_summary.get('total_data_transferred', 0)} bytes")
            
            # Show console activity
            if 'console_data' in screenshot:
                console = screenshot['console_data']
                console_summary = console.get('console_summary', {})
                print(f"   💬 Console Activity:")
                print(f"      Total Logs: {console_summary.get('total_logs', 0)}")
                print(f"      Errors: {console_summary.get('error_count', 0)}")
                print(f"      Warnings: {console_summary.get('warning_count', 0)}")
                print(f"      Recent Errors: {console_summary.get('has_recent_errors', False)}")
    
    # Save detailed analysis for inspection
    from pathlib import Path
    artifacts_dir = Path('.cursorflow/artifacts')
    artifacts_dir.mkdir(parents=True, exist_ok=True)
    
    analysis_file = artifacts_dir / 'comprehensive_screenshot_analysis.json'
    with open(analysis_file, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"\n💾 Complete analysis saved to: {analysis_file}")
    print(f"📁 All artifacts available in: .cursorflow/artifacts/")
    
    return results


async def analyze_specific_elements():
    """
    Show how to analyze specific elements from the comprehensive data
    """
    print("\n🎯 Element-Specific Analysis Demo")
    print("=" * 50)
    
    flow = CursorFlow(
        base_url="http://localhost:3000",
        log_config={'source': 'local', 'paths': ['logs/app.log']},
        browser_config={'headless': True}
    )
    
    # Take a comprehensive screenshot
    results = await flow.execute_and_collect([
        {"navigate": "/dashboard"},
        {"wait_for": "#main-content"},
        {"screenshot": "element_analysis"}
    ])
    
    # Extract the screenshot data
    screenshot_data = results.get('artifacts', {}).get('screenshots', [{}])[0]
    
    if isinstance(screenshot_data, dict) and 'dom_analysis' in screenshot_data:
        elements = screenshot_data['dom_analysis'].get('elements', [])
        
        print(f"📊 Found {len(elements)} elements with complete CSS data")
        
        # Analyze specific element types
        buttons = [el for el in elements if el.get('tagName') == 'button' or 'btn' in el.get('className', '')]
        headers = [el for el in elements if el.get('tagName') in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']]
        interactive = [el for el in elements if el.get('isInteractive', False)]
        
        print(f"\n🔘 Buttons found: {len(buttons)}")
        for button in buttons[:3]:  # Show first 3
            styles = button.get('computedStyles', {})
            print(f"   Button: {button.get('textContent', 'No text')[:30]}")
            print(f"      Background: {styles.get('backgroundColor', 'N/A')}")
            print(f"      Color: {styles.get('color', 'N/A')}")
            print(f"      Font Size: {styles.get('fontSize', 'N/A')}")
            print(f"      Border Radius: {styles.get('borderRadius', 'N/A')}")
            print(f"      Position: {button.get('boundingBox', {}).get('x', 0)}, {button.get('boundingBox', {}).get('y', 0)}")
        
        print(f"\n📝 Headers found: {len(headers)}")
        for header in headers[:3]:  # Show first 3
            styles = header.get('computedStyles', {})
            print(f"   {header.get('tagName', 'header').upper()}: {header.get('textContent', 'No text')[:50]}")
            print(f"      Font Size: {styles.get('fontSize', 'N/A')}")
            print(f"      Font Weight: {styles.get('fontWeight', 'N/A')}")
            print(f"      Color: {styles.get('color', 'N/A')}")
            print(f"      Margin: {styles.get('margin', 'N/A')}")
        
        print(f"\n🖱️  Interactive elements: {len(interactive)}")
        for element in interactive[:5]:  # Show first 5
            print(f"   {element.get('tagName', 'unknown')}: {element.get('textContent', 'No text')[:30]}")
            print(f"      Selector: {element.get('uniqueSelector', 'N/A')}")
            print(f"      Position: {element.get('boundingBox', {}).get('x', 0)}, {element.get('boundingBox', {}).get('y', 0)}")
    
    return results


async def demonstrate_error_correlation():
    """
    Show how comprehensive data enables intelligent error correlation
    """
    print("\n🔍 Error Correlation Demo")
    print("=" * 40)
    
    flow = CursorFlow(
        base_url="http://localhost:3000",
        log_config={'source': 'local', 'paths': ['logs/app.log']},
        browser_config={'headless': True}
    )
    
    # Simulate a test that might cause errors
    results = await flow.execute_and_collect([
        {"navigate": "/dashboard"},
        {"click": "#broken-button"},  # This might cause errors
        {"wait": 1},
        {"screenshot": "error_state"}
    ])
    
    # Analyze the comprehensive data for errors
    screenshot_data = results.get('artifacts', {}).get('screenshots', [{}])[-1]  # Last screenshot
    
    if isinstance(screenshot_data, dict):
        # Check console errors
        console_data = screenshot_data.get('console_data', {})
        if console_data.get('console_summary', {}).get('error_count', 0) > 0:
            print("❌ Console errors detected:")
            for error in console_data.get('errors', {}).get('logs', [])[:3]:
                print(f"   Error: {error.get('text', 'Unknown error')[:100]}")
                print(f"   Location: {error.get('location', {}).get('url', 'Unknown')}")
                print(f"   Time: {error.get('timestamp', 0)}")
        
        # Check network failures
        network_data = screenshot_data.get('network_data', {})
        failed_requests = network_data.get('failed_requests', {}).get('requests', [])
        if failed_requests:
            print("🌐 Network failures detected:")
            for request in failed_requests[:3]:
                print(f"   Failed: {request.get('url', 'Unknown URL')}")
                print(f"   Status: {request.get('status', 'Unknown')}")
                print(f"   Time: {request.get('timestamp', 0)}")
        
        # Check performance impact
        performance_data = screenshot_data.get('performance_data', {})
        perf_score = performance_data.get('performance_summary', {}).get('performance_score', 100)
        if perf_score < 70:
            print(f"⚡ Performance issues detected (Score: {perf_score}/100)")
            memory_mb = performance_data.get('performance_summary', {}).get('memory_usage_mb')
            if memory_mb:
                print(f"   Memory usage: {memory_mb:.1f} MB")
        
        # Overall health assessment
        analysis_summary = screenshot_data.get('analysis_summary', {})
        overall_health = analysis_summary.get('quality_indicators', {}).get('overall_health', 'unknown')
        print(f"\n🏥 Overall page health: {overall_health}")
    
    return results


async def main():
    """
    Run all comprehensive screenshot examples
    """
    print("🚀 CursorFlow Comprehensive Screenshot Analysis")
    print("=" * 70)
    print("Every screenshot now captures complete page intelligence:")
    print("• DOM structure with all CSS properties")
    print("• Complete network request/response data")
    print("• All console logs and error patterns")
    print("• Performance metrics and timing data")
    print("• Page state and interaction readiness")
    print()
    
    try:
        # Run comprehensive screenshot demo
        await demonstrate_comprehensive_screenshot()
        
        # Run element analysis demo
        await analyze_specific_elements()
        
        # Run error correlation demo
        await demonstrate_error_correlation()
        
        print("\n🎉 All comprehensive analysis examples completed!")
        print("\nKey Benefits:")
        print("✅ Every screenshot includes complete page intelligence")
        print("✅ No need for separate DOM/network/console queries")
        print("✅ Perfect for AI analysis and decision making")
        print("✅ Enables intelligent error correlation")
        print("✅ Provides actionable insights for debugging")
        print("\nNext steps:")
        print("1. Review the generated JSON files for complete data structure")
        print("2. Use the comprehensive data for intelligent analysis")
        print("3. Build AI agents that can make decisions based on complete page state")
        
    except Exception as e:
        print(f"\n❌ Example failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    print("⚠️  Make sure your development server is running on http://localhost:3000")
    print("   This example will capture comprehensive data from your application\n")
    
    asyncio.run(main())
