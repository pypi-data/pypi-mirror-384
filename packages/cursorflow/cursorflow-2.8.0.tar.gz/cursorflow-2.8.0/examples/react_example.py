"""
React Application Testing Example

This example shows how to test React applications with the universal testing agent.
Works with Create React App, Next.js, and other React frameworks.
"""

import asyncio
from cursorflow import TestAgent

async def test_react_user_dashboard():
    """Complete example of testing React user dashboard"""
    
    print("🚀 Testing React User Dashboard with Universal Testing Agent")
    
    # Configuration for React development environment
    react_config = {
        'log_paths': {
            'next_server': '.next/trace.log',
            'app_console': 'logs/app.log',
            'build_output': '.next/build.log'
        }
    }
    
    # Initialize universal test agent for React
    agent = TestAgent(
        framework='react',
        base_url='http://localhost:3000',
        logs='local',
        **react_config
    )
    
    # Test scenarios for React app
    test_scenarios = [
        {
            'name': 'User Authentication Flow',
            'params': {'userId': '123'},
            'workflows': ['auth_flow']
        },
        {
            'name': 'Data Loading and Refresh',
            'params': {'userId': '123'},
            'workflows': ['data_loading_test', 'data_refresh']
        },
        {
            'name': 'User Interaction Flow',
            'params': {'userId': '123'},
            'workflows': ['user_interaction_test']
        }
    ]
    
    all_results = {}
    
    for scenario in test_scenarios:
        print(f"\n📋 Running scenario: {scenario['name']}")
        
        try:
            results = await agent.test(
                'user-dashboard',
                test_params=scenario['params'],
                workflows=scenario['workflows']
            )
            
            all_results[scenario['name']] = results
            
            if results['success']:
                print(f"  ✅ {scenario['name']} - PASSED")
            else:
                print(f"  ❌ {scenario['name']} - FAILED")
                
        except Exception as e:
            print(f"  💥 {scenario['name']} - ERROR: {e}")
    
    return all_results

async def test_react_api_integration():
    """Test React app API integration"""
    
    agent = TestAgent('react', 'http://localhost:3000', logs='local')
    
    # Custom workflow for API testing
    api_workflow = [
        {'navigate': {'params': {'userId': '123'}}},
        {'wait_for': '[data-testid="dashboard-loaded"]'},
        {'click': {'selector': '[data-testid="refresh-data"]'}},
        {'wait_for': '.loading-spinner'},
        {'wait_for_condition': '!document.querySelector(".loading-spinner")'},
        {'validate': {'selector': '[data-testid="error-message"]', 'exists': False}},
        {'validate': {'api_response': {'status': 200}}},
        {'capture': 'api_integration_complete'}
    ]
    
    results = await agent.execute_workflow(api_workflow)
    return results

async def test_next_js_ssr():
    """Test Next.js server-side rendering"""
    
    agent = TestAgent('react', 'http://localhost:3000', logs='local')
    
    # Test SSR hydration
    ssr_workflow = [
        {'navigate': {'params': {}}},
        {'wait_for': '[data-reactroot]'},
        {'validate': {'react_rendered': True}},
        {'validate': {'selector': '[data-testid="hydration-error"]', 'exists': False}},
        {'capture': 'ssr_hydrated'}
    ]
    
    results = await agent.execute_workflow(ssr_workflow)
    return results

if __name__ == '__main__':
    # Run React testing examples
    print("Testing React application...")
    
    # Test user dashboard
    dashboard_results = asyncio.run(test_react_user_dashboard())
    
    # Test API integration
    api_results = asyncio.run(test_react_api_integration())
    
    # Print summary
    print(f"\n🎯 React Test Summary:")
    for scenario_name, result in dashboard_results.items():
        status = "✅ PASS" if result.get('success', False) else "❌ FAIL"
        print(f"  {scenario_name}: {status}")
