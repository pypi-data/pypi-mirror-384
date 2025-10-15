"""
CursorFlow Parallel Viewport Testing Example

Demonstrates responsive testing across multiple viewports in parallel.
Tests the same actions on mobile, tablet, and desktop viewports simultaneously.

Perfect for responsive design validation and cross-viewport behavior analysis.
"""

import asyncio
import json
from pathlib import Path
from cursorflow import CursorFlow


async def demonstrate_responsive_testing():
    """
    Show how parallel viewport testing provides comprehensive responsive analysis
    """
    print("📱 CursorFlow Parallel Viewport Testing Demo")
    print("=" * 60)
    
    # Initialize CursorFlow
    flow = CursorFlow(
        base_url="http://localhost:3000",
        log_config={"source": "local", "paths": ["logs/app.log"]},
        browser_config={"headless": True}
    )
    
    try:
        # Define standard responsive viewports
        viewports = [
            {"width": 375, "height": 667, "name": "mobile"},
            {"width": 768, "height": 1024, "name": "tablet"}, 
            {"width": 1440, "height": 900, "name": "desktop"}
        ]
        
        # Define test actions (same actions across all viewports)
        test_actions = [
            {"navigate": "/dashboard"},
            {"wait_for": "#main-content"},
            {"screenshot": "dashboard-loaded"},
            {"click": "#menu-button"},
            {"screenshot": {"name": "menu-opened", "options": {"clip": {"selector": "#navigation"}}}},
            {"fill": {"selector": "#search", "value": "test query"}},
            {"screenshot": "search-filled"}
        ]
        
        print(f"🚀 Testing {len(test_actions)} actions across {len(viewports)} viewports...")
        print("   📱 Mobile: 375x667")
        print("   📟 Tablet: 768x1024") 
        print("   💻 Desktop: 1440x900")
        
        # Execute responsive testing
        results = await flow.test_responsive(viewports, test_actions)
        
        # Display results
        print(f"\n✅ Responsive test completed!")
        
        execution_summary = results.get('execution_summary', {})
        print(f"📊 Viewports tested: {execution_summary.get('successful_viewports', 0)}/{execution_summary.get('total_viewports', 0)}")
        print(f"⏱️  Total execution time: {execution_summary.get('execution_time', 0):.2f}s")
        print(f"📸 Screenshots captured: {len(results.get('artifacts', {}).get('screenshots', []))}")
        
        # Show viewport-specific results
        print(f"\n📊 Viewport Analysis:")
        responsive_analysis = results.get('responsive_analysis', {})
        viewport_comparison = responsive_analysis.get('viewport_comparison', {})
        
        for viewport_name, data in viewport_comparison.items():
            print(f"   {viewport_name}: {data['dimensions']} - {data['execution_time']:.2f}s - {data['screenshot_count']} screenshots")
        
        # Performance analysis
        if 'performance_analysis' in responsive_analysis:
            perf = responsive_analysis['performance_analysis']
            print(f"\n🏃 Performance Analysis:")
            print(f"   Fastest: {perf.get('fastest_viewport')} viewport")
            print(f"   Slowest: {perf.get('slowest_viewport')} viewport") 
            print(f"   Time difference: {perf.get('time_difference', 0):.2f}s")
            print(f"   Performance variance: {perf.get('performance_variance', 'unknown')}")
        
        # Show responsive insights
        insights = responsive_analysis.get('responsive_insights', [])
        if insights:
            print(f"\n💡 Responsive Insights:")
            for insight in insights:
                print(f"   • {insight}")
        
        # Save results
        artifacts_dir = Path('.cursorflow/artifacts')
        artifacts_dir.mkdir(parents=True, exist_ok=True)
        
        results_file = artifacts_dir / 'responsive_testing_demo.json'
        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        print(f"\n📁 Results saved to: {results_file}")
        print(f"📸 Screenshots saved to: .cursorflow/artifacts/screenshots/")
        
        print(f"\n🌟 Philosophy: Pure observation across multiple viewports!")
        print(f"   • Same reality, multiple perspectives")
        print(f"   • No mocking or simulation")
        print(f"   • Actual responsive behavior captured")
        
        return results
        
    except Exception as e:
        print(f"❌ Demo failed: {e}")
        return {"error": str(e)}


async def demonstrate_cli_responsive():
    """
    Show CLI usage for responsive testing
    """
    print("\n" + "=" * 60)
    print("🖥️  CLI Responsive Testing Examples")
    print("=" * 60)
    
    print("\n📋 CLI Examples:")
    print("# Simple responsive test")
    print("cursorflow test --base-url http://localhost:3000 --path '/dashboard' --responsive")
    
    print("\n# Responsive test with custom actions")
    print("cursorflow test --base-url http://localhost:3000 --responsive --actions '[")
    print('  {"navigate": "/products"},')
    print('  {"fill": {"selector": "#search", "value": "laptop"}},')
    print('  {"click": "#search-btn"},')
    print('  {"screenshot": "search-results"}')
    print("]'")
    
    print("\n# All actions supported:")
    print("✅ navigate, click, fill, wait_for, wait, screenshot")
    print("✅ Enhanced screenshot options (clip, mask, quality)")
    print("✅ All Playwright actions from execute_and_collect()")
    
    print("\n🎯 Use Cases:")
    print("• Responsive design validation")
    print("• Cross-viewport behavior testing")
    print("• Mobile-first development verification")
    print("• Breakpoint testing")
    print("• Component library responsive testing")


if __name__ == "__main__":
    print("🚀 Starting CursorFlow Responsive Testing Demo...")
    
    # Run the demonstrations
    asyncio.run(demonstrate_responsive_testing())
    asyncio.run(demonstrate_cli_responsive())
    
    print("\n🎉 Responsive Testing Demo Complete!")
    print("\n💡 Key Benefits:")
    print("   • Test multiple viewports in parallel")
    print("   • Comprehensive responsive analysis")
    print("   • Performance comparison across viewports")
    print("   • All standard actions supported")
    print("   • Pure observation - no simulation")
    print("\n🌌 Remember: Same reality, multiple viewport perspectives!")
