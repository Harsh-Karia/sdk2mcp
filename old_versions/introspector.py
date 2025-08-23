"""
Universal SDK Introspection Engine
Discovers methods, parameters, and types from ANY Python SDK without SDK-specific code.
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
    parameters: List[ParameterInfo]
    return_type: Optional[str] = None
    docstring: Optional[str] = None
    is_async: bool = False
    is_static: bool = False
    is_class_method: bool = False
    parent_class: Optional[str] = None


class UniversalIntrospector:
    """
    Universal introspection engine that works with ANY Python SDK.
    No SDK-specific code - uses patterns and heuristics.
    """
    
    def __init__(self):
        self.discovered_methods: List[MethodInfo] = []
        self.visited_objects: Set[int] = set()
        self._seen_methods: Set[tuple] = set()  # For deduplication
        self._root_package = None  # Track the root package being introspected
        
        # Common patterns to exclude (internal methods, private methods)
        self.exclude_patterns = [
            '__', '_internal', '_private', 'test_', 'Test', 
            'Mock', 'Stub', 'Base', 'Abstract', 'Mixin',
            'dump', 'close', 'aclose', '__enter__', '__aenter__', '__exit__'
        ]
        
        # Common SDK method patterns we want to find
        self.include_patterns = [
            'list', 'get', 'create', 'update', 'delete', 'fetch',
            'send', 'receive', 'connect', 'execute', 'run', 'call',
            'find', 'search', 'query', 'filter', 'save', 'load',
            'upload', 'download', 'publish', 'subscribe'
        ]
        
        # Container methods to exclude (inherited from dict, list, etc.)
        self.container_methods = {
            'fromkeys', 'popitem', 'setdefault', 'clear', 'copy', 'update',
            'items', 'keys', 'values', 'pop', 'get', 'append', 'extend',
            'insert', 'remove', 'reverse', 'sort'
        }
        
        # Compiled regex for better verb detection
        self.verb_pattern = re.compile(r'^(get|list|create|update|delete|patch|put|post|search|find)(_|$)', re.IGNORECASE)
    
    def discover_from_module(self, module_name: str) -> List[MethodInfo]:
        """
        Discover all methods from a module.
        Works with any module structure.
        """
        try:
            # Import the module dynamically
            module = importlib.import_module(module_name)
            logger.info(f"Introspecting module: {module_name}")
            
            # Clear previous discoveries and set root package
            self.discovered_methods = []
            self.visited_objects = set()
            self._seen_methods = set()
            self._root_package = module_name.split('.')[0]
            
            # Start recursive discovery
            self._discover_from_object(module, module_name)
            
            # Also discover key classes from the module
            self._discover_key_classes(module, module_name)
            
            logger.info(f"Discovered {len(self.discovered_methods)} methods")
            return self.discovered_methods
            
        except ImportError as e:
            logger.error(f"Failed to import module {module_name}: {e}")
            return []
    
    def _discover_key_classes(self, module: Any, module_name: str):
        """
        Find and introspect key resource classes in the module.
        Addresses the missing Repository, User, etc. classes issue.
        """
        try:
            key_classes = []
            
            for name, obj in inspect.getmembers(module):
                if inspect.isclass(obj) and not name.startswith('_'):
                    # Skip exception classes and base classes
                    if name.endswith(('Error', 'Exception', 'Base', 'Mixin')):
                        continue
                    
                    # Count public methods (good indicator of usefulness)
                    public_methods = [m for m in dir(obj) if not m.startswith('_') and callable(getattr(obj, m, None))]
                    
                    # Include if it has a reasonable number of methods
                    if len(public_methods) >= 5:
                        key_classes.append((name, obj, len(public_methods)))
            
            # Sort by number of public methods (more methods = more important)
            key_classes.sort(key=lambda x: x[2], reverse=True)
            
            # Take top 10 classes to avoid overwhelming output
            for name, cls, method_count in key_classes[:10]:
                class_path = f"{module_name}.{name}"
                logger.debug(f"Discovering key class: {class_path} ({method_count} methods)")
                self._discover_class_methods(cls, class_path)
                
        except Exception as e:
            logger.debug(f"Error discovering key classes for {module_name}: {e}")
    
    def _belongs_to_root_package(self, obj: Any) -> bool:
        """
        Check if an object belongs to the root package being introspected.
        This prevents stdlib and foreign package bleeding.
        """
        try:
            module = inspect.getmodule(obj)
            if not module or not hasattr(module, '__name__'):
                return False
            
            module_name = module.__name__
            return (module_name == self._root_package or 
                    module_name.startswith(self._root_package + '.'))
        except Exception:
            return False
    
    def discover_from_class(self, cls: Type, class_path: str = "") -> List[MethodInfo]:
        """
        Discover all methods from a class.
        """
        if not class_path:
            class_path = f"{cls.__module__}.{cls.__name__}"
        
        logger.info(f"Introspecting class: {class_path}")
        
        # Clear previous discoveries
        self.discovered_methods = []
        self.visited_objects = set()
        
        # Discover from the class
        self._discover_class_methods(cls, class_path)
        
        return self.discovered_methods
    
    def _discover_from_object(self, obj: Any, path: str, depth: int = 0):
        """
        Recursively discover methods from any Python object.
        """
        # Prevent infinite recursion
        if depth > 5 or id(obj) in self.visited_objects:
            return
        
        self.visited_objects.add(id(obj))
        
        # Get all attributes
        try:
            members = inspect.getmembers(obj)
        except Exception as e:
            logger.debug(f"Could not inspect {path}: {e}")
            return
        
        for name, member in members:
            # Skip if name matches exclude patterns
            if any(pattern in name for pattern in self.exclude_patterns):
                continue
            
            member_path = f"{path}.{name}"
            
            # If it's a function or method, extract it
            if inspect.isfunction(member) or inspect.ismethod(member):
                self._extract_method_info(member, member_path)
            
            # If it's a class, discover its methods
            elif inspect.isclass(member):
                self._discover_class_methods(member, member_path)
            
            # If it's a module, recurse into it (but only within same package and avoid stdlib)
            elif inspect.ismodule(member) and not self._is_stdlib_module(member):
                # Only recurse into modules under the same top-level package
                base_pkg = path.split('.')[0]
                member_name = getattr(member, '__name__', '')
                if member_name.startswith(base_pkg + '.'):
                    self._discover_from_object(member, member_path, depth + 1)
            
            # If it's an instance of a class (client object), discover its methods
            elif hasattr(member, '__class__') and not self._is_builtin_type(member):
                # Check if it looks like an SDK client or service object
                if self._looks_like_sdk_object(member):
                    self._discover_instance_methods(member, member_path)
    
    def _discover_class_methods(self, cls: Type, class_path: str):
        """
        Discover all methods from a class.
        """
        try:
            # Only introspect classes that belong to our root package
            if not self._belongs_to_root_package(cls):
                return
                
            for name, method in inspect.getmembers(cls):
                # Skip private/magic methods
                if name.startswith('_'):
                    continue
                
                # Check if it's a callable method and belongs to our package
                if callable(method) and self._belongs_to_root_package(method):
                    method_path = f"{class_path}.{name}"
                    self._extract_method_info(method, method_path, parent_class=class_path)
        except Exception as e:
            logger.debug(f"Error discovering class methods for {class_path}: {e}")
    
    def _discover_instance_methods(self, instance: Any, instance_path: str):
        """
        Discover methods from an instance object.
        """
        try:
            for name in dir(instance):
                # Skip private/magic methods
                if name.startswith('_'):
                    continue
                
                try:
                    attr = getattr(instance, name)
                    if callable(attr):
                        method_path = f"{instance_path}.{name}"
                        self._extract_method_info(attr, method_path)
                except Exception:
                    continue
        except Exception as e:
            logger.debug(f"Error discovering instance methods for {instance_path}: {e}")
    
    def _extract_method_info(self, method: Any, method_path: str, parent_class: Optional[str] = None):
        """
        Extract detailed information about a method.
        """
        try:
            # Get method signature
            sig = inspect.signature(method)
            
            # Create deduplication key (owner, method_name, signature)  
            module = inspect.getmodule(method)
            # Ensure owner is never None - use parent_class or module name
            owner = parent_class or (module.__name__ if module else 'unknown')
            method_name = method_path.split('.')[-1]
            sig_str = str(sig)
            dedup_key = (owner, method_name, sig_str)
            
            # Skip if we've already seen this exact method
            if dedup_key in self._seen_methods:
                return
            self._seen_methods.add(dedup_key)
            
            # Extract parameters
            parameters = []
            for param_name, param in sig.parameters.items():
                # Skip 'self' and 'cls' parameters
                if param_name in ['self', 'cls']:
                    continue
                
                # Handle *args and **kwargs correctly
                if param.kind in (inspect.Parameter.VAR_POSITIONAL, inspect.Parameter.VAR_KEYWORD):
                    is_required = False
                else:
                    is_required = param.default == inspect.Parameter.empty
                
                param_info = ParameterInfo(
                    name=param_name,
                    type_hint=self._get_type_hint_str(param.annotation),
                    default_value=param.default if param.default != inspect.Parameter.empty else None,
                    is_required=is_required
                )
                parameters.append(param_info)
            
            # Get return type
            return_type = self._get_type_hint_str(sig.return_annotation)
            
            # Get docstring
            docstring = inspect.getdoc(method)
            
            # Check if async
            is_async = inspect.iscoroutinefunction(method)
            
            # Check if static/class method (more accurate detection)
            is_static = False
            is_class_method = False
            
            # Try to get the original descriptor for accurate static/class method detection
            if parent_class:
                try:
                    # Extract the class object from parent_class path
                    class_parts = parent_class.split('.')
                    owner_cls = None
                    
                    # Try to resolve the class
                    if len(class_parts) >= 2:
                        # Try to get the class from the module
                        module_name = '.'.join(class_parts[:-1])
                        class_name = class_parts[-1]
                        try:
                            module = importlib.import_module(module_name)
                            owner_cls = getattr(module, class_name, None)
                        except (ImportError, AttributeError):
                            pass
                    
                    if owner_cls:
                        method_name = method_path.split('.')[-1]
                        descriptor = inspect.getattr_static(owner_cls, method_name, None)
                        if descriptor:
                            is_static = isinstance(descriptor, staticmethod)
                            is_class_method = isinstance(descriptor, classmethod)
                except Exception:
                    # Fall back to basic detection
                    pass
            
            # Create method info (ensure parent_class is never None for owner info)
            final_parent_class = parent_class or (module.__name__ if module else 'unknown')
            
            method_info = MethodInfo(
                name=method_path.split('.')[-1],
                full_name=method_path,
                parameters=parameters,
                return_type=return_type,
                docstring=docstring,
                is_async=is_async,
                is_static=is_static,
                is_class_method=is_class_method,
                parent_class=final_parent_class
            )
            
            self.discovered_methods.append(method_info)
            logger.debug(f"Discovered method: {method_path}")
            
        except Exception as e:
            logger.debug(f"Could not extract method info for {method_path}: {e}")
    
    def _get_type_hint_str(self, annotation: Any) -> Optional[str]:
        """
        Convert a type annotation to a string representation.
        """
        if annotation == inspect.Parameter.empty:
            return None
        
        if isinstance(annotation, type):
            return annotation.__name__
        
        if hasattr(annotation, '__name__'):
            return annotation.__name__
        
        # Convert complex type hints to string
        return str(annotation).replace('typing.', '')
    
    def _is_stdlib_module(self, module: types.ModuleType) -> bool:
        """
        Check if a module is part of Python's standard library.
        Fixed to use proper stdlib detection.
        """
        if not hasattr(module, '__file__') or module.__file__ is None:
            return True  # builtins/frozen modules
        
        try:
            module_path = pathlib.Path(module.__file__).resolve()
            return str(module_path).startswith(str(_STDLIB_PATH))
        except Exception:
            # If we can't determine, err on the side of caution
            return True
    
    def _is_builtin_type(self, obj: Any) -> bool:
        """
        Check if an object is a built-in type.
        """
        return type(obj).__module__ in ['builtins', '__builtin__']
    
    def _looks_like_sdk_object(self, obj: Any) -> bool:
        """
        Heuristic to determine if an object looks like an SDK client/service object.
        Improved to look for patterns within attribute names, not exact matches.
        """
        # Get all attributes
        attrs = dir(obj)
        
        # Check if it has methods containing SDK patterns (not just exact matches)
        has_sdk_methods = any(
            any(pattern in attr.lower() for attr in attrs)
            for pattern in self.include_patterns
        )
        
        # Check if it's not a simple built-in type
        is_complex = not self._is_builtin_type(obj)
        
        # Check class name patterns
        class_name = obj.__class__.__name__
        is_sdk_class = any(
            pattern in class_name.lower() 
            for pattern in ['client', 'service', 'api', 'sdk', 'resource', 'manager']
        )
        
        return is_complex and (has_sdk_methods or is_sdk_class)
    
    def filter_high_value_methods(self, methods: List[MethodInfo]) -> List[MethodInfo]:
        """
        Filter to only high-value methods with priority-based selection.
        Prioritizes core public API over internal helpers.
        """
        # Use priority-based filtering
        return self._prioritize_methods(methods)
    
    def _prioritize_methods(self, methods: List[MethodInfo]) -> List[MethodInfo]:
        """
        Priority-based method selection that ensures core public API is captured.
        """
        # Remove noise methods first
        clean_methods = [m for m in methods if not self._is_noise_method(m)]
        
        priority_methods = []
        seen_signatures = set()  # To avoid duplicates
        
        # Priority 1: Core module-level HTTP methods (requests.get, requests.post, etc.)
        core_http_methods = ['get', 'post', 'put', 'delete', 'patch', 'head', 'options']
        p1_methods = []
        for method in clean_methods:
            if (method.name in core_http_methods and 
                ('requests.api' in method.full_name or  # requests.api.get
                 method.full_name == f'requests.{method.name}' or  # requests.get (if exists)
                 'requests.Session' in str(method.parent_class))):  # Session.get
                sig_key = (method.full_name, str(method.parameters))  # Use full_name to avoid deduping different APIs
                if sig_key not in seen_signatures:
                    p1_methods.append(method)
                    seen_signatures.add(sig_key)
        
        # Priority 2: Main class public methods from important classes
        important_classes = [
            'requests.Session', 'requests.Response', 'requests.PreparedRequest',
            'github.Github', 'github.Repository', 'github.User', 'github.Organization',
            'github.Issue', 'github.PullRequest', 'github.AuthenticatedUser'
        ]
        p2_methods = []
        for method in clean_methods:
            if (method.parent_class and 
                any(cls in method.parent_class for cls in important_classes) and
                not method.name.startswith('_')):
                sig_key = (method.full_name, str(method.parameters))
                if sig_key not in seen_signatures:
                    p2_methods.append(method)
                    seen_signatures.add(sig_key)
        
        # Priority 3: Methods with REST documentation (GitHub's :calls: pattern)
        p3_methods = []
        for method in clean_methods:
            if (method.docstring and ':calls:' in method.docstring):
                sig_key = (method.full_name, str(method.parameters))
                if sig_key not in seen_signatures:
                    p3_methods.append(method)
                    seen_signatures.add(sig_key)
        
        # Priority 4: Methods with strong verb patterns at start of name
        p4_methods = []
        for method in clean_methods:
            if self.verb_pattern.match(method.name):
                sig_key = (method.full_name, str(method.parameters))
                if sig_key not in seen_signatures:
                    p4_methods.append(method)
                    seen_signatures.add(sig_key)
        
        # Priority 5: Other valuable patterns (but limit these)
        p5_methods = []
        valuable_patterns = ['search', 'find', 'auth', 'login', 'token']
        for method in clean_methods:
            method_lower = method.name.lower()
            if any(pattern in method_lower for pattern in valuable_patterns):
                sig_key = (method.full_name, str(method.parameters))
                if sig_key not in seen_signatures:
                    p5_methods.append(method)
                    seen_signatures.add(sig_key)
        
        # Combine priorities with limits to avoid overwhelming output
        result = []
        result.extend(p1_methods)  # All core HTTP methods
        result.extend(p2_methods[:200])  # Top 200 from main classes
        result.extend(p3_methods[:100])  # Top 100 with REST docs
        result.extend(p4_methods[:50])   # Top 50 with verb patterns
        result.extend(p5_methods[:20])   # Top 20 other valuable
        
        return result
    
    def _is_noise_method(self, method: MethodInfo) -> bool:
        """
        Determine if a method is noise that should be filtered out.
        Much more aggressive filtering.
        """
        # NEVER filter out core HTTP methods
        if self._is_core_http_method(method):
            return False
            
        # Check for dunder-like methods
        if method.name.startswith('get__') or method.name.startswith('set__'):
            return True
            
        # Check for internal utility methods (GitHub-specific noise)
        internal_methods = [
            'is_graphql', 'is_rest', 'complete', 'get__repr__',
            'getMandatoryRelease', 'getOptionalRelease', 'createException',
            '_check_cryptography'  # requests internal
        ]
        if method.name in internal_methods:
            return True
            
        # Check for container methods (unless they have REST hints)
        if (method.name in self.container_methods and 
            not (method.docstring and ':calls:' in method.docstring)):
            return True
            
        # Check for logging/handler methods
        if method.parent_class and any(handler in method.parent_class for handler in 
                                      ['Handler', 'Logger']):
            return True
        
        # Check for utility/adapter internal methods
        if any(util in method.full_name for util in [
            'SOCKSProxyManager', '_basic_auth_str', '_urllib3_request_context',
            'extract_cookies_to_jar', 'extract_zipped_paths', 'get_auth_from_url',
            'get_encoding_from_headers', 'parse_url', 'prepend_scheme_if_needed'
        ]):
            return True
            
        # Check for stdlib bleeding (datetime.now, etc.)
        if method.full_name and any(stdlib in method.full_name for stdlib in 
                                   ['datetime.now', 'builtins.', 'collections.']):
            return True
            
        # Check if method comes from container base classes
        if self._is_container_method(method):
            return True
        
        # Filter out methods from obvious utility classes
        if method.parent_class and any(util_class in method.parent_class for util_class in [
            'LookupDict', 'CaseInsensitiveDict', 'RequestsCookieJar'
        ]):
            # But allow if it's a core operation with REST hints
            if not (method.docstring and ':calls:' in method.docstring):
                return True
            
        return False
    
    def _is_core_http_method(self, method: MethodInfo) -> bool:
        """
        Check if this is a core HTTP method that should never be filtered as noise.
        """
        core_http_methods = ['get', 'post', 'put', 'delete', 'patch', 'head', 'options']
        return (method.name in core_http_methods and 
                ('requests.api' in method.full_name or 
                 'requests.Session' in str(method.parent_class)))
    
    def _is_container_method(self, method: MethodInfo) -> bool:
        """
        Check if method is inherited from Python container types.
        """
        # This is a heuristic - if the method name is a common container method
        # and doesn't have SDK-specific documentation, it's likely inherited
        if method.name in self.container_methods:
            # Allow if it has SDK-specific docstring with REST hints
            if method.docstring and (':calls:' in method.docstring or 'repo' in method.docstring.lower()):
                return False
            return True
        return False
    
    def to_dict(self, methods: Optional[List[MethodInfo]] = None) -> List[Dict]:
        """
        Convert method info to dictionary format.
        """
        if methods is None:
            methods = self.discovered_methods
        
        result = []
        for m in methods:
            # Convert parameters safely
            params = []
            for p in m.parameters:
                param_dict = {
                    'name': p.name,
                    'type_hint': p.type_hint,
                    'is_required': p.is_required,
                    'description': p.description
                }
                # Handle default values that might not be JSON serializable
                if p.default_value is not None:
                    try:
                        # Try to keep native types (bool, int, float, str, None)
                        json.dumps(p.default_value)  # Test if JSON serializable
                        param_dict['default_value'] = p.default_value
                    except (TypeError, ValueError):
                        # If not JSON serializable, convert to string
                        param_dict['default_value'] = str(p.default_value)
                else:
                    param_dict['default_value'] = None
                params.append(param_dict)
            
            result.append({
                'name': m.name,
                'full_name': m.full_name,
                'owner': m.parent_class,  # Include owner/class context
                'parameters': params,
                'return_type': m.return_type,
                'docstring': m.docstring[:200] if m.docstring else None,  # Truncate long docstrings
                'is_async': m.is_async,
                'is_static': m.is_static,
                'is_class_method': m.is_class_method
            })
        
        return result