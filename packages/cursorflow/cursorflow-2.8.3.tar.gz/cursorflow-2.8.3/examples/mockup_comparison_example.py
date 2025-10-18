"""
Mockup Comparison Example

Demonstrates pure observation approach to visual design matching.
CursorFlow provides measurements - Cursor makes decisions based on data.

Philosophy: We observe multiple realities (mockup, implementation, CSS variations)
and provide quantified similarity metrics. No interpretation, just data.
"""

import asyncio
import json
from pathlib import Path
import sys

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from cursorflow.core.cursorflow import CursorFlow


async def basic_mockup_comparison():
    """
    Basic example: Compare mockup to implementation with pure data collection
    """
    print("=" * 60)
    print("🎨 Basic Mockup Comparison - Pure Observation")
    print("=" * 60)
    
    # Initialize CursorFlow
    flow = CursorFlow(
        base_url="http://localhost:3000",  # Your work-in-progress
        log_config={'source': 'local', 'paths': []},
        browser_config={'headless': True}
    )
    
    # Compare mockup to implementation (observing both realities)
    print("\n📸 Capturing both mockup and implementation...")
    results = await flow.compare_mockup_to_implementation(
        mockup_url="https://example.com",  # Simulating mockup
        implementation_actions=[
            {"navigate": "/"},
            {"wait_for": "body"}
        ],
        comparison_config={
            "viewports": [
                {"width": 1440, "height": 900, "name": "desktop"}
            ],
            "diff_threshold": 0.1
        }
    )
    
    if "error" in results:
        print(f"❌ Comparison failed: {results['error']}")
        return
    
    # Display pure metrics (no interpretation)
    summary = results.get('summary', {})
    print(f"\n✅ Comparison completed: {results.get('comparison_id')}")
    print(f"\n📊 Measurement Data:")
    print(f"   Average similarity: {summary.get('average_similarity', 0)}%")
    print(f"   Viewports tested: {summary.get('viewports_tested', 0)}")
    
    # Show per-viewport data
    similarity_by_viewport = summary.get('similarity_by_viewport', [])
    for viewport_data in similarity_by_viewport:
        print(f"   {viewport_data['viewport']}: {viewport_data['similarity']}%")
    
    # Show what artifacts were created
    print(f"\n📁 Artifacts created:")
    for result in results.get('results', []):
        print(f"   Mockup screenshot: {Path(result['mockup_screenshot']).name}")
        print(f"   Implementation screenshot: {Path(result['implementation_screenshot']).name}")
        print(f"   Diff image: {Path(result['visual_diff']['diff_image']).name}")
        print(f"   Highlighted diff: {Path(result['visual_diff']['highlighted_diff']).name}")
    
    print(f"\n💡 Cursor can now analyze this data to decide on CSS changes")
    print(f"   Data saved to: .cursorflow/artifacts/mockup_comparisons/")


async def css_iteration_with_measurements():
    """
    Example: Test multiple CSS variations and observe real outcomes
    """
    print("\n" + "=" * 60)
    print("🔄 CSS Iteration - Observing Multiple Realities")
    print("=" * 60)
    
    flow = CursorFlow(
        base_url="http://localhost:3000",
        log_config={'source': 'local', 'paths': []},
        browser_config={'headless': True}
    )
    
    # Define CSS variations to test
    css_improvements = [
        {
            "name": "generous-spacing",
            "css": ".container { padding: 2rem; gap: 2rem; }"
        },
        {
            "name": "moderate-spacing",
            "css": ".container { padding: 1.5rem; gap: 1.5rem; }"
        },
        {
            "name": "tight-spacing",
            "css": ".container { padding: 1rem; gap: 1rem; }"
        }
    ]
    
    print(f"\n🧪 Testing {len(css_improvements)} CSS variations...")
    print("   (Temporarily injecting CSS to observe real rendering)")
    
    # Run iterative comparison
    results = await flow.iterative_mockup_matching(
        mockup_url="https://example.com",
        css_improvements=css_improvements,
        base_actions=[{"navigate": "/"}, {"wait_for": "body"}]
    )
    
    if "error" in results:
        print(f"❌ Iteration failed: {results['error']}")
        return
    
    # Display measurements for each variation
    print(f"\n📊 Similarity Measurements:")
    
    baseline_sim = results.get('baseline', {}).get('visual_diff', {}).get('similarity_score', 0)
    print(f"   Baseline (no changes): {baseline_sim}%")
    
    for iteration in results.get('iterations', []):
        name = iteration.get('css_change', {}).get('name', 'unknown')
        similarity = iteration.get('visual_diff', {}).get('similarity_score', 0)
        diff = similarity - baseline_sim
        print(f"   {name}: {similarity}% ({diff:+.1f}%)")
    
    print(f"\n💡 Pure data provided - Cursor analyzes and decides which CSS to apply")
    print(f"   Each variation measured against REAL rendering")


async def understanding_the_data():
    """
    Example: What data is available in comparison results
    """
    print("\n" + "=" * 60)
    print("📋 Understanding Comparison Data Structure")
    print("=" * 60)
    
    print("""
CursorFlow provides these measurements:

1. Visual Metrics:
   - similarity_percentage: 0-100 (quantified match)
   - different_pixels: Count of differing pixels
   - total_pixels: Total canvas size
   - major_difference_regions: [{x, y, width, height, area}]

2. Screenshots:
   - mockup_screenshot: Path to mockup capture
   - implementation_screenshot: Path to implementation
   - diff_image: Pixel-by-pixel difference
   - highlighted_diff: Visual diff with red overlay

3. Layout Data:
   - mockup_elements: Count of elements in mockup
   - implementation_elements: Count in implementation
   - differences: Position/size/style variances

4. Per-Viewport Data:
   - Separate measurements for each breakpoint
   - Responsive behavior captured

Cursor uses this data to:
- Decide if implementation is close enough
- Choose which CSS changes to make
- Prioritize layout vs styling fixes
- Determine when design match is acceptable
    """)


if __name__ == '__main__':
    print("=" * 60)
    print("CursorFlow Mockup Comparison Examples")
    print("Pure Observation - Cursor Makes Decisions")
    print("=" * 60)
    
    # Run examples
    asyncio.run(basic_mockup_comparison())
    asyncio.run(css_iteration_with_measurements())
    asyncio.run(understanding_the_data())
    
    print("\n" + "=" * 60)
    print("✅ All examples completed!")
    print("💡 CursorFlow observes reality - Cursor analyzes and decides")
    print("=" * 60)