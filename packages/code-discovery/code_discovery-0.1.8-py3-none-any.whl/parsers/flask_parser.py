"""Flask parser."""

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


class FlaskParser(BaseParser):
    """Parser for Flask applications."""

    def parse(self) -> DiscoveryResult:
        """Parse Flask source files for API endpoints."""
        endpoints = []
        py_files = self.find_files("*.py")

        for py_file in py_files:
            content = self.read_file(py_file)
            if content and self._has_flask_imports(content):
                endpoints.extend(self._parse_file(py_file, content))

        return DiscoveryResult(
            framework=FrameworkType.FLASK,
            endpoints=endpoints,
            title="Flask API",
        )

    def get_framework_type(self) -> FrameworkType:
        """Get the framework type."""
        return FrameworkType.FLASK

    def _has_flask_imports(self, content: str) -> bool:
        """Check if file imports Flask."""
        return "from flask import" in content or "import flask" in content

    def _parse_file(self, file_path: Path, content: str) -> List[APIEndpoint]:
        """Parse a Python file for Flask endpoints."""
        endpoints = []
        
        try:
            tree = ast.parse(content)
            
            # Find blueprints and their prefixes
            blueprints = self._find_blueprints(tree, content)
            
            # Parse function decorators
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    endpoint = self._parse_function(node, content, file_path, blueprints)
                    if endpoint:
                        endpoints.append(endpoint)
        except SyntaxError as e:
            print(f"Syntax error parsing {file_path}: {e}")
        
        return endpoints

    def _find_blueprints(self, tree: ast.AST, content: str) -> Dict[str, str]:
        """Find blueprint definitions and their URL prefixes."""
        blueprints = {}
        
        for node in ast.walk(tree):
            # Look for Blueprint(name, __name__, url_prefix='/path')
            if isinstance(node, ast.Assign):
                if isinstance(node.value, ast.Call):
                    if hasattr(node.value.func, 'id') and node.value.func.id == 'Blueprint':
                        # Extract blueprint name
                        if node.targets:
                            bp_name = node.targets[0].id if hasattr(node.targets[0], 'id') else None
                            # Extract url_prefix
                            prefix = self._extract_blueprint_prefix(node.value)
                            if bp_name:
                                blueprints[bp_name] = prefix or ""
        
        return blueprints

    def _extract_blueprint_prefix(self, call_node: ast.Call) -> Optional[str]:
        """Extract url_prefix from Blueprint call."""
        for keyword in call_node.keywords:
            if keyword.arg == 'url_prefix':
                if isinstance(keyword.value, ast.Constant):
                    return keyword.value.value
        return None

    def _parse_function(
        self,
        func_node: ast.FunctionDef,
        content: str,
        file_path: Path,
        blueprints: Dict[str, str],
    ) -> Optional[APIEndpoint]:
        """Parse a function for Flask route decorator."""
        # Check decorators for routes
        for decorator in func_node.decorator_list:
            endpoint = self._parse_decorator(
                decorator,
                func_node,
                content,
                file_path,
                blueprints,
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
        blueprints: Dict[str, str],
    ) -> Optional[APIEndpoint]:
        """Parse a decorator for route and methods."""
        # Handle @app.route(), @blueprint.route(), etc.
        if isinstance(decorator, ast.Call):
            if hasattr(decorator.func, 'attr') and decorator.func.attr == 'route':
                # Extract path
                path = self._extract_path_from_decorator(decorator)
                if not path:
                    return None
                
                # Extract HTTP methods
                methods = self._extract_methods_from_decorator(decorator)
                if not methods:
                    methods = [HTTPMethod.GET]  # Default to GET
                
                # Get blueprint prefix if applicable
                obj_name = decorator.func.value.id if hasattr(decorator.func.value, 'id') else None
                if obj_name and obj_name in blueprints:
                    prefix = blueprints[obj_name]
                    path = prefix.rstrip('/') + path
                
                # Normalize path
                path = self.normalize_path(path)
                
                # Extract parameters
                parameters = self._extract_parameters_from_function(func_node, path)
                
                # Create endpoint for each HTTP method
                # For simplicity, return only the first method
                # In production, you'd create multiple endpoints
                http_method = methods[0]
                
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
                        )
                    ],
                    source_file=self.get_relative_path(file_path),
                    source_line=func_node.lineno,
                )
        
        return None

    def _extract_path_from_decorator(self, decorator: ast.Call) -> Optional[str]:
        """Extract path from @route decorator."""
        # First positional argument
        if decorator.args:
            if isinstance(decorator.args[0], ast.Constant):
                return decorator.args[0].value
        
        # Keyword argument 'rule'
        for keyword in decorator.keywords:
            if keyword.arg == 'rule':
                if isinstance(keyword.value, ast.Constant):
                    return keyword.value.value
        
        return None

    def _extract_methods_from_decorator(self, decorator: ast.Call) -> List[HTTPMethod]:
        """Extract HTTP methods from decorator."""
        methods = []
        
        for keyword in decorator.keywords:
            if keyword.arg == 'methods':
                if isinstance(keyword.value, ast.List):
                    for elt in keyword.value.elts:
                        if isinstance(elt, ast.Constant):
                            try:
                                methods.append(HTTPMethod[elt.value.upper()])
                            except KeyError:
                                pass
        
        return methods

    def _extract_parameters_from_function(
        self,
        func_node: ast.FunctionDef,
        path: str,
    ) -> List[APIParameter]:
        """Extract parameters from function signature and path."""
        parameters = []
        
        # Extract path parameters
        path_vars = self.extract_path_variables(path)
        
        for var in path_vars:
            # Determine type from Flask path syntax
            param_type = "string"
            if "int:" in path:
                param_type = "integer"
            elif "float:" in path:
                param_type = "number"
            
            parameters.append(
                APIParameter(
                    name=var,
                    location=ParameterLocation.PATH,
                    required=True,
                    type=param_type,
                )
            )
        
        # Note: Flask doesn't have explicit query param declarations in decorators
        # We'd need more sophisticated analysis to detect request.args usage
        
        return parameters

