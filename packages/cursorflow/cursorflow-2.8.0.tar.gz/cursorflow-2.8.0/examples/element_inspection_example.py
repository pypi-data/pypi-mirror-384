"""
Element Inspection Example

This example shows how to use the inspect command for comprehensive CSS debugging
and element analysis. Perfect for understanding layout issues and computed styles.
"""

import asyncio
import json
from cursorflow import CursorFlow

async def inspect_element_comprehensive():
    """Example: Comprehensive element inspection with full CSS analysis"""
    
    print("🔍 Comprehensive Element Inspection Example\n")
    
    # Initialize CursorFlow
    flow = CursorFlow(
        base_url="http://localhost:3000",
        log_config={'source': 'local', 'paths': []},
        browser_config={'headless': True}
    )
    
    # Execute inspection with screenshot
    print("📸 Inspecting #messages-panel with comprehensive data capture...")
    results = await flow.execute_and_collect([
        {"navigate": "/console"},
        {"wait_for_selector": "body"},
        {"screenshot": "inspection"}
    ])
    
    # Extract element data from comprehensive analysis
    comprehensive_data = results.get('comprehensive_data', {})
    dom_analysis = comprehensive_data.get('dom_analysis', {})
    elements = dom_analysis.get('elements', [])
    
    # Find the target element
    target_selector = "#messages-panel"
    matching_elements = [
        el for el in elements 
        if el.get('id') == 'messages-panel'
    ]
    
    if not matching_elements:
        print(f"⚠️  Element {target_selector} not found")
        return
    
    element = matching_elements[0]
    
    # Display comprehensive element information
    print(f"\n═══ Element: {target_selector} ═══\n")
    
    # Basic info
    print(f"Tag:       {element.get('tagName', 'unknown')}")
    print(f"ID:        #{element.get('id', 'N/A')}")
    print(f"Classes:   .{element.get('className', 'N/A')}")
    
    # Dimensions
    visual_context = element.get('visual_context', {})
    bbox = visual_context.get('bounding_box', {})
    if bbox:
        print(f"\n📐 Dimensions:")
        print(f"   Position:  x={bbox.get('x', 0):.0f}, y={bbox.get('y', 0):.0f}")
        print(f"   Size:      {bbox.get('width', 0):.0f}w × {bbox.get('height', 0):.0f}h")
    
    # Computed styles
    computed = element.get('computedStyles', {})
    if computed:
        print(f"\n🎨 Key CSS Properties:")
        print(f"   display:   {computed.get('display', 'N/A')}")
        print(f"   position:  {computed.get('position', 'N/A')}")
        print(f"   flex:      {computed.get('flex', 'N/A')}")
        print(f"   width:     {computed.get('width', 'N/A')}")
        print(f"   height:    {computed.get('height', 'N/A')}")
    
    # Accessibility
    accessibility = element.get('accessibility', {})
    if accessibility:
        print(f"\n♿ Accessibility:")
        print(f"   Role:         {accessibility.get('role', 'N/A')}")
        print(f"   Interactive:  {'✅' if accessibility.get('isInteractive') else '❌'}")
    
    # Visual context
    visibility = visual_context.get('visibility', {})
    if visibility:
        print(f"\n👁️  Visual Context:")
        print(f"   Visible:  {'✅' if visibility.get('is_visible') else '❌'}")
        print(f"   In viewport: {'✅' if visibility.get('is_in_viewport') else '❌'}")
    
    # Screenshot location
    screenshots = results.get('artifacts', {}).get('screenshots', [])
    if screenshots:
        print(f"\n📸 Screenshot saved: {screenshots[0]}")
    
    print("\n✅ Inspection complete!")

async def inspect_multiple_elements():
    """Example: Inspect multiple elements for comparison"""
    
    print("\n🔍 Multiple Element Inspection Example\n")
    
    flow = CursorFlow(
        base_url="http://localhost:3000",
        log_config={'source': 'local', 'paths': []},
        browser_config={'headless': True}
    )
    
    # Execute inspection
    results = await flow.execute_and_collect([
        {"navigate": "/dashboard"},
        {"wait_for_selector": "body"},
        {"screenshot": "dashboard"}
    ])
    
    # Extract element data
    comprehensive_data = results.get('comprehensive_data', {})
    elements = comprehensive_data.get('dom_analysis', {}).get('elements', [])
    
    # Compare multiple panels
    selectors = [".sidebar", ".main-content", ".right-panel"]
    
    print("📊 Comparing panel widths:\n")
    for selector in selectors:
        matching = [
            el for el in elements
            if selector[1:] in el.get('className', '').split()
        ]
        
        if matching:
            element = matching[0]
            bbox = element.get('visual_context', {}).get('bounding_box', {})
            computed = element.get('computedStyles', {})
            
            print(f"{selector}:")
            print(f"  Rendered: {bbox.get('width', 0):.0f}px")
            print(f"  CSS:      {computed.get('width', 'N/A')}")
            print(f"  Flex:     {computed.get('flex', 'N/A')}\n")

async def inspect_with_verbose_css():
    """Example: Get ALL computed CSS properties for deep debugging"""
    
    print("\n🔍 Verbose CSS Inspection Example\n")
    
    flow = CursorFlow(
        base_url="http://localhost:3000",
        log_config={'source': 'local', 'paths': []},
        browser_config={'headless': True}
    )
    
    results = await flow.execute_and_collect([
        {"navigate": "/component"},
        {"wait_for_selector": "body"},
        {"screenshot": "component"}
    ])
    
    # Extract element
    elements = results.get('comprehensive_data', {}).get('dom_analysis', {}).get('elements', [])
    
    if elements:
        element = elements[0]  # First element
        computed = element.get('computedStyles', {})
        
        print(f"🎨 All {len(computed)} Computed CSS Properties:\n")
        
        for prop, value in sorted(computed.items())[:20]:  # Show first 20
            print(f"   {prop}: {value}")
        
        print(f"\n   ... and {len(computed) - 20} more properties")

if __name__ == '__main__':
    print("=" * 60)
    print("CursorFlow Element Inspection Examples")
    print("=" * 60)
    
    # Run examples
    asyncio.run(inspect_element_comprehensive())
    asyncio.run(inspect_multiple_elements())
    asyncio.run(inspect_with_verbose_css())
    
    print("\n" + "=" * 60)
    print("✅ All examples completed!")
    print("=" * 60)

