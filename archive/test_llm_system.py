#!/usr/bin/env python3
"""
Comprehensive test of the LLM Auto-Configuration System.

Demonstrates Phase 6: Smart Auto-Configuration with LLM
"""

import os
from pathlib import Path
from introspector_v2 import UniversalIntrospector
from plugin_system import get_plugin_manager
from llm_auto_configurator import LLMAutoConfigurator, auto_configure_sdk

def test_llm_auto_configuration():
    """Comprehensive test of LLM auto-configuration capabilities."""
    print("🤖 LLM Auto-Configuration System Test")
    print("=" * 60)
    
    # Test modules (built-in modules that won't have existing plugins)
    test_modules = [
        ('hashlib', 'hashlib'),
        ('base64', 'base64'), 
        ('datetime', 'datetime'),
        ('pathlib', 'pathlib')
    ]
    
    print(f"\n📦 Testing {len(test_modules)} unknown SDKs with LLM auto-configuration:")
    
    configurator = LLMAutoConfigurator()
    results = []
    
    for sdk_name, module_name in test_modules:
        print(f"\n🔍 Testing: {sdk_name}")
        print("-" * 40)
        
        try:
            # Run introspection with LLM auto-config
            introspector = UniversalIntrospector(sdk_name)
            methods = introspector.discover_from_module(module_name)
            
            result = {
                'sdk': sdk_name,
                'methods_discovered': len(methods),
                'auto_config_enabled': introspector.enable_auto_config,
                'plugin_generated': False,
                'confidence': 0.0
            }
            
            # Check if plugin was generated
            plugin_file = Path(f"plugins/{sdk_name}_auto.yaml")
            if plugin_file.exists():
                result['plugin_generated'] = True
                
                # Read confidence from generated plugin
                import yaml
                with open(plugin_file) as f:
                    plugin_data = yaml.safe_load(f)
                    result['confidence'] = plugin_data.get('metadata', {}).get('confidence', 0.0)
                
                print(f"   ✅ Plugin generated: {plugin_file}")
                print(f"   📊 Methods discovered: {len(methods)}")
                print(f"   🎯 LLM confidence: {result['confidence']:.2f}")
                
                # Show key insights
                if 'hints' in plugin_data and 'prioritize_methods' in plugin_data['hints']:
                    priority_methods = plugin_data['hints']['prioritize_methods'][:3]
                    print(f"   🔑 Priority methods: {', '.join(priority_methods)}")
            else:
                print(f"   ❌ No plugin generated (low confidence or error)")
            
            results.append(result)
            
        except Exception as e:
            print(f"   💥 Error testing {sdk_name}: {e}")
            results.append({
                'sdk': sdk_name,
                'error': str(e)
            })
    
    # Summary
    print(f"\n📈 LLM Auto-Configuration Results Summary:")
    print("=" * 60)
    
    successful = [r for r in results if r.get('plugin_generated')]
    failed = [r for r in results if 'error' in r]
    low_confidence = [r for r in results if not r.get('plugin_generated') and 'error' not in r]
    
    print(f"✅ Successful auto-configurations: {len(successful)}")
    print(f"❌ Failed attempts: {len(failed)}")  
    print(f"⚠️  Low confidence (skipped): {len(low_confidence)}")
    
    if successful:
        avg_confidence = sum(r['confidence'] for r in successful) / len(successful)
        print(f"📊 Average LLM confidence: {avg_confidence:.2f}")
        
        print(f"\n🎯 Generated Plugins:")
        for result in successful:
            print(f"   • {result['sdk']}: {result['methods_discovered']} methods, "
                  f"confidence {result['confidence']:.2f}")
    
    # Show plugin directory
    plugins_dir = Path("plugins")
    auto_plugins = list(plugins_dir.glob("*_auto.yaml"))
    print(f"\n📁 Auto-generated plugin files ({len(auto_plugins)}):")
    for plugin_file in auto_plugins:
        print(f"   • {plugin_file}")
    
    print(f"\n✅ LLM Auto-Configuration System test complete!")
    return results

def demo_llm_vs_manual():
    """Demo comparing LLM auto-config vs manual configuration."""
    print(f"\n🆚 LLM Auto-Config vs Manual Config Comparison")
    print("=" * 60)
    
    pm = get_plugin_manager()
    
    # Manual plugins
    manual_plugins = [name for name in pm.plugins.keys() if not name.endswith('_auto')]
    auto_plugins = [name for name in pm.plugins.keys() if name.endswith('_auto')]
    
    print(f"👤 Manual plugins: {len(manual_plugins)} ({', '.join(manual_plugins)})")
    print(f"🤖 LLM auto-generated: {len(auto_plugins)} ({', '.join([p.replace('_auto', '') for p in auto_plugins])})")
    
    print(f"\n💡 Key Benefits of LLM Auto-Configuration:")
    print(f"   • ⚡ Instant configuration for unknown SDKs")
    print(f"   • 🎯 Smart method prioritization based on analysis")
    print(f"   • 🔍 Automatic auth pattern detection")
    print(f"   • 📚 Contextual documentation URLs")
    print(f"   • 🔄 Self-improving as LLM models get better")

if __name__ == "__main__":
    # Ensure we have OpenAI API key
    if not os.getenv('OPENAI_API_KEY'):
        print("❌ OPENAI_API_KEY not found in environment")
        print("Please set your OpenAI API key in .env file")
        exit(1)
    
    # Run comprehensive test
    test_results = test_llm_auto_configuration()
    
    # Demo comparison
    demo_llm_vs_manual()
    
    print(f"\n🎉 Phase 6: Smart Auto-Configuration with LLM - COMPLETE! 🎉")