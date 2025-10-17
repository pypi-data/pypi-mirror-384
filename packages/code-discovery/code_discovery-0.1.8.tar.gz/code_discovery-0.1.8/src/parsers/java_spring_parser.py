"""Spring Boot API parser."""

import re
from pathlib import Path
from typing import List, Optional, Dict, Any
from parsers.base import BaseParser
from core.models import (
    APIEndpoint,
    APIParameter,
    APIResponse,
    AuthenticationRequirement,
    AuthenticationType,
    DiscoveryResult,
    FrameworkType,
    HTTPMethod,
    ParameterLocation,
)


class SpringBootParser(BaseParser):
    """Parser for Spring Boot REST APIs."""

    def parse(self) -> DiscoveryResult:
        """Parse Spring Boot source files for API endpoints."""
        endpoints = []
        java_files = self.find_files("*.java")

        for java_file in java_files:
            content = self.read_file(java_file)
            if content and self._is_rest_controller(content):
                endpoints.extend(self._parse_controller(java_file, content))

        return DiscoveryResult(
            framework=FrameworkType.SPRING_BOOT,
            endpoints=endpoints,
            title="Spring Boot API",
        )

    def get_framework_type(self) -> FrameworkType:
        """Get the framework type."""
        return FrameworkType.SPRING_BOOT

    def _is_rest_controller(self, content: str) -> bool:
        """Check if the class is a REST controller."""
        return "@RestController" in content or "@Controller" in content

    def _parse_controller(self, file_path: Path, content: str) -> List[APIEndpoint]:
        """Parse a controller file for endpoints."""
        endpoints = []
        
        # Extract class-level @RequestMapping
        class_path = self._extract_class_request_mapping(content)
        
        # Find all method annotations
        methods = self._extract_methods(content)
        
        for method_info in methods:
            endpoint = self._create_endpoint(
                method_info,
                class_path,
                file_path,
            )
            if endpoint:
                endpoints.append(endpoint)

        return endpoints

    def _extract_class_request_mapping(self, content: str) -> str:
        """Extract class-level @RequestMapping path."""
        # Match @RequestMapping("/path") or @RequestMapping(value = "/path")
        patterns = [
            r'@RequestMapping\s*\(\s*"([^"]+)"\s*\)',
            r'@RequestMapping\s*\(\s*value\s*=\s*"([^"]+)"\s*\)',
            r'@RequestMapping\s*\(\s*path\s*=\s*"([^"]+)"\s*\)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, content)
            if match:
                return match.group(1)
        
        return ""

    def _extract_methods(self, content: str) -> List[Dict[str, Any]]:
        """Extract method information from controller."""
        methods = []
        
        # Patterns for different Spring annotations
        mapping_patterns = [
            (r'@GetMapping\s*\(\s*"([^"]+)"\s*\)', HTTPMethod.GET),
            (r'@PostMapping\s*\(\s*"([^"]+)"\s*\)', HTTPMethod.POST),
            (r'@PutMapping\s*\(\s*"([^"]+)"\s*\)', HTTPMethod.PUT),
            (r'@DeleteMapping\s*\(\s*"([^"]+)"\s*\)', HTTPMethod.DELETE),
            (r'@PatchMapping\s*\(\s*"([^"]+)"\s*\)', HTTPMethod.PATCH),
            (r'@RequestMapping\s*\([^)]*method\s*=\s*RequestMethod\.(\w+)[^)]*value\s*=\s*"([^"]+)"[^)]*\)', None),
        ]
        
        for pattern, default_method in mapping_patterns:
            for match in re.finditer(pattern, content):
                if default_method:
                    path = match.group(1)
                    http_method = default_method
                else:
                    http_method = HTTPMethod[match.group(1).upper()]
                    path = match.group(2)
                
                # Extract method signature and body
                method_start = match.end()
                method_signature = self._extract_method_signature(content, method_start)
                
                methods.append({
                    "path": path,
                    "method": http_method,
                    "signature": method_signature,
                    "position": match.start(),
                })
        
        return methods

    def _extract_method_signature(self, content: str, start_pos: int) -> str:
        """Extract Java method signature after annotation."""
        # Find the next method declaration
        method_pattern = r'(public|private|protected)?\s+\w+\s+\w+\s*\([^)]*\)'
        match = re.search(method_pattern, content[start_pos:start_pos+500])
        if match:
            return match.group(0)
        return ""

    def _create_endpoint(
        self,
        method_info: Dict[str, Any],
        class_path: str,
        file_path: Path,
    ) -> Optional[APIEndpoint]:
        """Create an APIEndpoint from method information."""
        # Combine class path and method path
        full_path = self._combine_paths(class_path, method_info["path"])
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
        
        # Remove trailing slash from base and leading slash from path
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
        
        # Extract query parameters from @RequestParam
        request_params = re.findall(r'@RequestParam[^)]*\s+\w+\s+(\w+)', signature)
        for param in request_params:
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
        # Remove leading slash and convert to camelCase
        path_parts = [p for p in path.split('/') if p and not p.startswith('{')]
        operation_id = method.value.lower() + ''.join(p.capitalize() for p in path_parts)
        return operation_id

