"""FastAPI parser."""

import ast
import re
from pathlib import Path
from typing import List, Optional, Dict, Any
from parsers.base import BaseParser
from core.models import (
    APIEndpoint,
    APIParameter,
    APIResponse,
    DiscoveryResult,
    FrameworkType,
    HTTPMethod,
    ParameterLocation,
)


class FastAPIParser(BaseParser):
    """Parser for FastAPI applications."""

    def parse(self) -> DiscoveryResult:
        """Parse FastAPI source files for API endpoints."""
        endpoints = []
        py_files = self.find_files("*.py")

        for py_file in py_files:
            content = self.read_file(py_file)
            if content and self._has_fastapi_imports(content):
                endpoints.extend(self._parse_file(py_file, content))

        return DiscoveryResult(
            framework=FrameworkType.FASTAPI,
            endpoints=endpoints,
            title="FastAPI",
        )

    def get_framework_type(self) -> FrameworkType:
        """Get the framework type."""
        return FrameworkType.FASTAPI

    def _has_fastapi_imports(self, content: str) -> bool:
        """Check if file imports FastAPI."""
        return "from fastapi import" in content or "import fastapi" in content

    def _parse_file(self, file_path: Path, content: str) -> List[APIEndpoint]:
        """Parse a Python file for FastAPI endpoints."""
        endpoints = []
        
        try:
            tree = ast.parse(content)
            
            # Find router and app variables
            routers = self._find_routers(tree)
            
            # Parse function decorators
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    endpoint = self._parse_function(node, content, file_path, routers)
                    if endpoint:
                        endpoints.append(endpoint)
        except SyntaxError as e:
            print(f"Syntax error parsing {file_path}: {e}")
        
        return endpoints

    def _find_routers(self, tree: ast.AST) -> Dict[str, str]:
        """Find router definitions and their prefixes."""
        routers = {}
        
        for node in ast.walk(tree):
            # Look for APIRouter(prefix="/path")
            if isinstance(node, ast.Assign):
                if isinstance(node.value, ast.Call):
                    if hasattr(node.value.func, 'attr') and node.value.func.attr == 'APIRouter':
                        # Extract router name
                        if node.targets:
                            router_name = node.targets[0].id if hasattr(node.targets[0], 'id') else None
                            # Extract prefix
                            prefix = self._extract_router_prefix(node.value)
                            if router_name and prefix:
                                routers[router_name] = prefix
        
        return routers

    def _extract_router_prefix(self, call_node: ast.Call) -> Optional[str]:
        """Extract prefix from APIRouter call."""
        for keyword in call_node.keywords:
            if keyword.arg == 'prefix':
                if isinstance(keyword.value, ast.Constant):
                    return keyword.value.value
        return None

    def _parse_function(
        self,
        func_node: ast.FunctionDef,
        content: str,
        file_path: Path,
        routers: Dict[str, str],
    ) -> Optional[APIEndpoint]:
        """Parse a function for FastAPI route decorator."""
        # Check decorators for HTTP methods
        for decorator in func_node.decorator_list:
            endpoint = self._parse_decorator(
                decorator,
                func_node,
                content,
                file_path,
                routers,
            )
            if endpoint:
                return endpoint
        
        return None

    def _parse_decorator(
        self,
        decorator: ast.AST,
        func_node: ast.FunctionDef,
        content: str,
        file_path: Path,
        routers: Dict[str, str],
    ) -> Optional[APIEndpoint]:
        """Parse a decorator for HTTP method and path."""
        # Handle app.get(), router.post(), etc.
        if isinstance(decorator, ast.Call):
            if hasattr(decorator.func, 'attr'):
                method_name = decorator.func.attr.upper()
                if method_name in ['GET', 'POST', 'PUT', 'DELETE', 'PATCH']:
                    http_method = HTTPMethod[method_name]
                    
                    # Extract path
                    path = self._extract_path_from_decorator(decorator)
                    if not path:
                        path = f"/{func_node.name}"
                    
                    # Get router prefix if applicable
                    router_name = decorator.func.value.id if hasattr(decorator.func.value, 'id') else None
                    if router_name and router_name in routers:
                        path = routers[router_name].rstrip('/') + path
                    
                    # Normalize path
                    path = self.normalize_path(path)
                    
                    # Extract parameters
                    parameters = self._extract_parameters_from_function(func_node, path)
                    
                    # Extract response model
                    response_model = self._extract_response_model(decorator)
                    
                    # Create endpoint
                    return APIEndpoint(
                        path=path,
                        method=http_method,
                        summary=ast.get_docstring(func_node),
                        operation_id=func_node.name,
                        parameters=parameters,
                        responses=[
                            APIResponse(
                                status_code=200,
                                description="Successful response",
                                schema={"type": response_model} if response_model else None,
                            )
                        ],
                        source_file=self.get_relative_path(file_path),
                        source_line=func_node.lineno,
                    )
        
        return None

    def _extract_path_from_decorator(self, decorator: ast.Call) -> Optional[str]:
        """Extract path from decorator arguments."""
        # First positional argument
        if decorator.args:
            if isinstance(decorator.args[0], ast.Constant):
                return decorator.args[0].value
        
        # Keyword argument 'path'
        for keyword in decorator.keywords:
            if keyword.arg == 'path':
                if isinstance(keyword.value, ast.Constant):
                    return keyword.value.value
        
        return None

    def _extract_response_model(self, decorator: ast.Call) -> Optional[str]:
        """Extract response_model from decorator."""
        for keyword in decorator.keywords:
            if keyword.arg == 'response_model':
                if hasattr(keyword.value, 'id'):
                    return keyword.value.id
        return None

    def _extract_parameters_from_function(
        self,
        func_node: ast.FunctionDef,
        path: str,
    ) -> List[APIParameter]:
        """Extract parameters from function signature."""
        parameters = []
        
        # Extract path parameters
        path_vars = self.extract_path_variables(path)
        
        # Analyze function arguments
        for arg in func_node.args.args:
            arg_name = arg.arg
            
            # Skip 'self' and 'cls'
            if arg_name in ['self', 'cls']:
                continue
            
            # Determine parameter location
            if arg_name in path_vars:
                location = ParameterLocation.PATH
                required = True
            else:
                # Default to query parameter
                location = ParameterLocation.QUERY
                required = func_node.args.defaults is None or len(func_node.args.defaults) == 0
            
            # Extract type annotation
            param_type = "string"
            if arg.annotation:
                param_type = self._extract_type_annotation(arg.annotation)
            
            parameters.append(
                APIParameter(
                    name=arg_name,
                    location=location,
                    required=required,
                    type=param_type,
                )
            )
        
        return parameters

    def _extract_type_annotation(self, annotation: ast.AST) -> str:
        """Extract type from annotation."""
        if isinstance(annotation, ast.Name):
            type_map = {
                'int': 'integer',
                'float': 'number',
                'bool': 'boolean',
                'str': 'string',
            }
            return type_map.get(annotation.id, 'string')
        return 'string'

