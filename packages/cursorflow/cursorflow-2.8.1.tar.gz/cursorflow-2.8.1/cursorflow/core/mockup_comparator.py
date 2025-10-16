"""
Mockup Comparator

Visual comparison system for mockup vs work-in-progress URLs.
Enables rapid iteration to match UI implementation to design mockups.
"""

import asyncio
import time
import json
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path
import logging

from .json_utils import safe_json_dump, safe_json_serialize
try:
    from PIL import Image, ImageDraw, ImageChops
    import numpy as np
    VISUAL_COMPARISON_AVAILABLE = True
    # Type aliases for when PIL is available
    PILImage = Image.Image
    NDArray = np.ndarray
except ImportError:
    # PIL/numpy not available - visual comparison features disabled
    Image = ImageDraw = ImageChops = np = None
    VISUAL_COMPARISON_AVAILABLE = False
    # Dummy types for when PIL/numpy are not available
    PILImage = Any
    NDArray = Any

from .browser_controller import BrowserController
from .css_iterator import CSSIterator


class MockupComparator:
    """
    Compare mockup designs with work-in-progress implementations
    
    Provides visual diff analysis and iteration guidance for UI matching.
    """
    
    def __init__(self):
        """Initialize mockup comparator"""
        self.logger = logging.getLogger(__name__)
        
        # Create artifacts in current working directory
        self.artifacts_base = Path.cwd() / ".cursorflow" / "artifacts"
        self.artifacts_base.mkdir(parents=True, exist_ok=True)
        
        # Ensure subdirectories exist
        (self.artifacts_base / "mockup_comparisons").mkdir(exist_ok=True)
        (self.artifacts_base / "visual_diffs").mkdir(exist_ok=True)
        (self.artifacts_base / "iteration_progress").mkdir(exist_ok=True)
        
        # Initialize CSS iterator for implementation testing
        self.css_iterator = CSSIterator()
    
    async def compare_mockup_to_implementation(
        self,
        mockup_url: str,
        implementation_url: str,
        mockup_actions: Optional[List[Dict]] = None,
        implementation_actions: Optional[List[Dict]] = None,
        comparison_config: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Compare mockup design to current implementation
        
        Args:
            mockup_url: URL of the design mockup/reference
            implementation_url: URL of the work-in-progress implementation
            mockup_actions: Optional actions to perform on mockup (clicks, scrolls, etc.)
            implementation_actions: Optional actions to perform on implementation
            comparison_config: {
                "viewports": [{"width": 1440, "height": 900, "name": "desktop"}],
                "diff_threshold": 0.1,  # Sensitivity for visual differences
                "ignore_regions": [{"x": 0, "y": 0, "width": 100, "height": 50}],
                "focus_regions": [{"x": 100, "y": 100, "width": 800, "height": 600}]
            }
            
        Returns:
            Complete comparison analysis for Cursor to analyze
        """
        try:
            timestamp = int(time.time())
            comparison_name = f"mockup_comparison_{timestamp}"
            
            config = comparison_config or {}
            viewports = config.get("viewports", [{"width": 1440, "height": 900, "name": "desktop"}])
            
            self.logger.info(f"Starting mockup comparison: {mockup_url} vs {implementation_url}")
            
            # Initialize dual browser sessions
            mockup_browser = BrowserController(mockup_url, {"headless": True})
            implementation_browser = BrowserController(implementation_url, {"headless": True})
            
            await mockup_browser.initialize()
            await implementation_browser.initialize()
            
            try:
                comparison_results = []
                
                # Test across all specified viewports
                for viewport in viewports:
                    viewport_name = viewport.get("name", f"{viewport['width']}x{viewport['height']}")
                    self.logger.info(f"Testing viewport: {viewport_name}")
                    
                    # Set viewport for both browsers
                    await mockup_browser.set_viewport(viewport["width"], viewport["height"])
                    await implementation_browser.set_viewport(viewport["width"], viewport["height"])
                    
                    # Navigate to initial pages with stabilization
                    await mockup_browser.navigate("/")
                    await asyncio.sleep(1)
                    await mockup_browser.page.wait_for_load_state("domcontentloaded")
                    
                    await implementation_browser.navigate("/")
                    await asyncio.sleep(1)
                    await implementation_browser.page.wait_for_load_state("domcontentloaded")
                    
                    # Execute any required actions on mockup
                    if mockup_actions:
                        await self._execute_actions_on_browser(mockup_browser, mockup_actions)
                    
                    # Execute any required actions on implementation
                    if implementation_actions:
                        await self._execute_actions_on_browser(implementation_browser, implementation_actions)
                    
                    # Final stabilization before capturing
                    await asyncio.sleep(0.5)
                    
                    # Capture screenshots
                    mockup_screenshot = await self._capture_comparison_screenshot(
                        mockup_browser, f"{comparison_name}_mockup_{viewport_name}"
                    )
                    implementation_screenshot = await self._capture_comparison_screenshot(
                        implementation_browser, f"{comparison_name}_implementation_{viewport_name}"
                    )
                    
                    # Perform visual comparison
                    visual_diff = await self._create_visual_diff(
                        mockup_screenshot, implementation_screenshot, 
                        f"{comparison_name}_{viewport_name}", config
                    )
                    
                    # Analyze layout differences
                    layout_analysis = await self._analyze_layout_differences(
                        mockup_browser, implementation_browser, viewport_name
                    )
                    
                    # Capture element-level differences
                    element_analysis = await self._analyze_element_differences(
                        mockup_browser, implementation_browser, viewport_name
                    )
                    
                    viewport_result = {
                        "viewport": viewport,
                        "mockup_screenshot": mockup_screenshot,
                        "implementation_screenshot": implementation_screenshot,
                        "visual_diff": visual_diff,
                        "layout_analysis": layout_analysis,
                        "element_analysis": element_analysis,
                        "timestamp": time.time()
                    }
                    
                    comparison_results.append(viewport_result)
                
                # Create comprehensive comparison report
                comparison_report = {
                    "comparison_id": comparison_name,
                    "timestamp": time.time(),
                    "mockup_url": mockup_url,
                    "implementation_url": implementation_url,
                    "viewports_tested": len(viewports),
                    "results": comparison_results,
                    "summary": self._create_comparison_summary(comparison_results)
                }
                
                # Save comparison report with safe serialization
                report_path = self.artifacts_base / "mockup_comparisons" / f"{comparison_name}.json"
                safe_json_dump(comparison_report, str(report_path))
                
                self.logger.info(f"Mockup comparison completed: {comparison_name}")
                return comparison_report
                
            finally:
                await mockup_browser.cleanup()
                await implementation_browser.cleanup()
                
        except Exception as e:
            self.logger.error(f"Mockup comparison failed: {e}")
            return {"error": str(e), "comparison_id": comparison_name if 'comparison_name' in locals() else None}
    
    async def iterative_ui_matching(
        self,
        mockup_url: str,
        implementation_url: str,
        css_improvements: List[Dict],
        base_actions: Optional[List[Dict]] = None,
        comparison_config: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Iteratively improve implementation to match mockup
        
        Args:
            mockup_url: Reference mockup URL
            implementation_url: Work-in-progress implementation URL
            css_improvements: [
                {
                    "name": "fix-header-spacing",
                    "css": ".header { padding: 2rem 0; }",
                    "rationale": "Match mockup header spacing"
                }
            ]
            base_actions: Actions to perform before each comparison
            comparison_config: Configuration for comparison sensitivity
            
        Returns:
            Iteration results with progress tracking toward mockup match
        """
        try:
            timestamp = int(time.time())
            iteration_session_id = f"ui_matching_{timestamp}"
            
            self.logger.info(f"Starting iterative UI matching session: {iteration_session_id}")
            
            # Capture baseline mockup state
            baseline_comparison = await self.compare_mockup_to_implementation(
                mockup_url, implementation_url, 
                base_actions, base_actions, comparison_config
            )
            
            if "error" in baseline_comparison:
                return baseline_comparison
            
            # Initialize implementation browser for CSS iteration
            implementation_browser = BrowserController(implementation_url, {"headless": True})
            await implementation_browser.initialize()
            
            try:
                # Execute base actions to set up page state
                if base_actions:
                    await self._execute_actions_on_browser(implementation_browser, base_actions)
                
                # Capture implementation baseline for CSS iteration
                implementation_baseline = await self.css_iterator.capture_baseline(implementation_browser.page)
                
                iteration_results = []
                
                # Apply each CSS improvement and compare to mockup
                for i, css_improvement in enumerate(css_improvements):
                    self.logger.info(f"Testing CSS improvement {i+1}/{len(css_improvements)}: {css_improvement.get('name', 'unnamed')}")
                    
                    # Apply CSS change to implementation
                    css_result = await self.css_iterator.apply_css_and_capture(
                        implementation_browser.page, css_improvement, implementation_baseline,
                        suffix=f"_iteration_{i+1}"
                    )
                    
                    # Compare improved implementation to mockup
                    improved_comparison = await self._compare_current_state_to_mockup(
                        mockup_url, implementation_browser, 
                        f"{iteration_session_id}_iteration_{i+1}", comparison_config
                    )
                    
                    # Calculate improvement metrics
                    improvement_metrics = self._calculate_improvement_metrics(
                        baseline_comparison, improved_comparison
                    )
                    
                    iteration_result = {
                        "iteration_number": i + 1,
                        "css_change": css_improvement,
                        "css_result": css_result,
                        "mockup_comparison": improved_comparison,
                        "improvement_metrics": improvement_metrics,
                        "timestamp": time.time()
                    }
                    
                    iteration_results.append(iteration_result)
                    
                    # Small delay to let changes settle
                    await asyncio.sleep(0.2)
                
                # Create comprehensive iteration report
                iteration_report = {
                    "session_id": iteration_session_id,
                    "timestamp": time.time(),
                    "mockup_url": mockup_url,
                    "implementation_url": implementation_url,
                    "baseline_comparison": baseline_comparison,
                    "iterations": iteration_results,
                    "total_iterations": len(css_improvements),
                    "summary": self._create_iteration_summary(baseline_comparison, iteration_results),
                    "best_iteration": self._find_best_iteration(iteration_results),
                    "final_recommendations": self._generate_final_recommendations(iteration_results)
                }
                
                # Save iteration report with safe JSON serialization
                report_path = self.artifacts_base / "iteration_progress" / f"{iteration_session_id}.json"
                safe_json_dump(iteration_report, str(report_path))
                
                self.logger.info(f"UI matching iteration completed: {iteration_session_id}")
                return iteration_report
                
            finally:
                await implementation_browser.cleanup()
                
        except Exception as e:
            self.logger.error(f"Iterative UI matching failed: {e}")
            return {"error": str(e), "session_id": iteration_session_id if 'iteration_session_id' in locals() else None}
    
    async def _execute_actions_on_browser(self, browser: BrowserController, actions: List[Dict]):
        """Execute actions on a specific browser instance"""
        for action in actions:
            if "navigate" in action:
                path = action["navigate"]
                await browser.navigate(path)
                # Wait for page to stabilize after navigation
                await asyncio.sleep(1)  # Brief pause for dynamic content rendering
                await browser.page.wait_for_load_state("domcontentloaded")
            elif "click" in action:
                selector = action["click"]
                if isinstance(selector, dict):
                    selector = selector["selector"]
                await browser.click(selector)
                await asyncio.sleep(0.5)  # Brief pause for UI response
            elif "wait_for" in action:
                selector = action["wait_for"]
                if isinstance(selector, dict):
                    selector = selector["selector"]
                await browser.wait_for_element(selector)
            elif "wait" in action:
                await asyncio.sleep(action["wait"])
            elif "scroll" in action:
                scroll_config = action["scroll"]
                await browser.page.evaluate(f"window.scrollTo({scroll_config.get('x', 0)}, {scroll_config.get('y', 0)})")
                await asyncio.sleep(0.3)  # Brief pause for scroll rendering
    
    async def _capture_comparison_screenshot(self, browser: BrowserController, name: str) -> str:
        """Capture screenshot for comparison"""
        screenshot_path = str(self.artifacts_base / "mockup_comparisons" / f"{name}.png")
        await browser.page.screenshot(path=screenshot_path, full_page=True)
        return screenshot_path
    
    async def _create_visual_diff(
        self, 
        mockup_path: str, 
        implementation_path: str, 
        diff_name: str,
        config: Dict
    ) -> Dict[str, Any]:
        """Create visual difference analysis between mockup and implementation"""
        
        if not VISUAL_COMPARISON_AVAILABLE:
            self.logger.warning("Visual comparison unavailable - PIL/numpy not installed")
            return {
                "error": "Visual comparison requires PIL and numpy",
                "diff_path": None,
                "highlighted_path": None,
                "similarity_score": 0.0,
                "difference_areas": [],
                "pixel_differences": 0,
                "total_pixels": 0,
                "note": "Install with: pip install pillow numpy"
            }
        
        try:
            # Load images
            mockup_img = Image.open(mockup_path)
            implementation_img = Image.open(implementation_path)
            
            # Ensure images are same size for comparison
            if mockup_img.size != implementation_img.size:
                # Resize to match the larger dimension
                max_width = max(mockup_img.width, implementation_img.width)
                max_height = max(mockup_img.height, implementation_img.height)
                
                mockup_img = mockup_img.resize((max_width, max_height), Image.Resampling.LANCZOS)
                implementation_img = implementation_img.resize((max_width, max_height), Image.Resampling.LANCZOS)
            
            # Create difference image
            diff_img = ImageChops.difference(mockup_img, implementation_img)
            
            # Create highlighted difference image
            highlighted_diff = self._create_highlighted_diff(mockup_img, implementation_img, diff_img, config)
            
            # Save difference images
            diff_path = str(self.artifacts_base / "visual_diffs" / f"{diff_name}_diff.png")
            highlighted_path = str(self.artifacts_base / "visual_diffs" / f"{diff_name}_highlighted.png")
            
            diff_img.save(diff_path)
            highlighted_diff.save(highlighted_path)
            
            # Calculate difference metrics
            diff_metrics = self._calculate_visual_diff_metrics(mockup_img, implementation_img, diff_img, config)
            
            return {
                "diff_image": diff_path,
                "highlighted_diff": highlighted_path,
                "metrics": diff_metrics,
                "similarity_score": diff_metrics.get("similarity_percentage", 0),
                "major_differences": diff_metrics.get("major_difference_regions", [])
            }
            
        except Exception as e:
            self.logger.error(f"Visual diff creation failed: {e}")
            return {"error": str(e)}
    
    def _create_highlighted_diff(self, mockup_img: PILImage, implementation_img: PILImage, diff_img: PILImage, config: Dict) -> PILImage:
        """Create highlighted difference image with colored regions"""
        # Convert to RGBA for overlay
        highlighted = implementation_img.convert("RGBA")
        overlay = Image.new("RGBA", highlighted.size, (0, 0, 0, 0))
        
        # Convert difference to numpy array for analysis
        diff_array = np.array(diff_img.convert("L"))
        
        # Find significant differences
        threshold = config.get("diff_threshold", 0.1) * 255
        significant_diff = diff_array > threshold
        
        # Create overlay for differences
        overlay_array = np.array(overlay)
        overlay_array[significant_diff] = [255, 0, 0, 100]  # Red highlight with transparency
        
        overlay = Image.fromarray(overlay_array, "RGBA")
        
        # Composite the overlay onto the implementation
        highlighted = Image.alpha_composite(highlighted, overlay)
        
        return highlighted.convert("RGB")
    
    def _calculate_visual_diff_metrics(self, mockup_img: PILImage, implementation_img: PILImage, diff_img: PILImage, config: Dict) -> Dict[str, Any]:
        """Calculate detailed visual difference metrics"""
        try:
            # Convert to numpy arrays for analysis
            mockup_array = np.array(mockup_img.convert("RGB"))
            implementation_array = np.array(implementation_img.convert("RGB"))
            diff_array = np.array(diff_img.convert("L"))
            
            # Calculate overall similarity
            total_pixels = diff_array.size
            threshold = config.get("diff_threshold", 0.1) * 255
            different_pixels = np.sum(diff_array > threshold)
            similarity_percentage = ((total_pixels - different_pixels) / total_pixels) * 100
            
            # Find major difference regions
            major_diff_regions = self._find_difference_regions(diff_array, threshold)
            
            # Calculate color difference metrics
            color_metrics = self._calculate_color_metrics(mockup_array, implementation_array)
            
            return {
                "similarity_percentage": round(similarity_percentage, 2),
                "different_pixels": int(different_pixels),
                "total_pixels": int(total_pixels),
                "major_difference_regions": major_diff_regions,
                "color_metrics": color_metrics,
                "threshold_used": threshold
            }
            
        except Exception as e:
            self.logger.error(f"Visual diff metrics calculation failed: {e}")
            return {"error": str(e)}
    
    def _find_difference_regions(self, diff_array: NDArray, threshold: float) -> List[Dict]:
        """Find regions with significant visual differences"""
        # This is a simplified implementation - could be enhanced with computer vision
        significant_diff = diff_array > threshold
        
        # Find bounding boxes of difference regions
        regions = []
        
        # Simple region detection (could be improved with connected components)
        if np.any(significant_diff):
            rows, cols = np.where(significant_diff)
            if len(rows) > 0:
                regions.append({
                    "x": int(np.min(cols)),
                    "y": int(np.min(rows)),
                    "width": int(np.max(cols) - np.min(cols)),
                    "height": int(np.max(rows) - np.min(rows)),
                    "area": int(np.sum(significant_diff))
                })
        
        return regions
    
    def _calculate_color_metrics(self, mockup_array: NDArray, implementation_array: NDArray) -> Dict[str, Any]:
        """Calculate color-based difference metrics"""
        try:
            # Calculate average colors
            mockup_avg_color = np.mean(mockup_array, axis=(0, 1))
            implementation_avg_color = np.mean(implementation_array, axis=(0, 1))
            
            # Calculate color distance
            color_distance = np.linalg.norm(mockup_avg_color - implementation_avg_color)
            
            return {
                "mockup_avg_color": mockup_avg_color.tolist(),
                "implementation_avg_color": implementation_avg_color.tolist(),
                "color_distance": float(color_distance)
            }
            
        except Exception as e:
            return {"error": str(e)}
    
    async def _analyze_layout_differences(self, mockup_browser: BrowserController, implementation_browser: BrowserController, viewport_name: str) -> Dict[str, Any]:
        """Analyze layout differences between mockup and implementation"""
        try:
            # Capture layout metrics from both pages
            mockup_layout = await mockup_browser.page.evaluate("""
                () => {
                    const elements = [];
                    const selectors = ['h1', 'h2', 'h3', 'nav', 'main', 'header', 'footer', '.btn', '.button', 'form', 'input'];
                    
                    selectors.forEach(selector => {
                        document.querySelectorAll(selector).forEach((el, index) => {
                            const rect = el.getBoundingClientRect();
                            const styles = window.getComputedStyle(el);
                            elements.push({
                                selector: selector + (index > 0 ? `[${index}]` : ''),
                                x: rect.x,
                                y: rect.y,
                                width: rect.width,
                                height: rect.height,
                                fontSize: styles.fontSize,
                                color: styles.color,
                                backgroundColor: styles.backgroundColor,
                                margin: styles.margin,
                                padding: styles.padding
                            });
                        });
                    });
                    
                    return elements;
                }
            """)
            
            implementation_layout = await implementation_browser.page.evaluate("""
                () => {
                    const elements = [];
                    const selectors = ['h1', 'h2', 'h3', 'nav', 'main', 'header', 'footer', '.btn', '.button', 'form', 'input'];
                    
                    selectors.forEach(selector => {
                        document.querySelectorAll(selector).forEach((el, index) => {
                            const rect = el.getBoundingClientRect();
                            const styles = window.getComputedStyle(el);
                            elements.push({
                                selector: selector + (index > 0 ? `[${index}]` : ''),
                                x: rect.x,
                                y: rect.y,
                                width: rect.width,
                                height: rect.height,
                                fontSize: styles.fontSize,
                                color: styles.color,
                                backgroundColor: styles.backgroundColor,
                                margin: styles.margin,
                                padding: styles.padding
                            });
                        });
                    });
                    
                    return elements;
                }
            """)
            
            # Compare layouts
            layout_differences = self._compare_layouts(mockup_layout, implementation_layout)
            
            return {
                "mockup_elements": len(mockup_layout),
                "implementation_elements": len(implementation_layout),
                "differences": layout_differences,
                "viewport": viewport_name
            }
            
        except Exception as e:
            self.logger.error(f"Layout analysis failed: {e}")
            return {"error": str(e)}
    
    def _compare_layouts(self, mockup_layout: List[Dict], implementation_layout: List[Dict]) -> List[Dict]:
        """Compare layout elements between mockup and implementation"""
        differences = []
        
        # Create lookup dictionaries
        mockup_elements = {el["selector"]: el for el in mockup_layout}
        implementation_elements = {el["selector"]: el for el in implementation_layout}
        
        # Find differences
        all_selectors = set(mockup_elements.keys()) | set(implementation_elements.keys())
        
        for selector in all_selectors:
            mockup_el = mockup_elements.get(selector)
            impl_el = implementation_elements.get(selector)
            
            if not mockup_el:
                differences.append({
                    "type": "missing_in_mockup",
                    "selector": selector,
                    "implementation_element": impl_el
                })
            elif not impl_el:
                differences.append({
                    "type": "missing_in_implementation",
                    "selector": selector,
                    "mockup_element": mockup_el
                })
            else:
                # Compare element properties
                element_diff = self._compare_element_properties(mockup_el, impl_el)
                if element_diff:
                    differences.append({
                        "type": "property_differences",
                        "selector": selector,
                        "differences": element_diff
                    })
        
        return differences
    
    def _compare_element_properties(self, mockup_el: Dict, impl_el: Dict) -> Dict[str, Any]:
        """Compare properties of individual elements"""
        differences = {}
        
        # Position differences
        position_threshold = 10  # pixels
        if abs(mockup_el["x"] - impl_el["x"]) > position_threshold:
            differences["x_position"] = {
                "mockup": mockup_el["x"],
                "implementation": impl_el["x"],
                "difference": impl_el["x"] - mockup_el["x"]
            }
        
        if abs(mockup_el["y"] - impl_el["y"]) > position_threshold:
            differences["y_position"] = {
                "mockup": mockup_el["y"],
                "implementation": impl_el["y"],
                "difference": impl_el["y"] - mockup_el["y"]
            }
        
        # Size differences
        size_threshold = 5  # pixels
        if abs(mockup_el["width"] - impl_el["width"]) > size_threshold:
            differences["width"] = {
                "mockup": mockup_el["width"],
                "implementation": impl_el["width"],
                "difference": impl_el["width"] - mockup_el["width"]
            }
        
        if abs(mockup_el["height"] - impl_el["height"]) > size_threshold:
            differences["height"] = {
                "mockup": mockup_el["height"],
                "implementation": impl_el["height"],
                "difference": impl_el["height"] - mockup_el["height"]
            }
        
        # Style differences
        if mockup_el["color"] != impl_el["color"]:
            differences["color"] = {
                "mockup": mockup_el["color"],
                "implementation": impl_el["color"]
            }
        
        if mockup_el["backgroundColor"] != impl_el["backgroundColor"]:
            differences["backgroundColor"] = {
                "mockup": mockup_el["backgroundColor"],
                "implementation": impl_el["backgroundColor"]
            }
        
        if mockup_el["fontSize"] != impl_el["fontSize"]:
            differences["fontSize"] = {
                "mockup": mockup_el["fontSize"],
                "implementation": impl_el["fontSize"]
            }
        
        return differences
    
    async def _analyze_element_differences(self, mockup_browser: BrowserController, implementation_browser: BrowserController, viewport_name: str) -> Dict[str, Any]:
        """Analyze specific element-level differences with detailed DOM and CSS data"""
        try:
            # Capture detailed DOM structure and CSS from both pages
            mockup_dom_data = await self._capture_detailed_dom_analysis(mockup_browser)
            implementation_dom_data = await self._capture_detailed_dom_analysis(implementation_browser)
            
            # Compare DOM structures
            dom_comparison = self._compare_dom_structures(mockup_dom_data, implementation_dom_data)
            
            # Compare CSS properties
            css_comparison = self._compare_css_properties(mockup_dom_data, implementation_dom_data)
            
            # Generate specific change recommendations
            change_recommendations = self._generate_css_change_recommendations(dom_comparison, css_comparison)
            
            return {
                "viewport": viewport_name,
                "mockup_dom_data": mockup_dom_data,
                "implementation_dom_data": implementation_dom_data,
                "dom_structure_comparison": dom_comparison,
                "css_property_comparison": css_comparison,
                "change_recommendations": change_recommendations,
                "analysis_timestamp": time.time()
            }
            
        except Exception as e:
            self.logger.error(f"Element analysis failed: {e}")
            return {"error": str(e), "viewport": viewport_name}
    
    async def _capture_detailed_dom_analysis(self, browser: BrowserController) -> Dict[str, Any]:
        """Capture comprehensive DOM structure and CSS data"""
        try:
            dom_analysis = await browser.page.evaluate("""
                () => {
                    // Helper function to get element path
                    function getElementPath(element) {
                        const path = [];
                        while (element && element.nodeType === Node.ELEMENT_NODE) {
                            let selector = element.nodeName.toLowerCase();
                            if (element.id) {
                                selector += '#' + element.id;
                            } else if (element.className) {
                                selector += '.' + element.className.split(' ').join('.');
                            }
                            path.unshift(selector);
                            element = element.parentNode;
                        }
                        return path.join(' > ');
                    }
                    
                    // Helper function to get comprehensive computed styles
                    function getComputedStylesDetailed(element) {
                        const computed = window.getComputedStyle(element);
                        return {
                            // Layout properties
                            display: computed.display,
                            position: computed.position,
                            top: computed.top,
                            left: computed.left,
                            right: computed.right,
                            bottom: computed.bottom,
                            width: computed.width,
                            height: computed.height,
                            minWidth: computed.minWidth,
                            maxWidth: computed.maxWidth,
                            minHeight: computed.minHeight,
                            maxHeight: computed.maxHeight,
                            
                            // Flexbox properties
                            flexDirection: computed.flexDirection,
                            flexWrap: computed.flexWrap,
                            justifyContent: computed.justifyContent,
                            alignItems: computed.alignItems,
                            alignContent: computed.alignContent,
                            flex: computed.flex,
                            flexGrow: computed.flexGrow,
                            flexShrink: computed.flexShrink,
                            flexBasis: computed.flexBasis,
                            
                            // Grid properties
                            gridTemplateColumns: computed.gridTemplateColumns,
                            gridTemplateRows: computed.gridTemplateRows,
                            gridGap: computed.gridGap,
                            gridArea: computed.gridArea,
                            
                            // Spacing
                            margin: computed.margin,
                            marginTop: computed.marginTop,
                            marginRight: computed.marginRight,
                            marginBottom: computed.marginBottom,
                            marginLeft: computed.marginLeft,
                            padding: computed.padding,
                            paddingTop: computed.paddingTop,
                            paddingRight: computed.paddingRight,
                            paddingBottom: computed.paddingBottom,
                            paddingLeft: computed.paddingLeft,
                            
                            // Typography
                            fontFamily: computed.fontFamily,
                            fontSize: computed.fontSize,
                            fontWeight: computed.fontWeight,
                            fontStyle: computed.fontStyle,
                            lineHeight: computed.lineHeight,
                            letterSpacing: computed.letterSpacing,
                            textAlign: computed.textAlign,
                            textDecoration: computed.textDecoration,
                            textTransform: computed.textTransform,
                            
                            // Colors and backgrounds
                            color: computed.color,
                            backgroundColor: computed.backgroundColor,
                            backgroundImage: computed.backgroundImage,
                            backgroundSize: computed.backgroundSize,
                            backgroundPosition: computed.backgroundPosition,
                            backgroundRepeat: computed.backgroundRepeat,
                            
                            // Borders
                            border: computed.border,
                            borderTop: computed.borderTop,
                            borderRight: computed.borderRight,
                            borderBottom: computed.borderBottom,
                            borderLeft: computed.borderLeft,
                            borderRadius: computed.borderRadius,
                            borderWidth: computed.borderWidth,
                            borderStyle: computed.borderStyle,
                            borderColor: computed.borderColor,
                            
                            // Visual effects
                            boxShadow: computed.boxShadow,
                            opacity: computed.opacity,
                            transform: computed.transform,
                            transition: computed.transition,
                            animation: computed.animation,
                            
                            // Z-index and overflow
                            zIndex: computed.zIndex,
                            overflow: computed.overflow,
                            overflowX: computed.overflowX,
                            overflowY: computed.overflowY
                        };
                    }
                    
                    // Get all significant elements
                    const elements = [];
                    const selectors = [
                        // Structural elements
                        'body', 'main', 'header', 'nav', 'aside', 'footer', 'section', 'article',
                        // Common containers
                        '.container', '.wrapper', '.content', '.sidebar', '.header', '.footer',
                        '.navbar', '.nav', '.menu', '.main', '.page', '.app',
                        // Interactive elements
                        'button', '.btn', '.button', 'a', '.link', 'input', 'form', '.form',
                        // Content elements
                        'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p', '.title', '.heading',
                        // Layout elements
                        '.row', '.col', '.column', '.grid', '.flex', '.card', '.panel',
                        // Common UI components
                        '.modal', '.dropdown', '.tooltip', '.alert', '.badge', '.tab'
                    ];
                    
                    selectors.forEach(selector => {
                        try {
                            document.querySelectorAll(selector).forEach((element, index) => {
                                const rect = element.getBoundingClientRect();
                                const computedStyles = getComputedStylesDetailed(element);
                                
                                // Only include visible elements
                                if (rect.width > 0 && rect.height > 0) {
                                    elements.push({
                                        selector: selector,
                                        index: index,
                                        uniqueSelector: selector + (index > 0 ? `:nth-of-type(${index + 1})` : ''),
                                        elementPath: getElementPath(element),
                                        tagName: element.tagName.toLowerCase(),
                                        id: element.id || null,
                                        className: element.className || null,
                                        textContent: element.textContent ? element.textContent.trim().substring(0, 100) : null,
                                        
                                        // Bounding box
                                        boundingBox: {
                                            x: rect.x,
                                            y: rect.y,
                                            width: rect.width,
                                            height: rect.height,
                                            top: rect.top,
                                            left: rect.left,
                                            right: rect.right,
                                            bottom: rect.bottom
                                        },
                                        
                                        // All computed styles
                                        computedStyles: computedStyles,
                                        
                                        // Element attributes
                                        attributes: Array.from(element.attributes).reduce((attrs, attr) => {
                                            attrs[attr.name] = attr.value;
                                            return attrs;
                                        }, {}),
                                        
                                        // Children count
                                        childrenCount: element.children.length,
                                        
                                        // Visibility
                                        isVisible: rect.width > 0 && rect.height > 0 && computedStyles.display !== 'none' && computedStyles.visibility !== 'hidden'
                                    });
                                }
                            });
                        } catch (e) {
                            console.warn(`Failed to analyze selector ${selector}:`, e);
                        }
                    });
                    
                    // Get page-level information
                    const pageInfo = {
                        title: document.title,
                        url: window.location.href,
                        viewport: {
                            width: window.innerWidth,
                            height: window.innerHeight
                        },
                        documentSize: {
                            width: Math.max(
                                document.body.scrollWidth,
                                document.body.offsetWidth,
                                document.documentElement.clientWidth,
                                document.documentElement.scrollWidth,
                                document.documentElement.offsetWidth
                            ),
                            height: Math.max(
                                document.body.scrollHeight,
                                document.body.offsetHeight,
                                document.documentElement.clientHeight,
                                document.documentElement.scrollHeight,
                                document.documentElement.offsetHeight
                            )
                        }
                    };
                    
                    return {
                        pageInfo: pageInfo,
                        elements: elements,
                        totalElements: elements.length,
                        captureTimestamp: Date.now()
                    };
                }
            """)
            
            return dom_analysis
            
        except Exception as e:
            self.logger.error(f"DOM analysis capture failed: {e}")
            return {"error": str(e)}
    
    def _compare_dom_structures(self, mockup_data: Dict, implementation_data: Dict) -> Dict[str, Any]:
        """Compare DOM structures between mockup and implementation"""
        try:
            mockup_elements = {el['uniqueSelector']: el for el in mockup_data.get('elements', [])}
            implementation_elements = {el['uniqueSelector']: el for el in implementation_data.get('elements', [])}
            
            # Find missing, extra, and common elements
            mockup_selectors = set(mockup_elements.keys())
            implementation_selectors = set(implementation_elements.keys())
            
            missing_in_implementation = mockup_selectors - implementation_selectors
            extra_in_implementation = implementation_selectors - mockup_selectors
            common_elements = mockup_selectors & implementation_selectors
            
            # Analyze structural differences
            structural_differences = []
            
            for selector in missing_in_implementation:
                element = mockup_elements[selector]
                structural_differences.append({
                    "type": "missing_element",
                    "selector": selector,
                    "element_path": element.get('elementPath'),
                    "mockup_element": {
                        "tagName": element.get('tagName'),
                        "className": element.get('className'),
                        "textContent": element.get('textContent'),
                        "boundingBox": element.get('boundingBox')
                    },
                    "severity": "high" if element.get('tagName') in ['nav', 'header', 'main', 'footer'] else "medium"
                })
            
            for selector in extra_in_implementation:
                element = implementation_elements[selector]
                structural_differences.append({
                    "type": "extra_element",
                    "selector": selector,
                    "element_path": element.get('elementPath'),
                    "implementation_element": {
                        "tagName": element.get('tagName'),
                        "className": element.get('className'),
                        "textContent": element.get('textContent'),
                        "boundingBox": element.get('boundingBox')
                    },
                    "severity": "low"
                })
            
            return {
                "missing_in_implementation": list(missing_in_implementation),
                "extra_in_implementation": list(extra_in_implementation),
                "common_elements": list(common_elements),
                "structural_differences": structural_differences,
                "similarity_score": len(common_elements) / max(len(mockup_selectors), len(implementation_selectors)) * 100 if mockup_selectors or implementation_selectors else 100
            }
            
        except Exception as e:
            self.logger.error(f"DOM structure comparison failed: {e}")
            return {"error": str(e)}
    
    def _compare_css_properties(self, mockup_data: Dict, implementation_data: Dict) -> Dict[str, Any]:
        """Compare CSS properties between matching elements"""
        try:
            mockup_elements = {el['uniqueSelector']: el for el in mockup_data.get('elements', [])}
            implementation_elements = {el['uniqueSelector']: el for el in implementation_data.get('elements', [])}
            
            css_differences = []
            
            # Compare common elements
            common_selectors = set(mockup_elements.keys()) & set(implementation_elements.keys())
            
            for selector in common_selectors:
                mockup_el = mockup_elements[selector]
                impl_el = implementation_elements[selector]
                
                mockup_styles = mockup_el.get('computedStyles', {})
                impl_styles = impl_el.get('computedStyles', {})
                
                # Compare key CSS properties
                property_differences = {}
                
                # Important properties to compare
                key_properties = [
                    'display', 'position', 'width', 'height', 'top', 'left', 'right', 'bottom',
                    'margin', 'marginTop', 'marginRight', 'marginBottom', 'marginLeft',
                    'padding', 'paddingTop', 'paddingRight', 'paddingBottom', 'paddingLeft',
                    'fontSize', 'fontWeight', 'fontFamily', 'lineHeight', 'textAlign',
                    'color', 'backgroundColor', 'border', 'borderRadius', 'boxShadow',
                    'flexDirection', 'justifyContent', 'alignItems', 'gridTemplateColumns'
                ]
                
                for prop in key_properties:
                    mockup_value = mockup_styles.get(prop, '')
                    impl_value = impl_styles.get(prop, '')
                    
                    if mockup_value != impl_value:
                        # Calculate significance of difference
                        significance = self._calculate_css_difference_significance(prop, mockup_value, impl_value)
                        
                        property_differences[prop] = {
                            "mockup_value": mockup_value,
                            "implementation_value": impl_value,
                            "significance": significance,
                            "css_property": prop
                        }
                
                if property_differences:
                    # Compare bounding boxes for layout impact
                    mockup_box = mockup_el.get('boundingBox', {})
                    impl_box = impl_el.get('boundingBox', {})
                    
                    layout_impact = {
                        "position_difference": {
                            "x": abs(mockup_box.get('x', 0) - impl_box.get('x', 0)),
                            "y": abs(mockup_box.get('y', 0) - impl_box.get('y', 0))
                        },
                        "size_difference": {
                            "width": abs(mockup_box.get('width', 0) - impl_box.get('width', 0)),
                            "height": abs(mockup_box.get('height', 0) - impl_box.get('height', 0))
                        }
                    }
                    
                    css_differences.append({
                        "selector": selector,
                        "element_path": mockup_el.get('elementPath'),
                        "property_differences": property_differences,
                        "layout_impact": layout_impact,
                        "difference_count": len(property_differences),
                        "severity": "high" if len(property_differences) > 5 else "medium" if len(property_differences) > 2 else "low"
                    })
            
            return {
                "elements_compared": len(common_selectors),
                "elements_with_differences": len(css_differences),
                "css_differences": css_differences,
                "overall_css_similarity": max(0, 100 - (len(css_differences) / max(len(common_selectors), 1) * 100))
            }
            
        except Exception as e:
            self.logger.error(f"CSS property comparison failed: {e}")
            return {"error": str(e)}
    
    def _calculate_css_difference_significance(self, property: str, mockup_value: str, impl_value: str) -> str:
        """Calculate the significance of a CSS property difference"""
        
        # High significance properties (major visual impact)
        high_impact_props = ['display', 'position', 'width', 'height', 'backgroundColor', 'color', 'fontSize']
        
        # Medium significance properties (moderate visual impact)
        medium_impact_props = ['margin', 'padding', 'border', 'borderRadius', 'fontWeight', 'textAlign']
        
        if property in high_impact_props:
            return "high"
        elif property in medium_impact_props:
            return "medium"
        else:
            return "low"
    
    def _generate_css_change_recommendations(self, dom_comparison: Dict, css_comparison: Dict) -> List[Dict]:
        """Generate specific CSS change recommendations based on analysis"""
        try:
            recommendations = []
            
            # Recommendations for missing elements
            for diff in dom_comparison.get('structural_differences', []):
                if diff['type'] == 'missing_element':
                    mockup_element = diff['mockup_element']
                    recommendations.append({
                        "type": "add_element",
                        "priority": diff['severity'],
                        "selector": diff['selector'],
                        "description": f"Add missing {mockup_element['tagName']} element",
                        "suggested_html": f"<{mockup_element['tagName']} class=\"{mockup_element.get('className', '')}\">{mockup_element.get('textContent', '')}</{mockup_element['tagName']}>",
                        "estimated_effort": "medium"
                    })
            
            # Recommendations for CSS property differences
            for element_diff in css_comparison.get('css_differences', []):
                selector = element_diff['selector']
                property_diffs = element_diff['property_differences']
                
                # Generate CSS rule for this element
                css_rules = []
                for prop, diff in property_diffs.items():
                    css_property = self._convert_to_css_property(prop)
                    css_rules.append(f"  {css_property}: {diff['mockup_value']};")
                
                if css_rules:
                    css_rule = f"{selector} {{\n" + "\n".join(css_rules) + "\n}"
                    
                    recommendations.append({
                        "type": "modify_css",
                        "priority": element_diff['severity'],
                        "selector": selector,
                        "description": f"Update CSS properties for {selector}",
                        "suggested_css": css_rule,
                        "properties_to_change": list(property_diffs.keys()),
                        "layout_impact": element_diff['layout_impact'],
                        "estimated_effort": "low" if len(property_diffs) <= 2 else "medium"
                    })
            
            # Sort by priority and impact
            priority_order = {"high": 3, "medium": 2, "low": 1}
            recommendations.sort(key=lambda x: priority_order.get(x['priority'], 0), reverse=True)
            
            return recommendations
            
        except Exception as e:
            self.logger.error(f"CSS recommendation generation failed: {e}")
            return []
    
    def _convert_to_css_property(self, computed_property: str) -> str:
        """Convert computed style property name to CSS property name"""
        # Convert camelCase to kebab-case
        css_property = ""
        for char in computed_property:
            if char.isupper():
                css_property += "-" + char.lower()
            else:
                css_property += char
        return css_property
    
    async def _compare_current_state_to_mockup(
        self, 
        mockup_url: str, 
        implementation_browser: BrowserController, 
        comparison_name: str,
        config: Optional[Dict]
    ) -> Dict[str, Any]:
        """Compare current implementation state to mockup"""
        # Initialize mockup browser for comparison
        mockup_browser = BrowserController(mockup_url, {"headless": True})
        await mockup_browser.initialize()
        
        try:
            # Navigate mockup browser
            await mockup_browser.navigate("/")
            
            # Capture screenshots
            mockup_screenshot = await self._capture_comparison_screenshot(
                mockup_browser, f"{comparison_name}_mockup"
            )
            implementation_screenshot = await self._capture_comparison_screenshot(
                implementation_browser, f"{comparison_name}_implementation"
            )
            
            # Create visual diff
            visual_diff = await self._create_visual_diff(
                mockup_screenshot, implementation_screenshot, comparison_name, config or {}
            )
            
            return {
                "mockup_screenshot": mockup_screenshot,
                "implementation_screenshot": implementation_screenshot,
                "visual_diff": visual_diff,
                "comparison_name": comparison_name
            }
            
        finally:
            await mockup_browser.cleanup()
    
    def _calculate_improvement_metrics(self, baseline_comparison: Dict, improved_comparison: Dict) -> Dict[str, Any]:
        """Calculate improvement metrics between baseline and improved implementation"""
        try:
            baseline_similarity = 0
            improved_similarity = 0
            
            # Extract similarity scores from comparison results
            if "results" in baseline_comparison and baseline_comparison["results"]:
                baseline_result = baseline_comparison["results"][0]  # Use first viewport
                baseline_similarity = baseline_result.get("visual_diff", {}).get("similarity_score", 0)
            
            if "visual_diff" in improved_comparison:
                improved_similarity = improved_comparison["visual_diff"].get("similarity_score", 0)
            
            improvement = improved_similarity - baseline_similarity
            
            return {
                "baseline_similarity": float(baseline_similarity),
                "improved_similarity": float(improved_similarity),
                "improvement": float(improvement),
                "improvement_percentage": round(float(improvement), 2),
                "is_improvement": bool(improvement > 0)  # Convert to Python bool
            }
            
        except Exception as e:
            self.logger.error(f"Improvement metrics calculation failed: {e}")
            return {"error": str(e)}
    
    def _create_comparison_summary(self, comparison_results: List[Dict]) -> Dict[str, Any]:
        """Create summary of comparison results"""
        if not comparison_results:
            return {"error": "No comparison results"}
        
        # Calculate average similarity across viewports
        similarities = []
        for result in comparison_results:
            similarity = result.get("visual_diff", {}).get("similarity_score", 0)
            similarities.append(similarity)
        
        avg_similarity = sum(similarities) / len(similarities) if similarities else 0
        
        # Pure data summary - no interpretation
        return {
            "average_similarity": round(float(avg_similarity), 2),
            "viewports_tested": len(comparison_results),
            "similarity_by_viewport": [
                {
                    "viewport": result.get("viewport", {}).get("name", "unknown"),
                    "similarity": float(result.get("visual_diff", {}).get("similarity_score", 0))
                }
                for result in comparison_results
            ]
        }
    
    
    def _create_iteration_summary(self, baseline_comparison: Dict, iteration_results: List[Dict]) -> Dict[str, Any]:
        """Create summary of iteration session"""
        if not iteration_results:
            return {"error": "No iteration results"}
        
        # Track improvement over iterations
        improvements = []
        for result in iteration_results:
            improvement = result.get("improvement_metrics", {}).get("improvement", 0)
            improvements.append(improvement)
        
        total_improvement = sum(improvements)
        best_improvement = max(improvements) if improvements else 0
        
        return {
            "total_iterations": len(iteration_results),
            "total_improvement": round(total_improvement, 2),
            "best_single_improvement": round(best_improvement, 2),
            "successful_iterations": len([r for r in iteration_results if r.get("improvement_metrics", {}).get("is_improvement", False)]),
            "average_improvement_per_iteration": round(total_improvement / len(iteration_results), 2) if iteration_results else 0
        }
    
    def _find_best_iteration(self, iteration_results: List[Dict]) -> Optional[Dict]:
        """Find the iteration with the best improvement"""
        if not iteration_results:
            return None
        
        best_iteration = max(
            iteration_results, 
            key=lambda x: x.get("improvement_metrics", {}).get("improved_similarity", 0)
        )
        
        return {
            "iteration_number": best_iteration.get("iteration_number"),
            "css_change": best_iteration.get("css_change"),
            "similarity_achieved": best_iteration.get("improvement_metrics", {}).get("improved_similarity", 0),
            "improvement": best_iteration.get("improvement_metrics", {}).get("improvement", 0)
        }
    
    def _generate_final_recommendations(self, iteration_results: List[Dict]) -> List[Dict]:
        """Generate final recommendations based on all iterations"""
        recommendations = []
        
        # Find the most successful CSS changes
        successful_changes = [
            result for result in iteration_results 
            if result.get("improvement_metrics", {}).get("is_improvement", False)
        ]
        
        if successful_changes:
            recommendations.append({
                "type": "apply_successful_changes",
                "priority": "high",
                "description": f"Apply the {len(successful_changes)} successful CSS changes to your codebase",
                "changes": [result.get("css_change") for result in successful_changes]
            })
        
        # Identify areas that still need work
        final_similarities = [
            result.get("improvement_metrics", {}).get("improved_similarity", 0)
            for result in iteration_results
        ]
        
        if final_similarities and max(final_similarities) < 85:
            recommendations.append({
                "type": "additional_work_needed",
                "priority": "medium",
                "description": "Additional CSS improvements needed to achieve closer mockup match",
                "current_best_similarity": max(final_similarities) if final_similarities else 0
            })
        
        return recommendations
