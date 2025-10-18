"""
Element Measurement Example

This example shows how to use the measure command for surgical dimension checking
and quick CSS verification. Perfect for validating layout changes.
"""

import asyncio
import json
from cursorflow import CursorFlow

async def measure_single_element():
    """Example: Quick dimension check for a single element"""
    
    print("📏 Single Element Measurement Example\n")
    
    flow = CursorFlow(
        base_url="http://localhost:3000",
        log_config={'source': 'local', 'paths': []},
        browser_config={'headless': True}
    )
    
    # Execute measurement
    print("📐 Measuring #main-panel dimensions...")
    results = await flow.execute_and_collect([
        {"navigate": "/dashboard"},
        {"wait_for_selector": "body"},
        {"screenshot": "measurement"}
    ])
    
    # Extract element data
    elements = results.get('comprehensive_data', {}).get('dom_analysis', {}).get('elements', [])
    
    # Find target element
    matching = [el for el in elements if el.get('id') == 'main-panel']
    
    if not matching:
        print("⚠️  Element #main-panel not found")
        return
    
    element = matching[0]
    bbox = element.get('visual_context', {}).get('bounding_box', {})
    computed = element.get('computedStyles', {})
    
    # Display measurements (surgical precision)
    print(f"\n#main-panel")
    print(f"  📐 Rendered:  {bbox.get('width', 0):.0f}w × {bbox.get('height', 0):.0f}h")
    print(f"  📍 Position:  x={bbox.get('x', 0):.0f}, y={bbox.get('y', 0):.0f}")
    print(f"  🎨 Display:   {computed.get('display', 'N/A')}")
    print(f"  📦 CSS Width: {computed.get('width', 'N/A')}")
    
    if computed.get('flex'):
        print(f"  🔧 Flex:      {computed.get('flex')}")
    
    print("\n✅ Measurement complete!")

async def measure_multiple_elements():
    """Example: Measure multiple elements at once"""
    
    print("\n📏 Multiple Element Measurement Example\n")
    
    flow = CursorFlow(
        base_url="http://localhost:3000",
        log_config={'source': 'local', 'paths': []},
        browser_config={'headless': True}
    )
    
    results = await flow.execute_and_collect([
        {"navigate": "/layout"},
        {"wait_for_selector": "body"},
        {"screenshot": "layout"}
    ])
    
    # Extract elements
    elements = results.get('comprehensive_data', {}).get('dom_analysis', {}).get('elements', [])
    
    # Measure multiple panels
    selectors = ["#panel1", "#panel2", "#panel3"]
    
    print("📊 Measuring layout panels:\n")
    
    for selector in selectors:
        matching = [el for el in elements if el.get('id') == selector[1:]]
        
        if matching:
            element = matching[0]
            bbox = element.get('visual_context', {}).get('bounding_box', {})
            computed = element.get('computedStyles', {})
            
            print(f"{selector}")
            print(f"  📐 Rendered:  {bbox.get('width', 0):.0f}w × {bbox.get('height', 0):.0f}h")
            print(f"  📦 CSS Width: {computed.get('width', 'N/A')}")
            
            if computed.get('flex'):
                print(f"  🔧 Flex:      {computed.get('flex')}")
            if computed.get('flexBasis') != 'auto':
                print(f"  📏 Flex Base: {computed.get('flexBasis')}")
            
            print()

