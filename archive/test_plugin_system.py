#!/usr/bin/env python3
"""
Test the plugin system with configured SDKs.
"""

from plugin_system import get_plugin_manager
from mcp_execution_bridge import MCPExecutionBridge
from introspector_v2 import UniversalIntrospector

def test_plugin_system():
    """Test the plugin system functionality."""
    print("🔌 Testing Plugin System")
    print("=" * 50)
    
    # Initialize plugin manager
    pm = get_plugin_manager()
    print(f"✅ Loaded {len(pm.plugins)} plugins: {list(pm.plugins.keys())}")
    
    # Test each configured plugin
    for plugin_name in pm.plugins.keys():
        print(f"\n🧪 Testing {plugin_name} plugin:")
        
        # Get plugin info
        plugin = pm.get_plugin(plugin_name)
        print(f"   SDK Module: {plugin.sdk_module}")
        
        # Test auth info
        auth_info = pm.get_auth_info(plugin_name)
        if auth_info:
            print(f"   Auth Type: {auth_info['type']}")
            if 'env_vars' in auth_info:
                print(f"   Env Vars: {auth_info['env_vars']}")
        
        # Test hints
        hints = pm.get_hints(plugin_name)
        if hints:
            print(f"   Hints: {len(hints)} configuration keys")
            if 'prioritize_methods' in hints:
                print(f"   Priority Methods: {hints['prioritize_methods'][:3]}...")
    
    # Test introspector with plugin hints
    print(f"\n🔍 Testing Introspector Plugin Integration:")
    introspector_with_hints = UniversalIntrospector('github')
    introspector_without_hints = UniversalIntrospector()
    
    print(f"   With GitHub plugin: {len(introspector_with_hints.hints)} hint keys")
    print(f"   Without plugin: {len(introspector_without_hints.hints)} hint keys")
    
    # Test execution bridge
    print(f"\n⚡ Testing Execution Bridge Plugin Integration:")
    bridge = MCPExecutionBridge('github', 'github')
    print(f"   Bridge initialized for {bridge.sdk_name}")
    print(f"   Plugin manager accessible: {len(bridge.plugin_manager.plugins)} plugins")
    
    print(f"\n✅ Plugin system test complete!")

if __name__ == "__main__":
    test_plugin_system()