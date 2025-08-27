#!/usr/bin/env python3
"""
Demo script to show full SDK discovery and scope coverage.
Usage: python demo_full_discovery.py <sdk_name>
"""

import sys
from introspector_v2 import UniversalIntrospector

def main():
    if len(sys.argv) < 2:
        print("Usage: python demo_full_discovery.py <sdk_name>")
        print("Examples:")
        print("  python demo_full_discovery.py kubernetes")
        print("  python demo_full_discovery.py requests") 
        print("  python demo_full_discovery.py github")
        sys.exit(1)
    
    sdk_name = sys.argv[1]
    
    print(f"🔍 Full SDK Discovery Demo: {sdk_name}")
    print("=" * 60)
    
    try:
        # Create introspector
        introspector = UniversalIntrospector(sdk_name)
        
        # Discover ALL methods
        print(f"📡 Discovering all methods from '{sdk_name}' module...")
        all_methods = introspector.discover_from_module(sdk_name)
        
        print(f"✅ TOTAL METHODS DISCOVERED: {len(all_methods)}")
        print()
        
        # Show filtering in action
        print("🎯 Applying intelligent prioritization...")
        filtered_methods = introspector.filter_high_value_methods(all_methods)
        
        print(f"📊 FILTERING RESULTS:")
        print(f"   • Total discovered: {len(all_methods)}")
        print(f"   • High-value methods: {len(filtered_methods)}")
        print(f"   • Noise reduction: {100 - (len(filtered_methods)/len(all_methods)*100):.1f}%")
        print()
        
        # Show priority breakdown
        priority_counts = {}
        for method in all_methods:
            score = introspector._calculate_priority_score(method)
            if score >= 8:
                tier = "Priority 1 (Essential)"
            elif score >= 5:
                tier = "Priority 2 (Important)" 
            else:
                tier = "Priority 3 (Available)"
            
            priority_counts[tier] = priority_counts.get(tier, 0) + 1
        
        print("📈 PRIORITY BREAKDOWN:")
        for tier, count in priority_counts.items():
            print(f"   • {tier}: {count} methods")
        print()
        
        # Show some examples from each tier
        print("🔍 SAMPLE METHODS BY PRIORITY:")
        
        # Priority 1 examples
        p1_methods = [m for m in all_methods if introspector._calculate_priority_score(m) >= 8]
        if p1_methods:
            print(f"\n   Priority 1 Examples (showing first 5):")
            for method in p1_methods[:5]:
                print(f"     • {method.name}: {method.full_name}")
        
        # Priority 2 examples  
        p2_methods = [m for m in all_methods if 5 <= introspector._calculate_priority_score(m) < 8]
        if p2_methods:
            print(f"\n   Priority 2 Examples (showing first 3):")
            for method in p2_methods[:3]:
                print(f"     • {method.name}: {method.full_name}")
                
        # Priority 3 examples
        p3_methods = [m for m in all_methods if introspector._calculate_priority_score(m) < 5]
        if p3_methods:
            print(f"\n   Priority 3 Examples (showing first 3):")
            for method in p3_methods[:3]:
                print(f"     • {method.name}: {method.full_name}")
        
        print()
        print("💡 KEY INSIGHT:")
        print("   Nothing is lost - we discover EVERYTHING, then intelligently prioritize!")
        print("   Users can access any tier by adjusting the max_tools parameter.")
        print()
        print("📝 USAGE EXAMPLES:")
        print(f"   # Get top 20 essentials:")
        print(f"   python universal_mcp_server.py {sdk_name} {sdk_name} 20")
        print(f"   # Get broader coverage:")
        print(f"   python universal_mcp_server.py {sdk_name} {sdk_name} 100")
        print(f"   # Get everything:")
        print(f"   python universal_mcp_server.py {sdk_name} {sdk_name} {len(all_methods)}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print(f"   Make sure '{sdk_name}' is installed: pip install {sdk_name}")

if __name__ == "__main__":
    main()