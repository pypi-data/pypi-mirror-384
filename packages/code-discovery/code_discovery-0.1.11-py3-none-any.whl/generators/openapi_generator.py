"""OpenAPI specification generator."""

import json
from typing import Any, Dict, List, Optional
import yaml
from core.models import (
    APIEndpoint,
    APIParameter,
    APIResponse,
    AuthenticationRequirement,
    AuthenticationType,
    DiscoveryResult,
    HTTPMethod,
    ParameterLocation,
)


class OpenAPIGenerator:
    """Generator for OpenAPI 3.0 specifications."""

    def __init__(self, version: str = "3.0.0"):
        """
        Initialize the OpenAPI generator.

        Args:
            version: OpenAPI version (default: 3.0.0).
        """
        self.version = version

    def generate(self, result: DiscoveryResult) -> Dict[str, Any]:
        """
        Generate OpenAPI specification from discovery result.

        Args:
            result: The discovery result containing API information.

        Returns:
            Dict[str, Any]: OpenAPI specification as a dictionary.
        """
        spec = {
            "openapi": self.version,
            "info": self._generate_info(result),
            "servers": self._generate_servers(result),
            "paths": self._generate_paths(result.endpoints),
        }

        # Add components if there are security schemes
        components = self._generate_components(result)
        if components:
            spec["components"] = components

        # Add security if there are global security requirements
        security = self._generate_security(result)
        if security:
            spec["security"] = security

        return spec

    def generate_yaml(self, result: DiscoveryResult) -> str:
        """
        Generate OpenAPI specification as YAML string.

        Args:
            result: The discovery result containing API information.

        Returns:
            str: OpenAPI specification in YAML format.
        """
        spec = self.generate(result)
        return yaml.dump(spec, sort_keys=False, default_flow_style=False)

    def generate_json(self, result: DiscoveryResult) -> str:
        """
        Generate OpenAPI specification as JSON string.

        Args:
            result: The discovery result containing API information.

        Returns:
            str: OpenAPI specification in JSON format.
        """
        spec = self.generate(result)
        return json.dumps(spec, indent=2)

    def _generate_info(self, result: DiscoveryResult) -> Dict[str, Any]:
        """Generate the info section."""
        # Use repository name as title if available, otherwise use the provided title
        title = self._get_repository_name(result) or result.title
        
        info = {
            "title": title,
            "version": result.version or "1.0.0",
        }

        if result.description:
            info["description"] = result.description

        return info

    def _get_repository_name(self, result: DiscoveryResult) -> Optional[str]:
        """
        Extract repository name from discovery result metadata.
        
        Args:
            result: The discovery result containing API information.
            
        Returns:
            Optional[str]: Repository name if available, None otherwise.
        """
        # Check metadata for repository path
        if result.metadata and 'repository_path' in result.metadata:
            import os
            return os.path.basename(result.metadata['repository_path'])
        
        # Check if there's repository path in the result (legacy)
        if hasattr(result, 'repository_path') and result.repository_path:
            import os
            return os.path.basename(result.repository_path)
        
        # Check if there's VCS context with repository URL
        if hasattr(result, 'vcs_context') and result.vcs_context:
            if hasattr(result.vcs_context, 'repository_url') and result.vcs_context.repository_url:
                # Extract repo name from URL (e.g., "https://github.com/user/repo" -> "repo")
                repo_url = result.vcs_context.repository_url
                if '/' in repo_url:
                    return repo_url.rstrip('/').split('/')[-1]
        
        return None

    def _generate_servers(self, result: DiscoveryResult) -> List[Dict[str, str]]:
        """Generate the servers section."""
        if result.servers:
            return result.servers

        # Default server
        servers = [{"url": result.base_path or "/"}]
        return servers

    def _generate_paths(self, endpoints: List[APIEndpoint]) -> Dict[str, Any]:
        """Generate the paths section."""
        paths = {}

        for endpoint in endpoints:
            path = endpoint.path
            if path not in paths:
                paths[path] = {}

            # Add operation for this HTTP method
            method_lower = endpoint.method.value.lower()
            paths[path][method_lower] = self._generate_operation(endpoint)

        return paths

    def _generate_operation(self, endpoint: APIEndpoint) -> Dict[str, Any]:
        """Generate an operation object for an endpoint."""
        operation = {}

        # Add summary and description
        if endpoint.summary:
            operation["summary"] = endpoint.summary
        if endpoint.description:
            operation["description"] = endpoint.description

        # Add operation ID
        if endpoint.operation_id:
            operation["operationId"] = endpoint.operation_id

        # Add tags
        if endpoint.tags:
            operation["tags"] = endpoint.tags

        # Add parameters
        if endpoint.parameters:
            operation["parameters"] = [
                self._generate_parameter(param) for param in endpoint.parameters
            ]

        # Add request body
        if endpoint.request_body:
            operation["requestBody"] = endpoint.request_body

        # Add responses
        operation["responses"] = self._generate_responses(endpoint.responses)

        # Add security
        if endpoint.authentication:
            operation["security"] = [
                {self._get_security_scheme_name(endpoint.authentication): []}
            ]

        # Add deprecated flag
        if endpoint.deprecated:
            operation["deprecated"] = True

        return operation

    def _generate_parameter(self, param: APIParameter) -> Dict[str, Any]:
        """Generate a parameter object."""
        parameter = {
            "name": param.name,
            "in": param.location.value,
            "required": param.required,
        }

        # Add schema
        if param.schema:
            parameter["schema"] = param.schema
        else:
            parameter["schema"] = {"type": param.type}

        # Add description
        if param.description:
            parameter["description"] = param.description

        # Add default value
        if param.default_value is not None:
            parameter["schema"]["default"] = param.default_value

        # Add example
        if param.example is not None:
            parameter["example"] = param.example

        return parameter

    def _generate_responses(self, responses: List[APIResponse]) -> Dict[str, Any]:
        """Generate responses object."""
        responses_dict = {}

        for response in responses:
            status_code = str(response.status_code)
            response_obj = {
                "description": response.description or "Response",
            }

            # Add content if schema is provided
            if response.schema or response.example:
                response_obj["content"] = {
                    response.content_type: {
                        "schema": response.schema or {"type": "object"}
                    }
                }

                if response.example:
                    response_obj["content"][response.content_type]["example"] = (
                        response.example
                    )

            responses_dict[status_code] = response_obj

        # Ensure there's at least a default response
        if not responses_dict:
            responses_dict["200"] = {"description": "Successful response"}

        return responses_dict

    def _generate_components(self, result: DiscoveryResult) -> Dict[str, Any]:
        """Generate components section."""
        components = {}

        # Generate security schemes
        security_schemes = self._generate_security_schemes(result)
        if security_schemes:
            components["securitySchemes"] = security_schemes

        return components if components else {}

    def _generate_security_schemes(
        self, result: DiscoveryResult
    ) -> Dict[str, Any]:
        """Generate security schemes from global security requirements."""
        schemes = {}

        for auth in result.global_security:
            scheme_name = self._get_security_scheme_name(auth)
            schemes[scheme_name] = self._generate_security_scheme(auth)

        # Also collect from individual endpoints
        for endpoint in result.endpoints:
            if endpoint.authentication:
                scheme_name = self._get_security_scheme_name(endpoint.authentication)
                if scheme_name not in schemes:
                    schemes[scheme_name] = self._generate_security_scheme(
                        endpoint.authentication
                    )

        return schemes

    def _generate_security_scheme(self, auth: AuthenticationRequirement) -> Dict[str, Any]:
        """Generate a security scheme definition."""
        scheme = {"type": auth.type.value}

        if auth.description:
            scheme["description"] = auth.description

        if auth.type == AuthenticationType.BASIC:
            scheme["scheme"] = "basic"

        elif auth.type == AuthenticationType.BEARER:
            scheme["scheme"] = "bearer"
            if auth.bearer_format:
                scheme["bearerFormat"] = auth.bearer_format

        elif auth.type == AuthenticationType.API_KEY:
            if auth.in_location:
                scheme["in"] = auth.in_location
            if auth.name:
                scheme["name"] = auth.name

        elif auth.type == AuthenticationType.OAUTH2:
            if auth.flows:
                scheme["flows"] = auth.flows

        elif auth.type == AuthenticationType.OPENID_CONNECT:
            if auth.openid_connect_url:
                scheme["openIdConnectUrl"] = auth.openid_connect_url

        return scheme

    def _generate_security(self, result: DiscoveryResult) -> List[Dict[str, List]]:
        """Generate global security requirements."""
        if not result.global_security:
            return []

        security = []
        for auth in result.global_security:
            scheme_name = self._get_security_scheme_name(auth)
            security.append({scheme_name: []})

        return security

    def _get_security_scheme_name(self, auth: AuthenticationRequirement) -> str:
        """Get the name for a security scheme."""
        if auth.scheme:
            return auth.scheme
        return auth.type.value

