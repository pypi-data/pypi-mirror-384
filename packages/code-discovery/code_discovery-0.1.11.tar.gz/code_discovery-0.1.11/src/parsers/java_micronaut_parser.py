"""Micronaut API parser."""

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


class MicronautParser(BaseParser):
    """Parser for Micronaut REST APIs."""

    def parse(self) -> DiscoveryResult:
        """Parse Micronaut source files for API endpoints."""
        endpoints = []
        java_files = self.find_files("*.java")

        for java_file in java_files:
            content = self.read_file(java_file)
            if content and (self._is_micronaut_controller(content) or self._is_jaxrs_controller(content)):
                endpoints.extend(self._parse_controller(java_file, content))

        return DiscoveryResult(
            framework=FrameworkType.MICRONAUT,
            endpoints=endpoints,
            title="Micronaut API",
        )

    def get_framework_type(self) -> FrameworkType:
        """Get the framework type."""
        return FrameworkType.MICRONAUT

    def _is_micronaut_controller(self, content: str) -> bool:
        """Check if the class is a Micronaut controller."""
        return "@Controller" in content

    def _is_jaxrs_controller(self, content: str) -> bool:
        """Check if the class is a JAX-RS controller."""
        return "@Path" in content and ("jakarta.ws.rs" in content or "javax.ws.rs" in content)

    def _parse_controller(self, file_path: Path, content: str) -> List[APIEndpoint]:
        """Parse a controller file for endpoints."""
        endpoints = []
        
        # Determine if this is JAX-RS or Micronaut controller
        is_jaxrs = self._is_jaxrs_controller(content)
        
        # Extract class-level path
        if is_jaxrs:
            class_path = self._extract_jaxrs_class_path(content)
        else:
            class_path = self._extract_micronaut_controller_path(content)
        
        # Find all HTTP method annotations (both Micronaut and JAX-RS)
        methods = self._extract_methods(content)
        
        for method_info in methods:
            # JAX-RS methods should only use JAX-RS class path
            method_class_path = class_path if not (method_info.get("is_jaxrs") and not is_jaxrs) else ""
            
            # Handle multiple URIs (uris attribute)
            if isinstance(method_info.get("path"), list):
                for path in method_info["path"]:
                    endpoint = self._create_endpoint(
                        {**method_info, "path": path},
                        method_class_path,
                        file_path,
                    )
                    if endpoint:
                        endpoints.append(endpoint)
            else:
                endpoint = self._create_endpoint(
                    method_info,
                    method_class_path,
                    file_path,
                )
                if endpoint:
                    endpoints.append(endpoint)

        return endpoints

    def _extract_micronaut_controller_path(self, content: str) -> str:
        """Extract class-level path from Micronaut @Controller."""
        patterns = [
            r'@Controller\s*\(\s*"([^"]+)"\s*\)',
            r'@Controller\s*\(\s*value\s*=\s*"([^"]+)"\s*\)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, content)
            if match:
                return match.group(1)
        
        return ""
    
    def _extract_jaxrs_class_path(self, content: str) -> str:
        """Extract class-level path from JAX-RS @Path."""
        # Look for class-level @Path (before any method annotations)
        # Match @Path at class level (typically appears with @Path\npublic class)
        pattern = r'@Path\s*\(\s*"([^"]+)"\s*\)\s*\n\s*public\s+class'
        match = re.search(pattern, content)
        if match:
            return match.group(1)
        
        return ""

    def _extract_methods(self, content: str) -> List[Dict[str, Any]]:
        """Extract method information from controller."""
        methods = []
        found_positions = set()  # Track positions to avoid duplicates
        
        # Micronaut HTTP annotations with single path
        micronaut_single_path_patterns = [
            (r'@Get\s*\(\s*"([^"]+)"', HTTPMethod.GET),
            (r'@Get\s*\(\s*value\s*=\s*"([^"]+)"', HTTPMethod.GET),
            (r'@Get\s*\(\s*uri\s*=\s*"([^"]+)"', HTTPMethod.GET),
            (r'@Post\s*\(\s*"([^"]+)"', HTTPMethod.POST),
            (r'@Post\s*\(\s*value\s*=\s*"([^"]+)"', HTTPMethod.POST),
            (r'@Post\s*\(\s*uri\s*=\s*"([^"]+)"', HTTPMethod.POST),
            (r'@Put\s*\(\s*"([^"]+)"', HTTPMethod.PUT),
            (r'@Put\s*\(\s*value\s*=\s*"([^"]+)"', HTTPMethod.PUT),
            (r'@Put\s*\(\s*uri\s*=\s*"([^"]+)"', HTTPMethod.PUT),
            (r'@Delete\s*\(\s*"([^"]+)"', HTTPMethod.DELETE),
            (r'@Delete\s*\(\s*value\s*=\s*"([^"]+)"', HTTPMethod.DELETE),
            (r'@Delete\s*\(\s*uri\s*=\s*"([^"]+)"', HTTPMethod.DELETE),
            (r'@Patch\s*\(\s*"([^"]+)"', HTTPMethod.PATCH),
            (r'@Patch\s*\(\s*value\s*=\s*"([^"]+)"', HTTPMethod.PATCH),
            (r'@Patch\s*\(\s*uri\s*=\s*"([^"]+)"', HTTPMethod.PATCH),
            (r'@Options\s*\(\s*"([^"]+)"', HTTPMethod.OPTIONS),
            (r'@Options\s*\(\s*value\s*=\s*"([^"]+)"', HTTPMethod.OPTIONS),
            (r'@Options\s*\(\s*uri\s*=\s*"([^"]+)"', HTTPMethod.OPTIONS),
            (r'@Head\s*\(\s*"([^"]+)"', HTTPMethod.HEAD),
            (r'@Head\s*\(\s*value\s*=\s*"([^"]+)"', HTTPMethod.HEAD),
            (r'@Head\s*\(\s*uri\s*=\s*"([^"]+)"', HTTPMethod.HEAD),
        ]
        
        # Micronaut HTTP annotations with multiple URIs (uris attribute)
        # Match uris = {..."..."...} - extract content between outer braces
        micronaut_multi_uris_patterns = [
            (r'@Get\s*\(\s*uris\s*=\s*\{(.+?)\}\s*\)', HTTPMethod.GET),
            (r'@Post\s*\(\s*uris\s*=\s*\{(.+?)\}\s*\)', HTTPMethod.POST),
            (r'@Put\s*\(\s*uris\s*=\s*\{(.+?)\}\s*\)', HTTPMethod.PUT),
            (r'@Delete\s*\(\s*uris\s*=\s*\{(.+?)\}\s*\)', HTTPMethod.DELETE),
            (r'@Patch\s*\(\s*uris\s*=\s*\{(.+?)\}\s*\)', HTTPMethod.PATCH),
            (r'@Options\s*\(\s*uris\s*=\s*\{(.+?)\}\s*\)', HTTPMethod.OPTIONS),
            (r'@Head\s*\(\s*uris\s*=\s*\{(.+?)\}\s*\)', HTTPMethod.HEAD),
        ]
        
        # Micronaut annotations without path (use controller base path)
        micronaut_no_path_patterns = [
            (r'@Get\s*\((?!\s*(?:value|uri|uris)\s*=)(?:[^)]*)\)', HTTPMethod.GET),
            (r'@Post\s*\((?!\s*(?:value|uri|uris)\s*=)(?:[^)]*)\)', HTTPMethod.POST),
            (r'@Put\s*\((?!\s*(?:value|uri|uris)\s*=)(?:[^)]*)\)', HTTPMethod.PUT),
            (r'@Delete\s*\((?!\s*(?:value|uri|uris)\s*=)(?:[^)]*)\)', HTTPMethod.DELETE),
            (r'@Patch\s*\((?!\s*(?:value|uri|uris)\s*=)(?:[^)]*)\)', HTTPMethod.PATCH),
            (r'@Options\s*\((?!\s*(?:value|uri|uris)\s*=)(?:[^)]*)\)', HTTPMethod.OPTIONS),
            (r'@Head\s*\((?!\s*(?:value|uri|uris)\s*=)(?:[^)]*)\)', HTTPMethod.HEAD),
        ]
        
        # Micronaut annotations without parentheses
        micronaut_no_paren_patterns = [
            (r'@Get\s+(?![\(])', HTTPMethod.GET),
            (r'@Post\s+(?![\(])', HTTPMethod.POST),
            (r'@Put\s+(?![\(])', HTTPMethod.PUT),
            (r'@Delete\s+(?![\(])', HTTPMethod.DELETE),
            (r'@Patch\s+(?![\(])', HTTPMethod.PATCH),
            (r'@Options\s+(?![\(])', HTTPMethod.OPTIONS),
            (r'@Head\s+(?![\(])', HTTPMethod.HEAD),
        ]
        
        # JAX-RS annotations (@GET, @POST, etc. from jakarta.ws.rs or javax.ws.rs)
        jaxrs_patterns = [
            (r'@GET\s*\n', HTTPMethod.GET),
            (r'@POST\s*\n', HTTPMethod.POST),
            (r'@PUT\s*\n', HTTPMethod.PUT),
            (r'@DELETE\s*\n', HTTPMethod.DELETE),
            (r'@PATCH\s*\n', HTTPMethod.PATCH),
            (r'@OPTIONS\s*\n', HTTPMethod.OPTIONS),
            (r'@HEAD\s*\n', HTTPMethod.HEAD),
        ]
        
        # JAX-RS @Path at method level
        jaxrs_path_pattern = r'@Path\s*\(\s*"([^"]+)"\s*\)'
        
        # Extract single-path Micronaut endpoints
        for pattern, http_method in micronaut_single_path_patterns:
            for match in re.finditer(pattern, content):
                if match.start() in found_positions:
                    continue
                found_positions.add(match.start())
                
                path = match.group(1)
                method_start = match.end()
                method_signature = self._extract_method_signature(content, method_start)
                
                methods.append({
                    "path": path,
                    "method": http_method,
                    "signature": method_signature,
                    "position": match.start(),
                })
        
        # Extract multi-URI Micronaut endpoints
        for pattern, http_method in micronaut_multi_uris_patterns:
            for match in re.finditer(pattern, content):
                if match.start() in found_positions:
                    continue
                found_positions.add(match.start())
                
                # Extract all URIs from the array
                uris_str = match.group(1)
                uris = re.findall(r'"([^"]+)"', uris_str)
                
                method_start = match.end()
                method_signature = self._extract_method_signature(content, method_start)
                
                methods.append({
                    "path": uris,  # List of paths
                    "method": http_method,
                    "signature": method_signature,
                    "position": match.start(),
                })
        
        # Extract Micronaut endpoints without paths
        for pattern, http_method in micronaut_no_path_patterns:
            for match in re.finditer(pattern, content):
                if match.start() in found_positions:
                    continue
                # Check if this is actually a path - if it contains a quote, skip it
                if '"' in match.group(0):
                    continue
                found_positions.add(match.start())
                
                method_start = match.end()
                method_signature = self._extract_method_signature(content, method_start)
                
                methods.append({
                    "path": "",  # Empty path means use controller base path
                    "method": http_method,
                    "signature": method_signature,
                    "position": match.start(),
                })
        
        # Extract Micronaut endpoints without parentheses
        for pattern, http_method in micronaut_no_paren_patterns:
            for match in re.finditer(pattern, content):
                if match.start() in found_positions:
                    continue
                found_positions.add(match.start())
                
                method_start = match.end()
                method_signature = self._extract_method_signature(content, method_start)
                
                methods.append({
                    "path": "",
                    "method": http_method,
                    "signature": method_signature,
                    "position": match.start(),
                })
        
        # Extract JAX-RS endpoints
        # First, find all @Path annotations at method level
        method_paths = {}
        for match in re.finditer(jaxrs_path_pattern, content):
            path = match.group(1)
            pos = match.start()
            method_paths[pos] = path
        
        # Then find JAX-RS HTTP method annotations
        for pattern, http_method in jaxrs_patterns:
            for match in re.finditer(pattern, content):
                if match.start() in found_positions:
                    continue
                found_positions.add(match.start())
                
                # Look backwards for @Path annotation (within 200 chars)
                path = ""
                search_start = max(0, match.start() - 200)
                preceding_content = content[search_start:match.start()]
                path_match = re.search(r'@Path\s*\(\s*"([^"]+)"\s*\)', preceding_content)
                if path_match:
                    path = path_match.group(1)
                
                method_start = match.end()
                method_signature = self._extract_method_signature(content, method_start)
                
                methods.append({
                    "path": path,
                    "method": http_method,
                    "signature": method_signature,
                    "position": match.start(),
                    "is_jaxrs": True,
                })
        
        return methods

    def _extract_method_signature(self, content: str, start_pos: int) -> str:
        """Extract Java method signature after annotation."""
        method_pattern = r'(public|private|protected)?\s+[\w<>[\],\s]+\s+\w+\s*\([^)]*\)'
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
        class_path: str,
        file_path: Path,
    ) -> Optional[APIEndpoint]:
        """Create an APIEndpoint from method information."""
        # Combine class path and method path
        full_path = self._combine_paths(class_path, method_info["path"])
        full_path = self.normalize_path(full_path)
        
        # Extract parameters from signature
        parameters = self._extract_parameters(method_info["signature"], full_path, method_info.get("is_jaxrs", False))
        
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

    def _extract_parameters(self, signature: str, path: str, is_jaxrs: bool = False) -> List[APIParameter]:
        """Extract parameters from method signature."""
        parameters = []
        
        # Extract path parameters from the path itself
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
        
        # Extract Micronaut @QueryValue parameters
        # Pattern 1: @QueryValue("name") Type param
        query_with_name = re.findall(r'@QueryValue\s*\(\s*"([^"]+)"\s*\)', signature)
        for param_name in query_with_name:
            if param_name not in path_vars:
                parameters.append(
                    APIParameter(
                        name=param_name,
                        location=ParameterLocation.QUERY,
                        required=False,
                        type="string",
                    )
                )
        
        # Pattern 2: @QueryValue Type paramName (uses parameter name)
        query_without_name = re.findall(r'@QueryValue(?!\s*\()[^)]*\s+\w+\s+(\w+)', signature)
        for param_name in query_without_name:
            if param_name not in path_vars and param_name not in query_with_name:
                parameters.append(
                    APIParameter(
                        name=param_name,
                        location=ParameterLocation.QUERY,
                        required=False,
                        type="string",
                    )
                )
        
        # Extract Micronaut @PathVariable parameters
        path_vars_annotated = re.findall(r'@PathVariable\s*\(\s*"([^"]+)"\s*\)', signature)
        for param_name in path_vars_annotated:
            if param_name not in [p.name for p in parameters]:
                parameters.append(
                    APIParameter(
                        name=param_name,
                        location=ParameterLocation.PATH,
                        required=True,
                        type="string",
                    )
                )
        
        # Extract JAX-RS parameters if JAX-RS endpoint
        if is_jaxrs:
            # @PathParam
            jaxrs_path_params = re.findall(r'@PathParam\s*\(\s*"([^"]+)"\s*\)', signature)
            for param_name in jaxrs_path_params:
                if param_name not in [p.name for p in parameters]:
                    parameters.append(
                        APIParameter(
                            name=param_name,
                            location=ParameterLocation.PATH,
                            required=True,
                            type="string",
                        )
                    )
            
            # @QueryParam
            jaxrs_query_params = re.findall(r'@QueryParam\s*\(\s*"([^"]+)"\s*\)', signature)
            for param_name in jaxrs_query_params:
                if param_name not in [p.name for p in parameters]:
                    parameters.append(
                        APIParameter(
                            name=param_name,
                            location=ParameterLocation.QUERY,
                            required=False,
                            type="string",
                        )
                    )
            
            # @HeaderParam
            jaxrs_header_params = re.findall(r'@HeaderParam\s*\(\s*"([^"]+)"\s*\)', signature)
            for param_name in jaxrs_header_params:
                parameters.append(
                    APIParameter(
                        name=param_name,
                        location=ParameterLocation.HEADER,
                        required=False,
                        type="string",
                    )
                )
        
        # Extract Micronaut @Header parameters
        header_params = re.findall(r'@Header\s*\(\s*"([^"]+)"\s*\)', signature)
        for param_name in header_params:
            if param_name not in [p.name for p in parameters]:
                parameters.append(
                    APIParameter(
                        name=param_name,
                        location=ParameterLocation.HEADER,
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
