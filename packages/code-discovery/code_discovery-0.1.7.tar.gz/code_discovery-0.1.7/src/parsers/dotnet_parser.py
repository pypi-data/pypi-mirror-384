"""ASP.NET Core parser."""

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


class DotNetParser(BaseParser):
    """Parser for ASP.NET Core APIs."""

    def parse(self) -> DiscoveryResult:
        """Parse ASP.NET Core source files for API endpoints."""
        endpoints = []
        cs_files = self.find_files("*.cs")

        for cs_file in cs_files:
            content = self.read_file(cs_file)
            if content and self._is_api_controller(content):
                endpoints.extend(self._parse_controller(cs_file, content))

        return DiscoveryResult(
            framework=FrameworkType.ASPNET_CORE,
            endpoints=endpoints,
            title="ASP.NET Core API",
        )

    def get_framework_type(self) -> FrameworkType:
        """Get the framework type."""
        return FrameworkType.ASPNET_CORE

    def _is_api_controller(self, content: str) -> bool:
        """Check if the class is an API controller."""
        return "[ApiController]" in content or ": ControllerBase" in content

    def _parse_controller(self, file_path: Path, content: str) -> List[APIEndpoint]:
        """Parse a controller file for endpoints."""
        endpoints = []
        
        # Extract class-level [Route] attribute
        class_route = self._extract_class_route(content)
        
        # Find all HTTP method attributes
        methods = self._extract_methods(content)
        
        for method_info in methods:
            endpoint = self._create_endpoint(
                method_info,
                class_route,
                file_path,
            )
            if endpoint:
                endpoints.append(endpoint)

        return endpoints

    def _extract_class_route(self, content: str) -> str:
        """Extract class-level [Route] attribute."""
        # Match [Route("path")] or [Route("api/[controller]")]
        patterns = [
            r'\[Route\s*\(\s*"([^"]+)"\s*\)\]',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, content)
            if match:
                route = match.group(1)
                # Handle [controller] placeholder
                controller_match = re.search(r'class\s+(\w+)Controller', content)
                if controller_match and '[controller]' in route:
                    controller_name = controller_match.group(1).lower()
                    route = route.replace('[controller]', controller_name)
                return route
        
        return ""

    def _extract_methods(self, content: str) -> List[Dict[str, Any]]:
        """Extract method information from controller."""
        methods = []
        
        # Patterns for ASP.NET Core HTTP attributes
        http_patterns = [
            (r'\[HttpGet\s*\(\s*"([^"]+)"\s*\)\]', HTTPMethod.GET),
            (r'\[HttpGet\]', HTTPMethod.GET),
            (r'\[HttpPost\s*\(\s*"([^"]+)"\s*\)\]', HTTPMethod.POST),
            (r'\[HttpPost\]', HTTPMethod.POST),
            (r'\[HttpPut\s*\(\s*"([^"]+)"\s*\)\]', HTTPMethod.PUT),
            (r'\[HttpPut\]', HTTPMethod.PUT),
            (r'\[HttpDelete\s*\(\s*"([^"]+)"\s*\)\]', HTTPMethod.DELETE),
            (r'\[HttpDelete\]', HTTPMethod.DELETE),
            (r'\[HttpPatch\s*\(\s*"([^"]+)"\s*\)\]', HTTPMethod.PATCH),
            (r'\[HttpPatch\]', HTTPMethod.PATCH),
        ]
        
        for pattern, http_method in http_patterns:
            for match in re.finditer(pattern, content):
                # Extract path if present
                path = match.group(1) if match.lastindex and match.lastindex >= 1 else ""
                
                # Extract method signature
                method_start = match.end()
                method_signature = self._extract_method_signature(content, method_start)
                
                # If no path specified, use method name
                if not path and method_signature:
                    method_name = self._extract_method_name(method_signature)
                    if method_name:
                        path = method_name
                
                methods.append({
                    "path": path,
                    "method": http_method,
                    "signature": method_signature,
                    "position": match.start(),
                })
        
        return methods

    def _extract_method_signature(self, content: str, start_pos: int) -> str:
        """Extract C# method signature after attribute."""
        # Match method declaration
        method_pattern = r'(public|private|protected|internal)?\s+\w+\s+\w+\s*\([^)]*\)'
        match = re.search(method_pattern, content[start_pos:start_pos+500])
        if match:
            return match.group(0)
        return ""

    def _extract_method_name(self, signature: str) -> str:
        """Extract method name from signature."""
        match = re.search(r'\s+(\w+)\s*\(', signature)
        if match:
            return match.group(1)
        return ""

    def _create_endpoint(
        self,
        method_info: Dict[str, Any],
        class_route: str,
        file_path: Path,
    ) -> Optional[APIEndpoint]:
        """Create an APIEndpoint from method information."""
        # Combine class route and method path
        full_path = self._combine_paths(class_route, method_info["path"])
        full_path = self.normalize_path(full_path)
        
        # Extract parameters from signature
        parameters = self._extract_parameters(method_info["signature"], full_path)
        
        # Create endpoint
        endpoint = APIEndpoint(
            path=full_path,
            method=method_info["method"],
            operation_id=self._generate_operation_id(full_path, method_info["method"]),
            parameters=parameters,
            responses=[
                APIResponse(
                    status_code=200,
                    description="Successful response",
                )
            ],
            source_file=self.get_relative_path(file_path),
        )
        
        return endpoint

    def _combine_paths(self, base: str, path: str) -> str:
        """Combine base path and method path."""
        if not base:
            return path
        if not path:
            return base
        
        base = base.rstrip('/')
        path = path.lstrip('/')
        
        return f"{base}/{path}"

    def _extract_parameters(self, signature: str, path: str) -> List[APIParameter]:
        """Extract parameters from method signature."""
        parameters = []
        
        # Extract path parameters
        path_vars = self.extract_path_variables(path)
        for var in path_vars:
            parameters.append(
                APIParameter(
                    name=var,
                    location=ParameterLocation.PATH,
                    required=True,
                    type="string",
                )
            )
        
        # Extract parameters from signature
        # Look for [FromQuery], [FromRoute], [FromBody] attributes
        query_params = re.findall(r'\[FromQuery\][^,)]*\s+(\w+)', signature)
        for param in query_params:
            if param not in path_vars:
                parameters.append(
                    APIParameter(
                        name=param,
                        location=ParameterLocation.QUERY,
                        required=False,
                        type="string",
                    )
                )
        
        return parameters

    def _generate_operation_id(self, path: str, method: HTTPMethod) -> str:
        """Generate operation ID from path and method."""
        path_parts = [p for p in path.split('/') if p and not p.startswith('{')]
        operation_id = method.value.lower() + ''.join(p.capitalize() for p in path_parts)
        return operation_id

