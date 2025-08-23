"""
Universal SDK Introspection Engine v2
Improved version with SDK hints support for better scoping and prioritization.
"""

import inspect
import importlib
import sys
import types
import sysconfig
import pathlib
import re
import json
from typing import Any, Dict, List, Optional, Set, Type, get_type_hints
from dataclasses import dataclass, asdict
import ast
import logging
from hints import get_sdk_hints, load_hints

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Pre-compute stdlib path for accurate detection
_STDLIB_PATH = pathlib.Path(sysconfig.get_paths()["stdlib"]).resolve()


@dataclass
class ParameterInfo:
    """Information about a function/method parameter"""
    name: str
    type_hint: Optional[str] = None
    default_value: Optional[Any] = None
    is_required: bool = True
    description: Optional[str] = None


@dataclass
class MethodInfo:
    """Information about a discovered method"""
    name: str
    full_name: str  # module.class.method
    module_path: str  # Full module path for deduplication
    parameters: List[ParameterInfo]
    return_type: Optional[str] = None
    docstring: Optional[str] = None
    is_async: bool = False
    is_static: bool = False
    is_class_method: bool = False
    parent_class: Optional[str] = None
    priority_score: float = 0.0  # For ranking


class UniversalIntrospector:
    """
    Universal SDK introspector with optional hints support.
    Works with ANY Python SDK without SDK-specific code.
    """
    
    def __init__(self, sdk_name: Optional[str] = None):
        """
        Initialize the introspector.
        
        Args:
            sdk_name: Optional SDK name for loading hints (e.g., 'github', 'kubernetes')
        """
        self.discovered_methods: List[MethodInfo] = []
        self.discovered_classes: Set[str] = set()
        self.seen_objects: Set[int] = set()
        
        # Load SDK hints if available
        self.sdk_name = sdk_name
        all_hints = load_hints() if sdk_name else {}
        self.hints = get_sdk_hints(sdk_name, all_hints) if sdk_name else {}
        
        # Get root prefixes for scoping
        self.root_prefixes = self.hints.get('root_prefixes', [])
        
        # Compile verb patterns
        self.verb_pattern = re.compile(
            r'^(' + '|'.join(self.hints.get('anchored_verbs', [
                'get', 'list', 'create', 'update', 'delete', 'patch', 
                'search', 'find', 'fetch', 'add', 'remove'
            ])) + r')',
            re.IGNORECASE
        )
    
    def discover_from_module(self, module_name: str) -> List[MethodInfo]:
        """
        Discover all methods from a module and its submodules.
        
        Args:
            module_name: Name of the module to introspect
            
        Returns:
            List of discovered methods
        """
        self.discovered_methods = []
        self.discovered_classes = set()
        self.seen_objects = set()
        
        # Set root prefixes if not explicitly configured
        if not self.root_prefixes:
            self.root_prefixes = [module_name + '.', module_name]
        
        try:
            module = importlib.import_module(module_name)
            logger.info(f"Introspecting module: {module_name}")
            
            # Discover methods from the main module
            self._discover_module_methods(module, module_name)
            
            # Discover key classes and their methods
            self._discover_key_classes(module, module_name)
            
            # For some SDKs, important classes are in submodules
            self._discover_submodules(module, module_name)
            
            # For Azure Management SDKs, discover operation groups
            self._discover_operation_groups(module, module_name)
            
            # Remove duplicates preferring public over private paths
            self._deduplicate_methods()
            
            logger.info(f"Discovered {len(self.discovered_methods)} methods")
            
        except ImportError as e:
            logger.error(f"Failed to import module {module_name}: {e}")
            
        return self.discovered_methods
    
    def _is_in_scope(self, obj: Any, module_name: str = None) -> bool:
        """
        Check if an object is within our introspection scope.
        Uses root_prefixes from hints to prevent scope bleed.
        """
        if not self.root_prefixes:
            return True  # No scoping configured
        
        # Check module of the object
        obj_module = getattr(obj, '__module__', None)
        if obj_module:
            return any(obj_module.startswith(prefix) for prefix in self.root_prefixes)
        
        # Fall back to module_name check
        if module_name:
            return any(module_name.startswith(prefix) for prefix in self.root_prefixes)
        
        return False
    
    def _should_exclude_name(self, name: str) -> bool:
        """Check if a method name should be excluded based on hints."""
        exclude_patterns = self.hints.get('exclude_name_patterns', [])
        return any(pattern.search(name) for pattern in exclude_patterns)
    
    def _is_important_class(self, class_name: str) -> bool:
        """Check if a class matches important class patterns from hints."""
        important_patterns = self.hints.get('important_class_patterns', [])
        if not important_patterns:
            # Default important patterns if no hints
            important_patterns = [
                re.compile(r'Client$', re.IGNORECASE),
                re.compile(r'Api$', re.IGNORECASE),
                re.compile(r'Operations$', re.IGNORECASE),
                re.compile(r'Service$', re.IGNORECASE)
            ]
        
        class_base = class_name.split('.')[-1] if '.' in class_name else class_name
        return any(pattern.search(class_base) for pattern in important_patterns)
    
    def _calculate_priority_score(self, method: MethodInfo) -> float:
        """
        Calculate priority score for a method based on hints.
        Higher score = higher priority.
        """
        score = 0.0
        
        # Boost for important classes
        if method.parent_class and self._is_important_class(method.parent_class):
            score += 10.0
        
        # Boost patterns from hints
        boost_patterns = self.hints.get('boost_owner_patterns', [])
        if method.parent_class:
            for pattern in boost_patterns:
                if pattern.search(method.parent_class):
                    score += 5.0
                    break
        
        # Penalize patterns from hints
        penalize_patterns = self.hints.get('penalize_owner_patterns', [])
        if method.parent_class:
            for pattern in penalize_patterns:
                if pattern.search(method.parent_class):
                    score -= 5.0
                    break
        
        # Method-level boosts/penalties
        boost_method_patterns = self.hints.get('boost_method_patterns', [])
        for pattern in boost_method_patterns:
            if pattern.search(method.name):
                score += 8.0  # Higher boost for priority methods
                break
        
        penalize_method_patterns = self.hints.get('penalize_method_patterns', [])
        for pattern in penalize_method_patterns:
            if pattern.search(method.name):
                score -= 6.0  # Strong penalty for connect_* etc.
                break
        
        # Boost for verb patterns
        if self.verb_pattern.match(method.name):
            score += 3.0
        
        # Boost for REST documentation or :calls: hints
        if method.docstring and (':calls:' in method.docstring or 
                                 any(verb in method.docstring[:100] for verb in ['GET', 'POST', 'PUT', 'DELETE'])):
            score += 5.0
        
        # Penalize private methods
        if method.name.startswith('_') and not method.name.startswith('__'):
            score -= 2.0
        
        # Strong penalty for private module paths
        if '._' in method.module_path:
            score -= 8.0
        
        return score
    
    def _discover_module_methods(self, module: types.ModuleType, module_name: str):
        """Discover methods directly in a module."""
        for name, obj in inspect.getmembers(module):
            if name.startswith('_'):
                continue
                
            if self._should_exclude_name(name):
                continue
                
            if inspect.isfunction(obj) and self._is_in_scope(obj, module_name):
                method_path = f"{module_name}.{name}"
                self._extract_method_info(obj, method_path, None, module)
    
    def _discover_key_classes(self, module: types.ModuleType, module_name: str):
        """Discover key classes and their methods with better scoping."""
        visited_classes = set()
        
        # First, find all classes in the module
        for name, obj in inspect.getmembers(module, inspect.isclass):
            if id(obj) in visited_classes:
                continue
                
            # Check if class is in scope
            if not self._is_in_scope(obj, module_name):
                continue
                
            visited_classes.add(id(obj))
            class_full_name = f"{obj.__module__}.{obj.__name__}" if hasattr(obj, '__module__') else obj.__name__
            
            # Skip if not an important class (unless we have few classes)
            if len(self.discovered_classes) > 50 and not self._is_important_class(class_full_name):
                # For large SDKs, focus on important classes
                continue
            
            self.discovered_classes.add(class_full_name)
            
            # Discover methods in this class
            for method_name, method in inspect.getmembers(obj):
                if method_name.startswith('__') and method_name != '__init__':
                    continue
                    
                if self._should_exclude_name(method_name):
                    continue
                    
                if inspect.ismethod(method) or inspect.isfunction(method):
                    method_path = f"{class_full_name}.{method_name}"
                    self._extract_method_info(method, method_path, class_full_name, module)
        
        # For SDKs with client patterns, also check for dynamically important classes
        self._discover_dynamic_important_classes(module, module_name)
    
    def _discover_submodules(self, module: types.ModuleType, module_name: str):
        """
        Discover important submodules like kubernetes.client or azure.storage.blob._blob_client.
        """
        # Common submodule patterns to check
        common_submodules = ['client', 'api', 'apis', 'operations', 'v1', 'v2']
        
        for submodule_name in common_submodules:
            try:
                full_submodule_name = f"{module_name}.{submodule_name}"
                submodule = importlib.import_module(full_submodule_name)
                
                # Discover classes in this submodule
                for name, obj in inspect.getmembers(submodule, inspect.isclass):
                    if not self._is_in_scope(obj, full_submodule_name):
                        continue
                    
                    # Check if it's an important class
                    class_full_name = f"{obj.__module__}.{obj.__name__}" if hasattr(obj, '__module__') else obj.__name__
                    
                    if self._is_important_class(class_full_name):
                        self.discovered_classes.add(class_full_name)
                        
                        # Discover methods in this class
                        for method_name, method in inspect.getmembers(obj):
                            if method_name.startswith('__') and method_name != '__init__':
                                continue
                            
                            if self._should_exclude_name(method_name):
                                continue
                            
                            if inspect.ismethod(method) or inspect.isfunction(method):
                                method_path = f"{class_full_name}.{method_name}"
                                self._extract_method_info(method, method_path, class_full_name, submodule)
                
            except ImportError:
                # Submodule doesn't exist, that's fine
                continue
    
    def _discover_dynamic_important_classes(self, module: types.ModuleType, module_name: str):
        """
        Dynamically discover important classes based on method count and patterns.
        This helps find the actual API classes without hardcoding.
        """
        class_method_counts = {}
        
        # Count public methods per class
        for name, obj in inspect.getmembers(module, inspect.isclass):
            if not self._is_in_scope(obj, module_name):
                continue
                
            public_method_count = sum(
                1 for method_name, method in inspect.getmembers(obj)
                if (not method_name.startswith('_') and 
                    (inspect.ismethod(method) or inspect.isfunction(method)))
            )
            
            if public_method_count > 10:  # Classes with many public methods are likely important
                class_full_name = f"{obj.__module__}.{obj.__name__}" if hasattr(obj, '__module__') else obj.__name__
                class_method_counts[class_full_name] = public_method_count
        
        # Add top classes by method count
        sorted_classes = sorted(class_method_counts.items(), key=lambda x: x[1], reverse=True)
        for class_name, count in sorted_classes[:20]:  # Top 20 classes
            if class_name not in self.discovered_classes:
                self.discovered_classes.add(class_name)
                # Re-discover this class's methods
                parts = class_name.rsplit('.', 1)
                if len(parts) == 2:
                    try:
                        parent_module = importlib.import_module(parts[0])
                        cls = getattr(parent_module, parts[1], None)
                        if cls:
                            for method_name, method in inspect.getmembers(cls):
                                if method_name.startswith('__') and method_name != '__init__':
                                    continue
                                if self._should_exclude_name(method_name):
                                    continue
                                if inspect.ismethod(method) or inspect.isfunction(method):
                                    method_path = f"{class_name}.{method_name}"
                                    self._extract_method_info(method, method_path, class_name, parent_module)
                    except Exception:
                        pass
    
    def _discover_operation_groups(self, module: types.ModuleType, module_name: str):
        """
        Discover Azure-style operation groups (resource_groups, deployments, etc.)
        This is a generic pattern that works with any management SDK.
        """
        if 'azure' not in module_name or 'mgmt' not in module_name:
            return  # Only apply to Azure management SDKs
        
        # Look for client classes that might have operation group attributes
        for name, obj in inspect.getmembers(module, inspect.isclass):
            if 'Client' in name and self._is_in_scope(obj, module_name):
                try:
                    # Try to instantiate or inspect the class for operation groups
                    # Look for attributes that are likely operation groups
                    for attr_name in dir(obj):
                        if (not attr_name.startswith('_') and 
                            attr_name != 'models' and 
                            attr_name not in ['close', 'send_request']):
                            
                            # Check if this could be an operation group
                            attr_obj = getattr(obj, attr_name, None)
                            if (hasattr(attr_obj, '__class__') and 
                                'operations' in str(attr_obj.__class__).lower()):
                                
                                # This looks like an operation group
                                operations_class = attr_obj.__class__
                                class_full_name = f"{operations_class.__module__}.{operations_class.__name__}"
                                
                                if self._is_in_scope(operations_class, module_name):
                                    self.discovered_classes.add(class_full_name)
                                    
                                    # Discover methods in this operations class
                                    for method_name, method in inspect.getmembers(operations_class):
                                        if (not method_name.startswith('_') and 
                                            (inspect.ismethod(method) or inspect.isfunction(method))):
                                            
                                            if self._should_exclude_name(method_name):
                                                continue
                                            
                                            method_path = f"{class_full_name}.{method_name}"
                                            self._extract_method_info(method, method_path, class_full_name, module)
                                            
                except (AttributeError, TypeError):
                    # Can't inspect this class, that's OK
                    continue
    
    def _extract_method_info(self, method: Any, method_path: str, 
                           parent_class: Optional[str], module: Optional[types.ModuleType]):
        """Extract detailed information about a method."""
        if id(method) in self.seen_objects:
            return
            
        self.seen_objects.add(id(method))
        
        try:
            # Get signature
            sig = inspect.signature(method)
            parameters = []
            
            for param_name, param in sig.parameters.items():
                if param_name == 'self' or param_name == 'cls':
                    continue
                    
                param_info = ParameterInfo(
                    name=param_name,
                    type_hint=self._get_type_hint_str(param.annotation),
                    default_value=self._serialize_default(param.default),
                    is_required=(param.default == inspect.Parameter.empty)
                )
                parameters.append(param_info)
            
            # Get return type
            return_type = self._get_type_hint_str(sig.return_annotation)
            
            # Get docstring
            docstring = inspect.getdoc(method)
            
            # Check if async
            is_async = inspect.iscoroutinefunction(method)
            
            # Check if static/classmethod
            is_static = isinstance(inspect.getattr_static(
                parent_class if parent_class else module, 
                method_path.split('.')[-1], 
                None
            ), staticmethod) if parent_class or module else False
            
            is_class_method = isinstance(inspect.getattr_static(
                parent_class if parent_class else module,
                method_path.split('.')[-1],
                None
            ), classmethod) if parent_class or module else False
            
            # Get module path for deduplication
            module_path = getattr(method, '__module__', '') or ''
            
            # Create method info with public path preference
            final_parent_class = parent_class or (module.__name__ if module else 'unknown')
            
            # Try to use public path for parent_class if available
            if parent_class and '._' in parent_class:
                # Try to find a public equivalent
                public_parent = self._get_public_class_path(parent_class)
                if public_parent:
                    final_parent_class = public_parent
                    # Update method path too
                    method_name = method_path.split('.')[-1]
                    method_path = f"{public_parent}.{method_name}"
            
            method_info = MethodInfo(
                name=method_path.split('.')[-1],
                full_name=method_path,
                module_path=module_path,
                parameters=parameters,
                return_type=return_type,
                docstring=docstring,
                is_async=is_async,
                is_static=is_static,
                is_class_method=is_class_method,
                parent_class=final_parent_class
            )
            
            # Calculate priority score
            method_info.priority_score = self._calculate_priority_score(method_info)
            
            self.discovered_methods.append(method_info)
            logger.debug(f"Discovered method: {method_path} (score: {method_info.priority_score})")
            
        except Exception as e:
            logger.debug(f"Could not extract method info for {method_path}: {e}")
    
    def _deduplicate_methods(self):
        """
        Remove duplicate methods, preferring public over private module paths.
        E.g., prefer azure.storage.blob.BlobClient over azure.storage.blob._blob_client.BlobClient
        """
        if not self.hints.get('prefer_public_over_private', True):
            return
        
        # Group methods by (class, method_name, parameters)
        method_groups = {}
        for method in self.discovered_methods:
            # Create a key for grouping
            param_sig = tuple((p.name, p.type_hint) for p in method.parameters)
            key = (method.parent_class, method.name, param_sig)
            
            if key not in method_groups:
                method_groups[key] = []
            method_groups[key].append(method)
        
        # Select best method from each group
        deduplicated = []
        for methods in method_groups.values():
            if len(methods) == 1:
                deduplicated.append(methods[0])
            else:
                # Prefer public paths (no underscore in module path)
                public_methods = [m for m in methods if '._' not in m.module_path]
                if public_methods:
                    # Among public, choose highest priority score
                    best = max(public_methods, key=lambda m: m.priority_score)
                else:
                    # All are private, choose highest priority score
                    best = max(methods, key=lambda m: m.priority_score)
                deduplicated.append(best)
        
        self.discovered_methods = deduplicated
    
    def _get_type_hint_str(self, annotation: Any) -> Optional[str]:
        """Convert a type annotation to a string representation."""
        if annotation == inspect.Parameter.empty:
            return None
        
        if isinstance(annotation, type):
            return annotation.__name__
        
        if hasattr(annotation, '__name__'):
            return annotation.__name__
        
        # Convert complex type hints to string
        return str(annotation).replace('typing.', '')
    
    def _get_public_class_path(self, private_path: str) -> Optional[str]:
        """
        Try to find a public equivalent for a private class path.
        E.g., azure.storage.blob._blob_client.BlobClient -> azure.storage.blob.BlobClient
        """
        if not private_path or '._' not in private_path:
            return None
        
        # Simple heuristic: remove the private module part
        # E.g., azure.storage.blob._blob_client.BlobClient -> azure.storage.blob.BlobClient
        parts = private_path.split('.')
        public_parts = []
        
        for part in parts:
            if part.startswith('_') and part != '_':
                # Skip private module parts, but keep the class name
                continue
            public_parts.append(part)
        
        if len(public_parts) >= 2:  # At least module.ClassName
            return '.'.join(public_parts)
        
        return None
    
    def _serialize_default(self, default: Any) -> Any:
        """Serialize default values to JSON-compatible format."""
        if default == inspect.Parameter.empty:
            return None
        
        # Check for sentinel values from hints
        sentinel_defaults = self.hints.get('sentinel_defaults', ['NotSet', 'UNSET', 'Unset'])
        if str(default) in sentinel_defaults:
            return None  # Treat as optional
        
        # Try to keep the original value if JSON serializable
        try:
            json.dumps(default)
            return default
        except (TypeError, ValueError):
            # Fall back to string representation
            return str(default)
    
    def _is_stdlib_module(self, module: types.ModuleType) -> bool:
        """Check if a module is part of Python's standard library."""
        if not hasattr(module, '__file__') or module.__file__ is None:
            return True  # builtins/frozen modules
        
        try:
            module_path = pathlib.Path(module.__file__).resolve()
            return module_path.is_relative_to(_STDLIB_PATH)
        except (ValueError, AttributeError):
            return False
    
    def filter_high_value_methods(self, methods: List[MethodInfo]) -> List[MethodInfo]:
        """
        Filter to only high-value methods using improved prioritization.
        """
        # First, remove noise
        clean_methods = [m for m in methods if not self._is_noise_method(m)]
        
        # Sort by priority score
        clean_methods.sort(key=lambda m: m.priority_score, reverse=True)
        
        # Get priority limits from hints
        limits = self.hints.get('priority_limits', {})
        p2_limit = limits.get('p2_limit', 500)
        
        # Apply dynamic limiting based on SDK size
        if len(clean_methods) > 1000:
            # For very large SDKs, be more selective
            return clean_methods[:min(p2_limit, len(clean_methods) // 10)]
        elif len(clean_methods) > 500:
            # For large SDKs, use configured limit
            return clean_methods[:p2_limit]
        else:
            # For smaller SDKs, include more
            return clean_methods
    
    def _is_noise_method(self, method: MethodInfo) -> bool:
        """Determine if a method is noise that should be filtered out."""
        # Never filter core HTTP methods
        if self._is_core_http_method(method):
            return False
        
        # Check exclude patterns
        if self._should_exclude_name(method.name):
            return True
        
        # Filter double underscore methods (except __init__)
        if method.name.startswith('__') and method.name != '__init__':
            return True
        
        # Filter internal helpers
        if method.name.startswith('_') and not any(
            verb in method.name.lower() for verb in 
            ['get', 'set', 'create', 'delete', 'update']
        ):
            return True
        
        # Check penalize patterns with strong negative score
        if method.priority_score < -5:
            return True
        
        return False
    
    def _is_core_http_method(self, method: MethodInfo) -> bool:
        """Check if method is a core HTTP method that should never be filtered."""
        core_http_methods = ['get', 'post', 'put', 'delete', 'patch', 'head', 'options']
        return (method.name in core_http_methods and 
                ('requests.api' in method.full_name or 
                 'requests.Session' in str(method.parent_class)))