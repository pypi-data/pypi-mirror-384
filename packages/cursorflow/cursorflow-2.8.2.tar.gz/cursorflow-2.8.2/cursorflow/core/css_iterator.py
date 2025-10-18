"""
CSS Iterator

Visual development support for rapid CSS iteration with instant feedback.
Captures visual states, applies CSS changes, and provides comparison data
for Cursor to analyze layout improvements.
"""

import asyncio
import time
import json
from typing import Dict, List, Optional, Any
from pathlib import Path
import logging


class CSSIterator:
    """
    CSS iteration support - captures visual data for Cursor analysis
    
    Provides visual comparison data without interpretation - Cursor decides
    which CSS changes are improvements.
    """
    
    def __init__(self):
        """Initialize CSS iterator"""
        self.logger = logging.getLogger(__name__)
        
        # Create artifacts in current working directory (user's project)
        self.artifacts_base = Path.cwd() / ".cursorflow" / "artifacts"
        self.artifacts_base.mkdir(parents=True, exist_ok=True)
        
        # Ensure subdirectories exist
        (self.artifacts_base / "css_iterations").mkdir(exist_ok=True)
        (self.artifacts_base / "screenshots").mkdir(exist_ok=True)
        (self.artifacts_base / "sessions").mkdir(exist_ok=True)
    
    async def capture_baseline(self, page) -> Dict[str, Any]:
        """
        Capture baseline visual state before CSS changes
        
        Args:
            page: Playwright page object
            
        Returns:
            Baseline data for Cursor to compare against
        """
        try:
            timestamp = int(time.time())
            baseline_name = f"baseline_{timestamp}"
            
            # Capture screenshot
            screenshot_path = str(self.artifacts_base / "css_iterations" / f"{baseline_name}.png")
            await page.screenshot(path=screenshot_path, full_page=True)
            
            # Capture layout metrics
            layout_metrics = await self._capture_layout_metrics(page)
            
            # Capture computed styles for key elements
            computed_styles = await self._capture_computed_styles(page)
            
            # Capture performance baseline
            performance_metrics = await self._capture_performance_metrics(page)
            
            baseline_data = {
                "timestamp": time.time(),
                "screenshot": screenshot_path,
                "layout_metrics": layout_metrics,
                "computed_styles": computed_styles,
                "performance_metrics": performance_metrics,
                "name": baseline_name
            }
            
            self.logger.info(f"Captured baseline: {baseline_name}")
            return baseline_data
            
        except Exception as e:
            self.logger.error(f"Baseline capture failed: {e}")
            return {"error": str(e)}
    
    async def apply_css_and_capture(
        self, 
        page, 
        css_change: Dict, 
        baseline: Dict,
        suffix: str = ""
    ) -> Dict[str, Any]:
        """
        Apply CSS change and capture resulting visual state
        
        Args:
            page: Playwright page object
            css_change: {"name": "fix-name", "css": ".class { prop: value; }", "rationale": "why"}
            baseline: Baseline data for comparison
            suffix: Optional suffix for file naming (e.g., "_mobile")
            
        Returns:
            Iteration data for Cursor to analyze
        """
        try:
            iteration_name = css_change.get("name", "unnamed")
            css_code = css_change.get("css", "")
            
            if not css_code:
                return {"error": "No CSS code provided"}
            
            timestamp = int(time.time())
            iteration_file_name = f"{iteration_name}_{timestamp}{suffix}"
            
            # Apply CSS to page
            await page.add_style_tag(content=css_code)
            
            # Wait for layout to stabilize
            await page.wait_for_timeout(200)
            
            # Capture new visual state
            screenshot_path = str(self.artifacts_base / "css_iterations" / f"{iteration_file_name}.png")
            await page.screenshot(path=screenshot_path, full_page=True)
            
            # Capture new layout metrics
            new_layout_metrics = await self._capture_layout_metrics(page)
            
            # Capture new computed styles
            new_computed_styles = await self._capture_computed_styles(page)
            
            # Capture performance impact
            new_performance_metrics = await self._capture_performance_metrics(page)
            
            # Capture any console errors introduced by CSS
            console_errors = await self._capture_console_errors(page)
            
            # Create comparison data (simple differences, no analysis)
            layout_changes = self._calculate_layout_differences(
                baseline.get("layout_metrics", {}),
                new_layout_metrics
            )
            
            style_changes = self._calculate_style_differences(
                baseline.get("computed_styles", {}),
                new_computed_styles
            )
            
            iteration_data = {
                "timestamp": time.time(),
                "name": iteration_name,
                "css_applied": css_code,
                "rationale": css_change.get("rationale", ""),
                "screenshot": screenshot_path,
                "layout_metrics": new_layout_metrics,
                "computed_styles": new_computed_styles,
                "performance_metrics": new_performance_metrics,
                "console_errors": console_errors,
                "changes": {
                    "layout_differences": layout_changes,
                    "style_differences": style_changes
                }
            }
            
            self.logger.info(f"Applied CSS iteration: {iteration_name}")
            return iteration_data
            
        except Exception as e:
            self.logger.error(f"CSS iteration failed: {e}")
            return {"error": str(e), "name": css_change.get("name", "unknown")}
    
    async def _capture_layout_metrics(self, page) -> Dict[str, Any]:
        """Capture layout metrics for comparison"""
        try:
            metrics = await page.evaluate("""
                () => {
                    const body = document.body;
                    const html = document.documentElement;
                    
                    // Document dimensions
                    const documentHeight = Math.max(
                        body.scrollHeight, body.offsetHeight,
                        html.clientHeight, html.scrollHeight, html.offsetHeight
                    );
                    
                    const documentWidth = Math.max(
                        body.scrollWidth, body.offsetWidth,
                        html.clientWidth, html.scrollWidth, html.offsetWidth
                    );
                    
                    // Viewport info
                    const viewport = {
                        width: window.innerWidth,
                        height: window.innerHeight
                    };
                    
                    // Scroll info
                    const scroll = {
                        x: window.pageXOffset,
                        y: window.pageYOffset,
                        maxX: documentWidth - viewport.width,
                        maxY: documentHeight - viewport.height
                    };
                    
                    // Element positions for key elements
                    const elements = [];
                    const selectors = ['main', 'header', 'nav', 'aside', 'footer', '.container', '#content'];
                    
                    selectors.forEach(selector => {
                        const el = document.querySelector(selector);
                        if (el) {
                            const rect = el.getBoundingClientRect();
                            elements.push({
                                selector: selector,
                                x: rect.x,
                                y: rect.y,
                                width: rect.width,
                                height: rect.height,
                                top: rect.top,
                                left: rect.left
                            });
                        }
                    });
                    
                    return {
                        document: {
                            width: documentWidth,
                            height: documentHeight
                        },
                        viewport: viewport,
                        scroll: scroll,
                        elements: elements
                    };
                }
            """)
            
            return metrics
            
        except Exception as e:
            self.logger.error(f"Layout metrics capture failed: {e}")
            return {}
    
    async def _capture_computed_styles(self, page) -> Dict[str, Any]:
        """Capture computed styles for key elements"""
        try:
            styles = await page.evaluate("""
                () => {
                    const elements = {};
                    
                    // Key selectors to monitor
                    const selectors = [
                        'body', 'main', 'header', 'nav', 'aside', 'footer',
                        '.container', '.content', '.sidebar', '.wrapper',
                        '#main', '#content', '#sidebar'
                    ];
                    
                    selectors.forEach(selector => {
                        const el = document.querySelector(selector);
                        if (el) {
                            const computed = window.getComputedStyle(el);
                            elements[selector] = {
                                display: computed.display,
                                position: computed.position,
                                flexDirection: computed.flexDirection,
                                justifyContent: computed.justifyContent,
                                alignItems: computed.alignItems,
                                gridTemplateColumns: computed.gridTemplateColumns,
                                gridTemplateRows: computed.gridTemplateRows,
                                width: computed.width,
                                height: computed.height,
                                margin: computed.margin,
                                padding: computed.padding,
                                backgroundColor: computed.backgroundColor,
                                color: computed.color,
                                fontSize: computed.fontSize,
                                lineHeight: computed.lineHeight
                            };
                        }
                    });
                    
                    return elements;
                }
            """)
            
            return styles
            
        except Exception as e:
            self.logger.error(f"Computed styles capture failed: {e}")
            return {}
    
    async def _capture_performance_metrics(self, page) -> Dict[str, Any]:
        """Capture performance metrics"""
        try:
            metrics = await page.evaluate("""
                () => {
                    const perf = performance;
                    const navigation = perf.getEntriesByType('navigation')[0];
                    const paint = perf.getEntriesByType('paint');
                    
                    return {
                        renderTime: navigation ? navigation.loadEventEnd - navigation.loadEventStart : 0,
                        domContentLoaded: navigation ? navigation.domContentLoadedEventEnd - navigation.navigationStart : 0,
                        firstPaint: paint.find(p => p.name === 'first-paint')?.startTime || 0,
                        firstContentfulPaint: paint.find(p => p.name === 'first-contentful-paint')?.startTime || 0,
                        layoutShifts: perf.getEntriesByType('layout-shift').length
                    };
                }
            """)
            
            return metrics
            
        except Exception as e:
            self.logger.error(f"Performance metrics capture failed: {e}")
            return {}
    
    async def _capture_console_errors(self, page) -> List[Dict]:
        """Capture any console errors that occurred"""
        # This would be captured by the browser controller's console monitoring
        # For now, return empty - browser controller handles console errors
        return []
    
    def _calculate_layout_differences(self, baseline: Dict, current: Dict) -> Dict[str, Any]:
        """Calculate simple layout differences - NO ANALYSIS"""
        differences = {}
        
        # Document size changes
        baseline_doc = baseline.get("document", {})
        current_doc = current.get("document", {})
        
        if baseline_doc and current_doc:
            differences["document_size"] = {
                "width_change": current_doc.get("width", 0) - baseline_doc.get("width", 0),
                "height_change": current_doc.get("height", 0) - baseline_doc.get("height", 0)
            }
        
        # Element position changes
        baseline_elements = {el["selector"]: el for el in baseline.get("elements", [])}
        current_elements = {el["selector"]: el for el in current.get("elements", [])}
        
        element_changes = {}
        for selector in set(baseline_elements.keys()) | set(current_elements.keys()):
            baseline_el = baseline_elements.get(selector, {})
            current_el = current_elements.get(selector, {})
            
            if baseline_el and current_el:
                element_changes[selector] = {
                    "x_change": current_el.get("x", 0) - baseline_el.get("x", 0),
                    "y_change": current_el.get("y", 0) - baseline_el.get("y", 0),
                    "width_change": current_el.get("width", 0) - baseline_el.get("width", 0),
                    "height_change": current_el.get("height", 0) - baseline_el.get("height", 0)
                }
        
        differences["elements"] = element_changes
        return differences
    
    def _calculate_style_differences(self, baseline: Dict, current: Dict) -> Dict[str, Any]:
        """Calculate simple style differences - NO ANALYSIS"""
        differences = {}
        
        all_selectors = set(baseline.keys()) | set(current.keys())
        
        for selector in all_selectors:
            baseline_styles = baseline.get(selector, {})
            current_styles = current.get(selector, {})
            
            selector_changes = {}
            all_properties = set(baseline_styles.keys()) | set(current_styles.keys())
            
            for prop in all_properties:
                baseline_value = baseline_styles.get(prop, "")
                current_value = current_styles.get(prop, "")
                
                if baseline_value != current_value:
                    selector_changes[prop] = {
                        "from": baseline_value,
                        "to": current_value
                    }
            
            if selector_changes:
                differences[selector] = selector_changes
        
        return differences
    
    def create_comparison_summary(self, baseline: Dict, iterations: List[Dict]) -> Dict[str, Any]:
        """Create simple comparison data for Cursor analysis"""
        return {
            "baseline": {
                "screenshot": baseline.get("screenshot"),
                "timestamp": baseline.get("timestamp")
            },
            "iterations": [
                {
                    "name": iteration.get("name"),
                    "screenshot": iteration.get("screenshot"),
                    "css_applied": iteration.get("css_applied"),
                    "has_console_errors": len(iteration.get("console_errors", [])) > 0,
                    "layout_changed": bool(iteration.get("changes", {}).get("layout_differences", {})),
                    "styles_changed": bool(iteration.get("changes", {}).get("style_differences", {}))
                }
                for iteration in iterations
            ],
            "total_iterations": len(iterations)
        }
