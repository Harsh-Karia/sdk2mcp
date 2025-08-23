#!/usr/bin/env python3
"""
Universal SDK Pattern Recognition System

Analyzes discovered methods and identifies common patterns:
- CRUD operations (Create, Read, Update, Delete)
- Authentication flows
- Resource relationships
- API groupings for MCP tool generation
"""

from dataclasses import dataclass
from typing import List, Dict, Set, Optional, Tuple
import re
from collections import defaultdict
from introspector import MethodInfo

@dataclass
class ResourcePattern:
    """Represents a discovered resource and its operations."""
    name: str
    crud_operations: Dict[str, List[MethodInfo]]  # 'create', 'read', 'update', 'delete'
    auth_methods: List[MethodInfo]
    relationships: List[str]  # Related resource names
    primary_class: Optional[str] = None
    
@dataclass
class APIGroup:
    """Groups related methods into a logical MCP tool."""
    name: str
    description: str
    methods: List[MethodInfo]
    resource_type: Optional[str] = None

class UniversalPatternRecognizer:
    """
    Universal pattern recognition system that works with any Python SDK.
    Uses deterministic patterns rather than hardcoded SDK knowledge.
    """
    
    def __init__(self):
        # CRUD verb patterns
        self.create_verbs = {'create', 'add', 'new', 'make', 'build', 'generate', 'post'}
        self.read_verbs = {'get', 'list', 'find', 'search', 'fetch', 'retrieve', 'show', 'view'}
        self.update_verbs = {'update', 'edit', 'modify', 'change', 'set', 'patch', 'put'}
        self.delete_verbs = {'delete', 'remove', 'destroy', 'drop', 'clear'}
        
        # Authentication patterns
        self.auth_patterns = {
            'login', 'auth', 'token', 'credential', 'key', 'secret', 
            'oauth', 'bearer', 'session', 'signin', 'signup'
        }
        
        # Common resource name patterns
        self.resource_indicators = {
            'user', 'repo', 'issue', 'pull', 'comment', 'file', 'branch',
            'commit', 'release', 'tag', 'org', 'team', 'project', 'wiki',
            'request', 'response', 'session', 'connection', 'client'
        }
    
    def analyze_patterns(self, methods: List[MethodInfo]) -> Dict[str, any]:
        """
        Main analysis method that discovers all patterns in the SDK.
        
        Returns:
            Dict containing discovered resources, API groups, and auth flows
        """
        results = {
            'resources': self._discover_resources(methods),
            'api_groups': self._group_methods_by_functionality(methods),
            'auth_flows': self._discover_auth_flows(methods),
            'statistics': self._generate_statistics(methods)
        }
        
        return results
    
    def _discover_resources(self, methods: List[MethodInfo]) -> Dict[str, ResourcePattern]:
        """
        Discover resources and their CRUD operations.
        
        Strategy:
        1. Extract potential resource names from method names and classes
        2. Group methods by resource
        3. Classify each method as Create, Read, Update, or Delete
        4. Identify relationships between resources
        """
        resources = {}
        
        # Step 1: Extract resource candidates
        resource_candidates = self._extract_resource_candidates(methods)
        
        # Step 2: Group methods by resource
        resource_methods = self._group_methods_by_resource(methods, resource_candidates)
        
        # Step 3: Create ResourcePattern for each discovered resource
        for resource_name, method_list in resource_methods.items():
            if len(method_list) >= 2:  # Only resources with multiple operations
                crud_ops = self._classify_crud_operations(method_list)
                auth_methods = [m for m in method_list if self._is_auth_method(m)]
                relationships = self._find_relationships(resource_name, resource_candidates)
                primary_class = self._find_primary_class(method_list)
                
                resources[resource_name] = ResourcePattern(
                    name=resource_name,
                    crud_operations=crud_ops,
                    auth_methods=auth_methods,
                    relationships=relationships,
                    primary_class=primary_class
                )
        
        return resources
    
    def _extract_resource_candidates(self, methods: List[MethodInfo]) -> Set[str]:
        """Extract potential resource names from methods and classes."""
        candidates = set()
        
        for method in methods:
            # From method names (e.g., get_user -> user, create_repository -> repository)
            method_words = re.findall(r'[a-z]+', method.name.lower())
            for word in method_words:
                if word in self.resource_indicators or len(word) > 4:
                    candidates.add(word)
            
            # From class names (e.g., github.Repository -> repository)
            if method.parent_class:
                class_parts = str(method.parent_class).split('.')
                for part in class_parts:
                    clean_part = re.sub(r'[^a-zA-Z]', '', part).lower()
                    if clean_part and len(clean_part) > 3:
                        candidates.add(clean_part)
        
        # Filter out overly generic terms
        generic_terms = {'method', 'function', 'object', 'class', 'module', 'self', 'args', 'kwargs'}
        candidates = candidates - generic_terms
        
        return candidates
    
    def _group_methods_by_resource(self, methods: List[MethodInfo], 
                                 resource_candidates: Set[str]) -> Dict[str, List[MethodInfo]]:
        """Group methods by the resource they operate on."""
        resource_methods = defaultdict(list)
        
        for method in methods:
            # Find which resource this method belongs to
            method_lower = method.name.lower()
            class_lower = str(method.parent_class).lower() if method.parent_class else ""
            
            matched_resources = []
            for resource in resource_candidates:
                if (resource in method_lower or 
                    resource in class_lower or
                    resource.rstrip('s') in method_lower or  # Handle plurals
                    resource + 's' in method_lower):
                    matched_resources.append(resource)
            
            # Prefer more specific matches
            if matched_resources:
                best_resource = max(matched_resources, key=len)
                resource_methods[best_resource].append(method)
            else:
                # Fallback: use primary class as resource if available
                if method.parent_class:
                    class_name = str(method.parent_class).split('.')[-1].lower()
                    if class_name not in {'session', 'client', 'api'}:
                        resource_methods[class_name].append(method)
        
        return dict(resource_methods)
    
    def _classify_crud_operations(self, methods: List[MethodInfo]) -> Dict[str, List[MethodInfo]]:
        """Classify methods into CRUD operations."""
        crud_ops = {
            'create': [],
            'read': [],
            'update': [], 
            'delete': []
        }
        
        for method in methods:
            method_lower = method.name.lower()
            
            # Check for CRUD verbs
            if any(verb in method_lower for verb in self.create_verbs):
                crud_ops['create'].append(method)
            elif any(verb in method_lower for verb in self.read_verbs):
                crud_ops['read'].append(method)
            elif any(verb in method_lower for verb in self.update_verbs):
                crud_ops['update'].append(method)
            elif any(verb in method_lower for verb in self.delete_verbs):
                crud_ops['delete'].append(method)
        
        return crud_ops
    
    def _is_auth_method(self, method: MethodInfo) -> bool:
        """Check if a method is related to authentication."""
        method_lower = method.name.lower()
        return any(pattern in method_lower for pattern in self.auth_patterns)
    
    def _find_relationships(self, resource_name: str, all_resources: Set[str]) -> List[str]:
        """Find relationships between resources based on naming patterns."""
        relationships = []
        
        # Simple heuristic: resources that share common prefixes/suffixes might be related
        for other_resource in all_resources:
            if other_resource != resource_name:
                # Check for hierarchical relationships (e.g., repository -> issue)
                if (resource_name in other_resource or 
                    other_resource in resource_name or
                    abs(len(resource_name) - len(other_resource)) <= 2):
                    relationships.append(other_resource)
        
        return relationships[:5]  # Limit to avoid noise
    
    def _find_primary_class(self, methods: List[MethodInfo]) -> Optional[str]:
        """Find the primary class for this resource."""
        class_counts = defaultdict(int)
        for method in methods:
            if method.parent_class:
                class_counts[str(method.parent_class)] += 1
        
        if class_counts:
            return max(class_counts.items(), key=lambda x: x[1])[0]
        return None
    
    def _group_methods_by_functionality(self, methods: List[MethodInfo]) -> List[APIGroup]:
        """Group methods into logical API groups for MCP tools."""
        groups = []
        
        # Group 1: HTTP Methods (for REST APIs like requests)
        http_methods = [m for m in methods if m.name.lower() in 
                       {'get', 'post', 'put', 'delete', 'patch', 'head', 'options'}]
        if http_methods:
            groups.append(APIGroup(
                name="http_requests",
                description="HTTP request methods",
                methods=http_methods,
                resource_type="http"
            ))
        
        # Group 2: Authentication methods
        auth_methods = [m for m in methods if self._is_auth_method(m)]
        if auth_methods:
            groups.append(APIGroup(
                name="authentication",
                description="Authentication and authorization methods", 
                methods=auth_methods,
                resource_type="auth"
            ))
        
        # Group 3: Search/Query methods
        search_methods = [m for m in methods if any(term in m.name.lower() 
                         for term in ['search', 'find', 'query', 'filter'])]
        if search_methods:
            groups.append(APIGroup(
                name="search_query",
                description="Search and query methods",
                methods=search_methods,
                resource_type="search"
            ))
        
        return groups
    
    def _discover_auth_flows(self, methods: List[MethodInfo]) -> Dict[str, List[MethodInfo]]:
        """Discover authentication flows and patterns."""
        auth_flows = {
            'token_based': [],
            'session_based': [],
            'oauth': [],
            'key_based': []
        }
        
        for method in methods:
            if not self._is_auth_method(method):
                continue
                
            method_lower = method.name.lower()
            
            if any(term in method_lower for term in ['token', 'bearer', 'jwt']):
                auth_flows['token_based'].append(method)
            elif any(term in method_lower for term in ['session', 'login', 'signin']):
                auth_flows['session_based'].append(method)
            elif any(term in method_lower for term in ['oauth', 'authorize']):
                auth_flows['oauth'].append(method)
            elif any(term in method_lower for term in ['key', 'secret', 'credential']):
                auth_flows['key_based'].append(method)
        
        # Remove empty flows
        return {k: v for k, v in auth_flows.items() if v}
    
    def _generate_statistics(self, methods: List[MethodInfo]) -> Dict[str, any]:
        """Generate statistics about the discovered patterns."""
        stats = {
            'total_methods': len(methods),
            'methods_by_type': defaultdict(int),
            'classes_analyzed': len(set(str(m.parent_class) for m in methods if m.parent_class)),
            'coverage_analysis': {}
        }
        
        # Count methods by type
        for method in methods:
            if self._is_auth_method(method):
                stats['methods_by_type']['authentication'] += 1
            elif any(verb in method.name.lower() for verb in self.create_verbs):
                stats['methods_by_type']['create'] += 1
            elif any(verb in method.name.lower() for verb in self.read_verbs):
                stats['methods_by_type']['read'] += 1
            elif any(verb in method.name.lower() for verb in self.update_verbs):
                stats['methods_by_type']['update'] += 1
            elif any(verb in method.name.lower() for verb in self.delete_verbs):
                stats['methods_by_type']['delete'] += 1
            else:
                stats['methods_by_type']['other'] += 1
        
        return stats