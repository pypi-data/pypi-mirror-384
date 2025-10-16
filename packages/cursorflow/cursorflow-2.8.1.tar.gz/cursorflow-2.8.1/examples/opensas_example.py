"""
OpenSAS/Mod_Perl Testing Example

This example shows how to test OpenSAS components like the message console
with real-time server log monitoring and intelligent error correlation.
"""

import asyncio
import json
from cursorflow import TestAgent

async def test_opensas_message_console():
    """Complete example of testing OpenSAS message console"""
    
    print("🚀 Testing OpenSAS Message Console with Universal Testing Agent")
    
    # Configuration for OpenSAS staging environment
    opensas_config = {
        'ssh_config': {
            'hostname': 'staging.resumeblossom.com',
            'username': 'deploy',
            'key_filename': '~/.ssh/staging_key'
        },
        'log_paths': {
            'apache_error': '/var/log/httpd/error_log',
            'apache_access': '/var/log/httpd/access_log',
            'app_debug': '/tmp/opensas_debug.log'
        }
    }
    
    # Initialize universal test agent for mod_perl
    agent = TestAgent(
        framework='mod_perl',
        base_url='https://staging.resumeblossom.com',
        logs='ssh',
        **opensas_config
    )
    
    # Test scenarios
    test_scenarios = [
        {
            'name': 'Valid Order Load',
            'params': {'orderid': '6590532419829'},
            'workflows': ['smoke_test', 'ajax_test']
        },
        {
            'name': 'Invalid Order Error',
            'params': {'orderid': 'invalid123'},
            'workflows': ['smoke_test'],
            'expect_error': True
        },
        {
            'name': 'Modal Workflows',
            'params': {'orderid': '6590532419829'},
            'workflows': ['modal_test']
        }
    ]
    
    all_results = {}
    
    for scenario in test_scenarios:
        print(f"\n📋 Running scenario: {scenario['name']}")
        
        try:
            results = await agent.test(
                'message-console',
                test_params=scenario['params'],
                workflows=scenario['workflows']
            )
            
            all_results[scenario['name']] = results
            
            # Quick result check
            if results['success']:
                print(f"  ✅ {scenario['name']} - PASSED")
            else:
                print(f"  ❌ {scenario['name']} - FAILED")
                
                # Show critical issues
                critical = results.get('correlations', {}).get('critical_issues', [])
                if critical:
                    print(f"     🚨 {len(critical)} critical issues found")
            
        except Exception as e:
            print(f"  💥 {scenario['name']} - ERROR: {e}")
            all_results[scenario['name']] = {'error': str(e), 'success': False}
    
    # Generate comprehensive report
    print("\n📊 Generating comprehensive report...")
    report_path = agent.report_generator.save_report(all_results)
    print(f"Report saved to: {report_path}")
    
    # Open results in Cursor
    try:
        agent.open_results_in_cursor(all_results)
        print("🎯 Results opened in Cursor!")
    except:
        print("⚠️  Could not open in Cursor (install Cursor CLI)")
    
    return all_results

async def test_opensas_business_dashboard():
    """Example of testing business dashboard component"""
    
    agent = TestAgent(
        framework='mod_perl',
        base_url='https://staging.resumeblossom.com',
        logs='ssh',
        ssh_config={
            'hostname': 'staging.resumeblossom.com',
            'username': 'deploy'
        },
        log_paths={
            'apache_error': '/var/log/httpd/error_log'
        }
    )
    
    # Test dashboard with date range parameters
    results = await agent.test('business-dashboard', {
        'date_start': '2025-01-01',
        'date_end': '2025-01-31',
        'group_by': 'day'
    })
    
    return results

async def continuous_monitoring_example():
    """Example of continuous component monitoring"""
    
    agent = TestAgent('mod_perl', 'https://app.resumeblossom.com', logs='ssh')
    
    # Monitor critical component every 5 minutes
    print("🔄 Starting continuous monitoring...")
    await agent.continuous_monitoring('message-console', interval=300)

if __name__ == '__main__':
    # Run the main example
    results = asyncio.run(test_opensas_message_console())
    
    # Print summary
    print(f"\n🎯 Test Summary:")
    for scenario_name, result in results.items():
        status = "✅ PASS" if result.get('success', False) else "❌ FAIL"
        print(f"  {scenario_name}: {status}")
