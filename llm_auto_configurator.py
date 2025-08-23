#!/usr/bin/env python3
"""
LLM Auto-Configuration System for SDK Analysis

Uses OpenAI to automatically analyze unknown SDKs and generate optimal
plugin configurations for better MCP tool generation.
"""

import os
import json
import yaml
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from pathlib import Path
import openai
from dotenv import load_dotenv
from plugin_system import SDKPlugin, AuthConfig, ClientConfig, get_plugin_manager
from introspector_v2 import MethodInfo

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

@dataclass
class SDKAnalysis:
    """Results of LLM analysis of an SDK."""
    sdk_name: str
    sdk_module: str
    confidence: float
    
    # Authentication analysis
    likely_auth_type: Optional[str] = None
    auth_env_vars: List[str] = None
    auth_patterns: List[str] = None
    
    # Class analysis
    important_classes: List[str] = None
    client_classes: List[str] = None
    api_classes: List[str] = None
    
    # Method analysis
    crud_patterns: List[str] = None
    priority_methods: List[str] = None
    destructive_patterns: List[str] = None
    
    # General insights
    sdk_purpose: str = None
    documentation_url: str = None
    recommended_limits: Dict[str, int] = None

class LLMAutoConfigurator:
    """
    LLM-powered auto-configuration for unknown SDKs.
    """
    
    def __init__(self, openai_api_key: Optional[str] = None):
        """Initialize with OpenAI API key."""
        self.api_key = openai_api_key or os.getenv('OPENAI_API_KEY')
        if not self.api_key:
            raise ValueError("OpenAI API key not found. Set OPENAI_API_KEY environment variable.")
        
        # Initialize OpenAI client
        openai.api_key = self.api_key
        self.client = openai.OpenAI(api_key=self.api_key)
        
        self.plugin_manager = get_plugin_manager()
    
    def analyze_sdk(self, sdk_name: str, methods: List[MethodInfo]) -> SDKAnalysis:
        """
        Use LLM to analyze an SDK and generate configuration insights.
        
        Args:
            sdk_name: Name of the SDK
            methods: List of discovered methods from introspection
            
        Returns:
            SDKAnalysis with LLM insights
        """
        logger.info(f"🤖 Starting LLM analysis of {sdk_name} SDK...")
        
        # Prepare data for LLM analysis
        analysis_data = self._prepare_analysis_data(sdk_name, methods)
        
        # Get LLM insights
        analysis = self._query_llm_for_analysis(sdk_name, analysis_data)
        
        logger.info(f"✅ LLM analysis complete. Confidence: {analysis.confidence:.2f}")
        return analysis
    
    def generate_plugin_config(self, analysis: SDKAnalysis) -> SDKPlugin:
        """
        Generate a plugin configuration based on LLM analysis.
        
        Args:
            analysis: Results from LLM SDK analysis
            
        Returns:
            Generated SDKPlugin configuration
        """
        logger.info(f"🔧 Generating plugin config for {analysis.sdk_name}...")
        
        # Create auth configuration
        auth_config = None
        if analysis.likely_auth_type:
            auth_config = AuthConfig(
                type=analysis.likely_auth_type,
                env_vars=analysis.auth_env_vars or [],
                fallback="anonymous",
                required=False
            )
        
        # Create client configuration
        client_config = None
        if analysis.client_classes:
            # Pick the most likely client class
            main_client = analysis.client_classes[0]
            client_config = ClientConfig(
                class_path=f"{analysis.sdk_module}.{main_client}",
                init_params=self._generate_init_params(analysis),
                setup_methods=[]
            )
        
        # Create hints
        hints = {
            "important_classes": analysis.important_classes or [],
            "prioritize_methods": analysis.priority_methods or [],
            "boost_patterns": analysis.crud_patterns or [],
            "exclude_patterns": ["^_", "__.*__"],
        }
        
        if analysis.destructive_patterns:
            hints["penalize_method_patterns"] = analysis.destructive_patterns
        
        if analysis.recommended_limits:
            hints["priority_limits"] = analysis.recommended_limits
        
        # Create plugin
        plugin = SDKPlugin(
            name=analysis.sdk_name,
            sdk_module=analysis.sdk_module,
            auth=auth_config,
            client=client_config,
            hints=hints,
            metadata={
                "description": analysis.sdk_purpose or f"{analysis.sdk_name} SDK",
                "homepage": analysis.documentation_url or "",
                "auto_generated": True,
                "confidence": analysis.confidence,
                "generated_by": "LLM Auto-Configurator"
            }
        )
        
        return plugin
    
    def save_generated_plugin(self, plugin: SDKPlugin) -> Path:
        """
        Save the generated plugin configuration to the plugins directory.
        
        Args:
            plugin: Generated plugin configuration
            
        Returns:
            Path to the saved plugin file
        """
        plugins_dir = Path("plugins")
        plugins_dir.mkdir(exist_ok=True)
        
        plugin_file = plugins_dir / f"{plugin.name}_auto.yaml"
        
        # Convert to dictionary for YAML serialization
        plugin_dict = {
            "name": plugin.name,
            "sdk_module": plugin.sdk_module,
            "metadata": plugin.metadata
        }
        
        if plugin.auth:
            plugin_dict["auth"] = {
                "type": plugin.auth.type,
                "env_vars": plugin.auth.env_vars,
                "fallback": plugin.auth.fallback,
                "required": plugin.auth.required
            }
            if plugin.auth.config_files:
                plugin_dict["auth"]["config_files"] = plugin.auth.config_files
        
        if plugin.client:
            plugin_dict["client"] = {
                "class_path": plugin.client.class_path,
                "init_params": plugin.client.init_params,
                "setup_methods": plugin.client.setup_methods
            }
        
        if plugin.hints:
            plugin_dict["hints"] = plugin.hints
        
        # Save to YAML file
        with open(plugin_file, 'w') as f:
            yaml.dump(plugin_dict, f, indent=2, default_flow_style=False)
        
        logger.info(f"💾 Saved auto-generated plugin: {plugin_file}")
        return plugin_file
    
    def _prepare_analysis_data(self, sdk_name: str, methods: List[MethodInfo]) -> Dict[str, Any]:
        """Prepare data for LLM analysis."""
        # Group methods by class
        class_methods = {}
        for method in methods[:100]:  # Limit to first 100 methods for LLM
            class_name = method.parent_class or "module_level"
            if class_name not in class_methods:
                class_methods[class_name] = []
            class_methods[class_name].append(method.name)
        
        # Get method names and patterns
        method_names = [m.name for m in methods[:50]]  # First 50 method names
        class_names = list(class_methods.keys())
        
        return {
            "sdk_name": sdk_name,
            "total_methods": len(methods),
            "sample_methods": method_names,
            "classes": class_names,
            "class_methods": dict(list(class_methods.items())[:10])  # Top 10 classes
        }
    
    def _query_llm_for_analysis(self, sdk_name: str, data: Dict[str, Any]) -> SDKAnalysis:
        """Query OpenAI for SDK analysis."""
        
        prompt = f"""Analyze this Python SDK and provide configuration insights:

SDK Name: {sdk_name}
Total Methods: {data['total_methods']}
Sample Method Names: {', '.join(data['sample_methods'][:20])}
Classes Found: {', '.join(data['classes'][:10])}

Based on this SDK structure, please provide:

1. Authentication Analysis:
   - What type of authentication does this SDK likely use? (token, oauth, api_key, credentials, none)
   - What environment variable names would typically store auth info?

2. Class Analysis:
   - Which classes are most important for users?
   - Which classes are likely client/API classes?

3. Method Analysis:
   - What are the most important methods users would want?
   - What patterns indicate CRUD operations?
   - What patterns indicate destructive operations?

4. SDK Purpose:
   - What is this SDK used for?
   - What's the likely documentation URL?

Respond with a JSON object matching this structure:
{{
  "confidence": 0.0-1.0,
  "likely_auth_type": "token|oauth|api_key|credentials|none",
  "auth_env_vars": ["ENV_VAR1", "ENV_VAR2"],
  "important_classes": ["Class1", "Class2"],
  "client_classes": ["ClientClass"],
  "priority_methods": ["method1", "method2"],
  "crud_patterns": ["^(get|list|create|update|delete)_", "^(fetch|add|remove)_"],
  "destructive_patterns": ["^(delete|remove|destroy)_"],
  "sdk_purpose": "Brief description",
  "documentation_url": "https://...",
  "recommended_limits": {{"p2_limit": 100}}
}}

Only include fields you're confident about. Use null for uncertain values."""
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are an expert Python SDK analyst. Analyze SDK structures and provide JSON configuration insights."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=1000
            )
            
            # Parse JSON response
            content = response.choices[0].message.content.strip()
            
            # Extract JSON from response (in case there's extra text)
            json_start = content.find('{')
            json_end = content.rfind('}') + 1
            if json_start >= 0 and json_end > json_start:
                json_content = content[json_start:json_end]
                llm_data = json.loads(json_content)
            else:
                raise ValueError("No valid JSON found in LLM response")
            
            # Convert to SDKAnalysis
            analysis = SDKAnalysis(
                sdk_name=sdk_name,
                sdk_module=sdk_name,
                confidence=llm_data.get("confidence", 0.5),
                likely_auth_type=llm_data.get("likely_auth_type"),
                auth_env_vars=llm_data.get("auth_env_vars", []),
                important_classes=llm_data.get("important_classes", []),
                client_classes=llm_data.get("client_classes", []),
                priority_methods=llm_data.get("priority_methods", []),
                crud_patterns=llm_data.get("crud_patterns", []),
                destructive_patterns=llm_data.get("destructive_patterns", []),
                sdk_purpose=llm_data.get("sdk_purpose"),
                documentation_url=llm_data.get("documentation_url"),
                recommended_limits=llm_data.get("recommended_limits", {"p2_limit": 100})
            )
            
            return analysis
            
        except Exception as e:
            logger.error(f"LLM analysis failed: {e}")
            # Return minimal analysis with low confidence
            return SDKAnalysis(
                sdk_name=sdk_name,
                sdk_module=sdk_name,
                confidence=0.1
            )
    
    def _generate_init_params(self, analysis: SDKAnalysis) -> Dict[str, str]:
        """Generate initialization parameters based on auth analysis."""
        if not analysis.likely_auth_type:
            return {}
        
        if analysis.likely_auth_type == "token":
            return {"auth": "${auth.value}"}
        elif analysis.likely_auth_type == "api_key":
            return {"api_key": "${auth.value}"}
        elif analysis.likely_auth_type == "credentials":
            return {"credentials": "${auth.value}"}
        else:
            return {}

def auto_configure_sdk(sdk_name: str, methods: List[MethodInfo]) -> Optional[SDKPlugin]:
    """
    Main function to auto-configure an unknown SDK using LLM.
    
    Args:
        sdk_name: Name of the SDK to configure
        methods: Discovered methods from introspection
        
    Returns:
        Generated plugin configuration or None if failed
    """
    try:
        configurator = LLMAutoConfigurator()
        analysis = configurator.analyze_sdk(sdk_name, methods)
        
        if analysis.confidence < 0.3:
            logger.warning(f"Low confidence ({analysis.confidence:.2f}) in LLM analysis, skipping auto-config")
            return None
        
        plugin = configurator.generate_plugin_config(analysis)
        configurator.save_generated_plugin(plugin)
        
        return plugin
        
    except Exception as e:
        logger.error(f"Auto-configuration failed for {sdk_name}: {e}")
        return None