async def measure_before_and_after():
    """Example: Measure before CSS changes, apply changes, measure after"""
    
    print("\n📏 Before/After Measurement Example\n")
    
    flow = CursorFlow(
        base_url="http://localhost:3000",
        log_config={'source': 'local', 'paths': []},
        browser_config={'headless': True}
    )
    
    # BEFORE measurement
    print("📐 BEFORE CSS changes:")
    before_results = await flow.execute_and_collect([
        {"navigate": "/component"},
        {"wait_for_selector": "body"},
        {"screenshot": "before"}
    ])
    
    before_elements = before_results.get('comprehensive_data', {}).get('dom_analysis', {}).get('elements', [])
    before_element = [el for el in before_elements if el.get('id') == 'container'][0]
    before_bbox = before_element.get('visual_context', {}).get('bounding_box', {})
    
    print(f"  Container: {before_bbox.get('width', 0):.0f}w × {before_bbox.get('height', 0):.0f}h")
    
    # --- User would make CSS changes here in actual workflow ---
    print("\n🔧 (Apply CSS changes: .container { padding: 2rem; gap: 1.5rem; })")
    print("   (In real workflow, you'd modify CSS files here)")
    
    # AFTER measurement (simulated with new test)
    print("\n📐 AFTER CSS changes:")
    after_results = await flow.execute_and_collect([
        {"navigate": "/component"},
        {"wait_for_selector": "body"},
        {"screenshot": "after"}
    ])
    
    after_elements = after_results.get('comprehensive_data', {}).get('dom_analysis', {}).get('elements', [])
    after_element = [el for el in after_elements if el.get('id') == 'container'][0]
    after_bbox = after_element.get('visual_context', {}).get('bounding_box', {})
    
    print(f"  Container: {after_bbox.get('width', 0):.0f}w × {after_bbox.get('height', 0):.0f}h")
    
    # Compare
    width_diff = after_bbox.get('width', 0) - before_bbox.get('width', 0)
    height_diff = after_bbox.get('height', 0) - before_bbox.get('height', 0)
    
    print(f"\n📊 Changes:")
    print(f"  Width:  {'+' if width_diff > 0 else ''}{width_diff:.0f}px")
    print(f"  Height: {'+' if height_diff > 0 else ''}{height_diff:.0f}px")
    print("\n✅ CSS changes verified!")

async def measure_responsive_breakpoints():
    """Example: Measure element dimensions across responsive breakpoints"""
    
    print("\n📏 Responsive Breakpoint Measurement Example\n")
    
    viewports = [
        {"width": 375, "height": 667, "name": "mobile"},
        {"width": 768, "height": 1024, "name": "tablet"},
        {"width": 1440, "height": 900, "name": "desktop"}
    ]
    
    flow = CursorFlow(
        base_url="http://localhost:3000",
        log_config={'source': 'local', 'paths': []},
        browser_config={'headless': True}
    )
    
    print("📱 Measuring across breakpoints:\n")
    
    for viewport in viewports:
        # Set viewport size
        flow.browser_config['viewport'] = {"width": viewport['width'], "height": viewport['height']}
        
        results = await flow.execute_and_collect([
            {"navigate": "/responsive"},
            {"wait_for_selector": "body"},
            {"screenshot": f"responsive-{viewport['name']}"}
        ])
        
        elements = results.get('comprehensive_data', {}).get('dom_analysis', {}).get('elements', [])
        matching = [el for el in elements if el.get('id') == 'main-content']
        
        if matching:
            element = matching[0]
            bbox = element.get('visual_context', {}).get('bounding_box', {})
            computed = element.get('computedStyles', {})
            
            print(f"{viewport['name'].upper()} ({viewport['width']}x{viewport['height']}):")
            print(f"  #main-content: {bbox.get('width', 0):.0f}w × {bbox.get('height', 0):.0f}h")
            print(f"  Display: {computed.get('display', 'N/A')}")
            print()

async def measure_with_verbose_css():
    """Example: Get all computed CSS for detailed analysis"""
    
    print("\n📏 Verbose Measurement (All CSS Properties)\n")
    
    flow = CursorFlow(
        base_url="http://localhost:3000",
        log_config={'source': 'local', 'paths': []},
        browser_config={'headless': True}
    )
    
    results = await flow.execute_and_collect([
        {"navigate": "/element"},
        {"wait_for_selector": "body"},
        {"screenshot": "element"}
    ])
    
    elements = results.get('comprehensive_data', {}).get('dom_analysis', {}).get('elements', [])
    
    if elements:
        element = elements[0]
        bbox = element.get('visual_context', {}).get('bounding_box', {})
        computed = element.get('computedStyles', {})
        
        print(f"Element: {element.get('tagName', 'unknown')}")
        print(f"  📐 Rendered:  {bbox.get('width', 0):.0f}w × {bbox.get('height', 0):.0f}h\n")
        print(f"  🎨 All {len(computed)} Computed CSS Properties:")
        
        for prop, value in sorted(computed.items())[:15]:
            print(f"     {prop}: {value}")
        
        print(f"\n     💡 {len(computed) - 15} more properties available")

if __name__ == '__main__':
    print("=" * 60)
    print("CursorFlow Element Measurement Examples")
    print("=" * 60)
    
    # Run examples
    asyncio.run(measure_single_element())
    asyncio.run(measure_multiple_elements())
    asyncio.run(measure_before_and_after())
    asyncio.run(measure_responsive_breakpoints())
    asyncio.run(measure_with_verbose_css())
    
    print("\n" + "=" * 60)
    print("✅ All examples completed!")
    print("=" * 60)

