"""
Universal Test Agent - Main orchestrator class

This is the primary interface for the universal testing framework.
It coordinates browser automation, log monitoring, and report generation
for any web architecture.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any
from pathlib import Path

from .browser_engine import BrowserEngine
from .log_monitor import LogMonitor
from .error_correlator import ErrorCorrelator
from .report_generator import ReportGenerator

class TestAgent:
    """Universal testing agent that adapts to any web framework"""
    
    def __init__(
        self,
        framework: str,
        base_url: str,
        logs: str = 'local',
        **config
    ):
        """
        Initialize universal test agent
        
        Args:
            framework: Target framework ('mod_perl', 'react', 'php', 'django', 'vue')
            base_url: Base URL for testing (e.g., 'http://localhost:3000')
            logs: Log source type ('local', 'ssh', 'docker', 'systemd', 'cloud')
            **config: Framework and environment specific configuration
        """
        self.framework = framework
        self.base_url = base_url
        self.config = config
        
        # Load framework-specific adapter
        self.adapter = self._load_adapter(framework)
        
        # Initialize core components
        self.browser_engine = BrowserEngine(base_url, self.adapter)
        self.log_monitor = LogMonitor(logs, config.get('log_config', {}))
        self.error_correlator = ErrorCorrelator(self.adapter.get_error_patterns())
        self.report_generator = ReportGenerator()
        
        # State tracking
        self.current_test = None
        self.test_results = []
        
        # Setup logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
    def _load_adapter(self, framework: str):
        """Dynamically load framework-specific adapter"""
        adapter_map = {
            'mod_perl': 'ModPerlAdapter',
            'react': 'ReactAdapter',
            'vue': 'VueAdapter', 
            'php': 'PHPAdapter',
            'django': 'DjangoAdapter',
            'flask': 'FlaskAdapter'
        }
        
        if framework not in adapter_map:
            raise ValueError(f"Unsupported framework: {framework}")
            
        # Dynamic import of adapter
        module_name = f"..adapters.{framework}"
        class_name = adapter_map[framework]
        
        try:
            module = __import__(module_name, fromlist=[class_name], level=1)
            adapter_class = getattr(module, class_name)
            return adapter_class()
        except ImportError:
            raise ImportError(f"Adapter for {framework} not found")
    
    @classmethod
    def auto_configure(cls, project_path: str, environment: str = 'local'):
        """
        Automatically configure agent based on project structure
        
        Args:
            project_path: Path to project directory
            environment: Target environment ('local', 'staging', 'production')
        """
        framework = cls._detect_framework(project_path)
        config = cls._load_project_config(project_path, environment)
        
        return cls(framework, config['base_url'], config['logs'], **config)
    
    @staticmethod
    def _detect_framework(project_path: str) -> str:
        """Detect framework from project structure"""
        path = Path(project_path)
        
        # Framework detection patterns
        patterns = {
            'react': ['package.json', 'src/App.jsx', 'next.config.js'],
            'mod_perl': ['*.comp', '*.smpl', '~openSAS/'],
            'php': ['composer.json', 'artisan', 'app/Http/'],
            'django': ['manage.py', 'settings.py', 'wsgi.py'],
            'vue': ['vue.config.js', 'src/main.js', 'nuxt.config.js']
        }
        
        for framework, indicators in patterns.items():
            if cls._check_patterns(path, indicators):
                return framework
                
        return 'generic'
    
    async def test(
        self,
        component_name: str,
        test_params: Optional[Dict] = None,
        workflows: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Test a specific component with optional workflows
        
        Args:
            component_name: Name of component to test
            test_params: Parameters for the test (e.g., {'orderid': '123'})
            workflows: List of workflows to execute (e.g., ['load', 'interact'])
            
        Returns:
            Test results with browser events, server logs, and correlations
        """
        self.logger.info(f"Starting test for {component_name} with {self.framework}")
        
        # Load test definition
        test_definition = self.adapter.get_test_definition(component_name)
        
        # Start log monitoring
        await self.log_monitor.start_monitoring()
        
        # Initialize browser
        await self.browser_engine.initialize()
        
        try:
            # Execute test workflows
            test_results = await self._execute_test_workflows(
                test_definition, test_params, workflows
            )
            
            # Stop monitoring and get logs
            server_logs = await self.log_monitor.stop_monitoring()
            
            # Correlate browser events with server logs
            correlations = self.error_correlator.correlate_events(
                test_results['browser_events'],
                server_logs
            )
            
            # Generate comprehensive results
            results = {
                'framework': self.framework,
                'component': component_name,
                'test_params': test_params,
                'browser_results': test_results,
                'server_logs': server_logs,
                'correlations': correlations,
                'success': len(correlations.get('errors', [])) == 0,
                'timestamp': asyncio.get_event_loop().time()
            }
            
            self.test_results.append(results)
            return results
            
        finally:
            await self.browser_engine.cleanup()
    
    async def _execute_test_workflows(
        self,
        test_definition: Dict,
        test_params: Optional[Dict],
        workflows: Optional[List[str]]
    ) -> Dict:
        """Execute specified test workflows"""
        
        # Build test URL
        test_url = self.adapter.build_url(self.base_url, test_definition, test_params)
        
        # Navigate to component
        await self.browser_engine.navigate(test_url)
        
        # Execute workflows
        workflow_results = {}
        workflows = workflows or ['smoke_test']
        
        for workflow_name in workflows:
            if workflow_name in test_definition.get('workflows', {}):
                workflow_def = test_definition['workflows'][workflow_name]
                result = await self.browser_engine.execute_workflow(workflow_def)
                workflow_results[workflow_name] = result
            else:
                self.logger.warning(f"Workflow {workflow_name} not found in test definition")
        
        return {
            'url': test_url,
            'workflows': workflow_results,
            'browser_events': self.browser_engine.get_events(),
            'performance_metrics': await self.browser_engine.get_performance_metrics(),
            'console_errors': await self.browser_engine.get_console_errors(),
            'network_requests': self.browser_engine.get_network_requests()
        }
    
    def generate_report(self, results: Optional[Dict] = None) -> str:
        """Generate Cursor-friendly test report"""
        
        if results is None:
            results = self.test_results[-1] if self.test_results else {}
            
        return self.report_generator.create_markdown_report(results)
    
    def open_results_in_cursor(self, results: Optional[Dict] = None):
        """Open test results in Cursor IDE"""
        
        report_path = self.report_generator.save_report(results or self.test_results[-1])
        
        # Open in Cursor
        import subprocess
        subprocess.run(['cursor', report_path])
        
        # Also open any files with errors
        if results and 'correlations' in results:
            for error in results['correlations'].get('errors', []):
                if 'file_path' in error and 'line_number' in error:
                    file_with_line = f"{error['file_path']}:{error['line_number']}"
                    subprocess.run(['cursor', file_with_line])
    
    async def run_smoke_tests(self, components: Optional[List[str]] = None) -> Dict:
        """Run smoke tests for specified components or all available"""
        
        if components is None:
            components = self.adapter.get_available_components()
            
        results = {}
        for component in components:
            try:
                result = await self.test(component, workflows=['smoke_test'])
                results[component] = result
            except Exception as e:
                results[component] = {'error': str(e), 'success': False}
                
        return results
    
    async def continuous_monitoring(self, component_name: str, interval: int = 60):
        """Continuously monitor component health"""
        
        while True:
            try:
                result = await self.test(component_name, workflows=['health_check'])
                
                if not result['success']:
                    # Alert on failures
                    await self._send_alert(component_name, result)
                    
                await asyncio.sleep(interval)
                
            except KeyboardInterrupt:
                self.logger.info("Continuous monitoring stopped")
                break
            except Exception as e:
                self.logger.error(f"Monitoring error: {e}")
                await asyncio.sleep(interval)
