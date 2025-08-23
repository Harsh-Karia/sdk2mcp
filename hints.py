#!/usr/bin/env python3
"""
SDK Hints Loader - Provides optional configuration for SDK-specific optimizations
while keeping the core introspector fully generic.
"""

import re
import yaml
from pathlib import Path
from typing import Dict, List, Any, Optional, Pattern

DEFAULTS = {
    "root_prefixes": [],
    "exclude_name_patterns": [],
    "boost_owner_patterns": [],
    "penalize_owner_patterns": [],
    "boost_method_patterns": [],
    "penalize_method_patterns": [],
    "sentinel_defaults": [],
    "important_class_patterns": [],
    "destructive_verbs": ["create", "update", "replace", "patch", "delete"],
    "anchored_verbs": ["list", "get", "search", "create", "update", "replace", "patch", "delete"],
    "drop_container_methods": True,
    "prefer_public_over_private": True,
    "priority_limits": {
        "p1_all": True,
        "p2_limit": 500,
        "p3_limit": 100,
        "p4_limit": 50,
        "p5_limit": 20
    }
}

def _compile_pattern_list(patterns: List[str]) -> List[Pattern]:
    """Compile a list of string patterns into regex objects."""
    return [re.compile(p, re.IGNORECASE) for p in (patterns or [])]

def load_hints(path: str = "sdk_hints.yaml") -> Dict[str, Any]:
    """
    Load SDK hints from YAML configuration file.
    
    Returns:
        Dictionary mapping SDK names to their hint configurations
    """
    if not Path(path).exists():
        # Return empty hints if file doesn't exist - the system still works
        return {}
    
    data = yaml.safe_load(Path(path).read_text()) or {}
    defaults = {**DEFAULTS, **(data.get("defaults") or {})}
    output = {}
    
    for sdk_name, config in (data.get("sdks") or {}).items():
        # Merge with defaults
        merged = {**defaults, **(config or {})}
        
        # Compile regex patterns
        merged["exclude_name_patterns"] = _compile_pattern_list(
            merged.get("exclude_name_patterns")
        )
        merged["boost_owner_patterns"] = _compile_pattern_list(
            merged.get("boost_owner_patterns")
        )
        merged["penalize_owner_patterns"] = _compile_pattern_list(
            merged.get("penalize_owner_patterns")
        )
        merged["boost_method_patterns"] = _compile_pattern_list(
            merged.get("boost_method_patterns")
        )
        merged["penalize_method_patterns"] = _compile_pattern_list(
            merged.get("penalize_method_patterns")
        )
        merged["important_class_patterns"] = _compile_pattern_list(
            merged.get("important_class_patterns")
        )
        
        output[sdk_name] = merged
    
    # Also store defaults for SDKs not explicitly configured
    defaults["exclude_name_patterns"] = _compile_pattern_list(
        defaults.get("exclude_name_patterns")
    )
    defaults["boost_owner_patterns"] = _compile_pattern_list(
        defaults.get("boost_owner_patterns")
    )
    defaults["penalize_owner_patterns"] = _compile_pattern_list(
        defaults.get("penalize_owner_patterns")
    )
    defaults["boost_method_patterns"] = _compile_pattern_list(
        defaults.get("boost_method_patterns")
    )
    defaults["penalize_method_patterns"] = _compile_pattern_list(
        defaults.get("penalize_method_patterns")
    )
    defaults["important_class_patterns"] = _compile_pattern_list(
        defaults.get("important_class_patterns")
    )
    
    output["_defaults"] = defaults
    
    return output

def get_sdk_hints(sdk_name: str, all_hints: Optional[Dict] = None) -> Dict[str, Any]:
    """
    Get hints for a specific SDK, falling back to defaults if not configured.
    
    Args:
        sdk_name: Name of the SDK (e.g., 'github', 'kubernetes')
        all_hints: Pre-loaded hints dictionary (optional)
    
    Returns:
        Hint configuration for the SDK
    """
    if all_hints is None:
        all_hints = load_hints()
    
    # Try exact match first
    if sdk_name in all_hints:
        return all_hints[sdk_name]
    
    # Try with underscores replaced by hyphens
    normalized = sdk_name.replace('_', '-')
    if normalized in all_hints:
        return all_hints[normalized]
    
    # Fall back to defaults
    return all_hints.get("_defaults", DEFAULTS)