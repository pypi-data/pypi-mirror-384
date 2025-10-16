"""
CursorFlow Enhanced Screenshot Options Example

Demonstrates the new screenshot options for precise visual data collection:
- Clip to specific elements or coordinates
- Mask sensitive information
- Full page vs viewport capture
- Quality control

Perfect for component-focused testing and privacy-aware screenshots.
"""

import asyncio
import json
from pathlib import Path
from cursorflow import CursorFlow


async def demonstrate_enhanced_screenshots():
    """
    Show how enhanced screenshot options provide more precise observation
    """
    print("🔍 CursorFlow Enhanced Screenshot Options Demo")
    print("=" * 60)
    
    # Initialize CursorFlow
    flow = CursorFlow(
        base_url="http://localhost:3000",
        log_config={"source": "local", "paths": ["logs/app.log"]}
    )
    
    try:
        # Example 1: Basic screenshot (current behavior)
        print("\n1. 📸 Basic Screenshot")
        basic_results = await flow.execute_and_collect([
            {"navigate": "/dashboard"},
            {"screenshot": "basic-dashboard"}
        ])
        
        # Example 2: Component-focused screenshot (clip to element)
        print("\n2. 🎯 Component-Focused Screenshot")
        component_results = await flow.execute_and_collect([
            {"navigate": "/dashboard"},
            {"screenshot": {
                "name": "dashboard-header",
                "options": {
                    "clip": {"selector": "#header"},
                    "quality": 90
                }
            }}
        ])
        
        # Example 3: Privacy-aware screenshot (mask sensitive data)
        print("\n3. 🛡️ Privacy-Aware Screenshot")
        privacy_results = await flow.execute_and_collect([
            {"navigate": "/user-profile"},
            {"screenshot": {
                "name": "profile-masked",
                "options": {
                    "mask": [".user-email", ".user-phone", ".sensitive-data"],
                    "full_page": True
                }
            }}
        ])
        
        # Example 4: Coordinate-based clipping
        print("\n4. 📐 Coordinate-Based Clipping")
        coordinate_results = await flow.execute_and_collect([
            {"navigate": "/dashboard"},
            {"screenshot": {
                "name": "dashboard-section",
                "options": {
                    "clip": {
                        "x": 100,
                        "y": 200,
                        "width": 800,
                        "height": 400
                    }
                }
            }}
        ])
        
        # Example 5: Full page with masking
        print("\n5. 📄 Full Page with Masking")
        fullpage_results = await flow.execute_and_collect([
            {"navigate": "/admin"},
            {"screenshot": {
                "name": "admin-fullpage-safe",
                "options": {
                    "full_page": True,
                    "mask": [".api-key", ".password-field", ".secret-token"],
                    "quality": 95
                }
            }}
        ])
        
        # Combine all results
        all_results = {
            "basic_screenshot": basic_results,
            "component_focused": component_results,
            "privacy_aware": privacy_results,
            "coordinate_clipping": coordinate_results,
            "fullpage_masked": fullpage_results,
            "demo_summary": {
                "total_screenshots": 5,
                "features_demonstrated": [
                    "Element-based clipping",
                    "Coordinate-based clipping", 
                    "Privacy masking",
                    "Full page capture",
                    "Quality control"
                ],
                "philosophy": "Pure observation with precise control - no modification of observed content"
            }
        }
        
        # Save results
        artifacts_dir = Path('.cursorflow/artifacts')
        artifacts_dir.mkdir(parents=True, exist_ok=True)
        
        results_file = artifacts_dir / 'enhanced_screenshot_demo.json'
        with open(results_file, 'w') as f:
            json.dump(all_results, f, indent=2, default=str)
        
        print(f"\n✅ Demo completed! Results saved to: {results_file}")
        print("\n📊 Screenshot Options Summary:")
        print("   🎯 Clip to elements: Focus on specific components")
        print("   📐 Clip to coordinates: Precise region control")
        print("   🛡️ Mask sensitive data: Privacy-aware testing")
        print("   📄 Full page capture: Complete page observation")
        print("   🎨 Quality control: Optimize file size vs clarity")
        
        print("\n🌟 Philosophy: Enhanced precision without changing what we observe!")
        
        return all_results
        
    except Exception as e:
        print(f"❌ Demo failed: {e}")
        return {"error": str(e)}


async def demonstrate_use_cases():
    """
    Show practical use cases for enhanced screenshot options
    """
    print("\n" + "=" * 60)
    print("🎪 Practical Use Cases for Enhanced Screenshots")
    print("=" * 60)
    
    flow = CursorFlow(
        base_url="http://localhost:3000",
        log_config={"source": "local", "paths": ["logs/app.log"]}
    )
    
    use_cases = []
    
    try:
        # Use Case 1: Component Library Testing
        print("\n🧩 Use Case 1: Component Library Testing")
        component_test = await flow.execute_and_collect([
            {"navigate": "/components/button"},
            {"screenshot": {
                "name": "button-component",
                "options": {"clip": {"selector": ".component-demo"}}
            }},
            {"navigate": "/components/modal"},
            {"screenshot": {
                "name": "modal-component", 
                "options": {"clip": {"selector": ".modal-container"}}
            }}
        ])
        use_cases.append({"name": "Component Library", "results": component_test})
        
        # Use Case 2: E-commerce Testing (with privacy)
        print("\n🛒 Use Case 2: E-commerce Testing (Privacy-Aware)")
        ecommerce_test = await flow.execute_and_collect([
            {"navigate": "/checkout"},
            {"screenshot": {
                "name": "checkout-safe",
                "options": {
                    "mask": [".credit-card", ".billing-address", ".personal-info"],
                    "full_page": True
                }
            }}
        ])
        use_cases.append({"name": "E-commerce Privacy", "results": ecommerce_test})
        
        # Use Case 3: Responsive Design Testing
        print("\n📱 Use Case 3: Responsive Design Testing")
        responsive_test = await flow.execute_and_collect([
            {"navigate": "/landing"},
            {"screenshot": {
                "name": "hero-section",
                "options": {"clip": {"selector": ".hero-section"}}
            }},
            {"screenshot": {
                "name": "navigation",
                "options": {"clip": {"selector": ".navbar"}}
            }}
        ])
        use_cases.append({"name": "Responsive Design", "results": responsive_test})
        
        print(f"\n✅ Use cases demonstrated: {len(use_cases)}")
        return use_cases
        
    except Exception as e:
        print(f"❌ Use cases demo failed: {e}")
        return {"error": str(e)}


if __name__ == "__main__":
    print("🚀 Starting CursorFlow Enhanced Screenshot Demo...")
    
    # Run the demonstrations
    asyncio.run(demonstrate_enhanced_screenshots())
    asyncio.run(demonstrate_use_cases())
    
    print("\n🎉 Enhanced Screenshot Demo Complete!")
    print("\n💡 Key Benefits:")
    print("   • More precise visual data collection")
    print("   • Privacy-aware testing capabilities")
    print("   • Component-focused analysis")
    print("   • Reduced artifact file sizes")
    print("   • Better CI/CD integration")
    print("\n🌌 Remember: We observe reality more precisely, never change it!")
