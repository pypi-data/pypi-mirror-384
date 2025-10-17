"""External API client for notifying about discovered APIs."""

import requests
from typing import Dict, Any, Optional, List
from .apisec_config import APISecConfig


class APIClient:
    """Client for interacting with external API endpoints."""

    def __init__(
        self,
        endpoint: str,
        auth_token: Optional[str] = None,
        timeout: int = 30,
    ):
        """
        Initialize API client.

        Args:
            endpoint: External API endpoint URL.
            auth_token: Authentication token (optional).
            timeout: Request timeout in seconds.
        """
        self.endpoint = endpoint
        self.auth_token = auth_token
        self.timeout = timeout

    def send_openapi_spec(
        self,
        openapi_spec: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        Send OpenAPI specification to external API through two-step process.

        Args:
            openapi_spec: OpenAPI specification as dictionary.
            metadata: Additional metadata to send (optional).

        Returns:
            bool: True if successful, False otherwise.
        """
        if not self.endpoint:
            print("Warning: No external API endpoint configured. Skipping upload.")
            return False

        try:
            # Step 1: Upload OpenAPI spec file
            upload_result = self._upload_openapi_file(openapi_spec, metadata)
            if not upload_result:
                return False

            # Step 2: Process the uploaded application (if needed)
            # This could be a second API call if required by the external service
            # For now, we'll just return success after upload
            
            return True

        except Exception as e:
            print(f"✗ Unexpected error sending to external API: {e}")
            return False

    def _upload_openapi_file(
        self,
        openapi_spec: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        Upload OpenAPI specification file to external API.

        Args:
            openapi_spec: OpenAPI specification as dictionary.
            metadata: Additional metadata to send (optional).

        Returns:
            bool: True if successful, False otherwise.
        """
        try:
            import tempfile
            import os
            from io import BytesIO

            # Get application name from spec title or metadata
            application_name = self._get_application_name(openapi_spec, metadata)
            
            # Create temporary file with OpenAPI spec
            spec_content = self._serialize_openapi_spec(openapi_spec)
            
            # Prepare multipart form data
            files = {
                'fileUpload': ('openapi-spec.yaml', BytesIO(spec_content.encode('utf-8')), 'application/x-yaml')
            }
            
            data = {
                'applicationName': application_name,
                'origin': 'CLI'
            }

            # Prepare headers (no Content-Type for multipart/form-data)
            headers = {}
            if self.auth_token:
                headers["Authorization"] = f"Bearer {self.auth_token}"

            # Construct upload URL
            upload_url = f"{self.endpoint.rstrip('/')}/v1/applications/oas"

            # Send request
            print(f"Uploading OpenAPI specification to {upload_url}...")
            print(f"  Application: {application_name}")
            
            response = requests.post(
                upload_url,
                files=files,
                data=data,
                headers=headers,
                timeout=self.timeout,
            )

            # Check response
            response.raise_for_status()

            print(f"✓ Successfully uploaded OpenAPI specification")
            print(f"  Response: {response.status_code}")

            # Parse and log response
            if response.text:
                try:
                    response_data = response.json()
                    application_id = response_data.get('applicationId')
                    host_urls = response_data.get('hostUrls', [])
                    
                    print(f"  Application ID: {application_id}")
                    if host_urls:
                        print(f"  Host URLs: {', '.join(host_urls)}")
                    
                    # Make second API call to create instances
                    if application_id and host_urls:
                        instances_success = self._create_application_instances(application_id, host_urls)
                        
                        # Print application URL if both calls were successful
                        if instances_success:
                            application_url = f"https://cst.dev.apisecapps.com/application/{application_id}"
                            print(f"\n🎉 Application Created: {application_url}")
                    
                except Exception as e:
                    print(f"  Error parsing response: {e}")
                    print(f"  Response data: {response.text[:200]}")

                return True

        except requests.exceptions.Timeout:
            print(f"✗ Error: Request to {upload_url} timed out after {self.timeout}s")
            return False

        except requests.exceptions.ConnectionError:
            print(f"✗ Error: Could not connect to {upload_url}")
            return False

        except requests.exceptions.HTTPError as e:
            print(f"✗ HTTP Error: {e}")
            if hasattr(e.response, 'text'):
                print(f"  Response: {e.response.text[:200]}")
            return False

        except Exception as e:
            print(f"✗ Error uploading OpenAPI file: {e}")
            return False

    def _create_application_instances(
        self,
        application_id: str,
        host_urls: List[str],
    ) -> bool:
        """
        Create application instances using the application ID and host URLs.

        Args:
            application_id: The application ID from the previous API response.
            host_urls: List of host URLs from the previous API response.

        Returns:
            bool: True if successful, False otherwise.
        """
        try:
            # Prepare headers
            headers = {
                "Content-Type": "application/json"
            }
            if self.auth_token:
                headers["Authorization"] = f"Bearer {self.auth_token}"

            # Prepare payload
            payload = {
                "instanceRequestItems": [
                    {"hostUrl": host_url} for host_url in host_urls
                ]
            }

            # Construct instances URL
            instances_url = f"{self.endpoint.rstrip('/')}/v1/applications/{application_id}/instances/batch"

            # Send request
            print(f"Creating application instances...")
            print(f"  Instances URL: {instances_url}")
            print(f"  Host URLs: {', '.join(host_urls)}")
            
            response = requests.post(
                instances_url,
                json=payload,
                headers=headers,
                timeout=self.timeout,
            )

            # Check response
            response.raise_for_status()

            print(f"✓ Successfully created application instances")
            print(f"  Response: {response.status_code}")

            # Parse and log response
            if response.text:
                try:
                    response_data = response.json()
                    print(f"  Instance creation response: {response_data}")
                except:
                    print(f"  Response data: {response.text[:200]}")

            return True

        except requests.exceptions.Timeout:
            print(f"✗ Error: Request to {instances_url} timed out after {self.timeout}s")
            return False

        except requests.exceptions.ConnectionError:
            print(f"✗ Error: Could not connect to {instances_url}")
            return False

        except requests.exceptions.HTTPError as e:
            print(f"✗ HTTP Error: {e}")
            if hasattr(e.response, 'text'):
                print(f"  Response: {e.response.text[:200]}")
            return False

        except Exception as e:
            print(f"✗ Error creating application instances: {e}")
            return False

    def _get_application_name(
        self,
        openapi_spec: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Get application name from OpenAPI spec or metadata.

        Args:
            openapi_spec: OpenAPI specification as dictionary.
            metadata: Additional metadata to send (optional).

        Returns:
            str: Application name.
        """
        # Try to get from OpenAPI spec title first
        if 'info' in openapi_spec and 'title' in openapi_spec['info']:
            return openapi_spec['info']['title']
        
        # Try to get from metadata
        if metadata and 'repository_path' in metadata:
            import os
            return os.path.basename(metadata['repository_path'])
        
        # Default fallback
        return "discovered-api"

    def _serialize_openapi_spec(self, openapi_spec: Dict[str, Any]) -> str:
        """
        Serialize OpenAPI spec to YAML string.

        Args:
            openapi_spec: OpenAPI specification as dictionary.

        Returns:
            str: YAML string representation of the spec.
        """
        import yaml
        return yaml.dump(openapi_spec, sort_keys=False, default_flow_style=False)

    def send_discovery_event(
        self,
        event_type: str,
        data: Dict[str, Any],
    ) -> bool:
        """
        Send a discovery event to external API.

        Args:
            event_type: Type of event (e.g., "api_discovered", "api_updated").
            data: Event data.

        Returns:
            bool: True if successful, False otherwise.
        """
        if not self.endpoint:
            print("Warning: No external API endpoint configured. Skipping event.")
            return False

        try:
            payload = {
                "event_type": event_type,
                "data": data,
            }

            headers = {
                "Content-Type": "application/json",
            }

            if self.auth_token:
                headers["Authorization"] = f"Bearer {self.auth_token}"

            response = requests.post(
                self.endpoint,
                json=payload,
                headers=headers,
                timeout=self.timeout,
            )

            response.raise_for_status()
            print(f"✓ Successfully sent {event_type} event to external API")
            return True

        except Exception as e:
            print(f"✗ Error sending event to external API: {e}")
            return False

    def health_check(self) -> bool:
        """
        Check if the external API is reachable.

        Returns:
            bool: True if API is healthy, False otherwise.
        """
        if not self.endpoint:
            return False

        try:
            # Try to send a HEAD or GET request to the endpoint
            response = requests.head(self.endpoint, timeout=5)
            return response.status_code < 500
        except:
            return False

    @classmethod
    def from_apisec_config(cls, service: str = "api-discovery", apisec_config: Optional[APISecConfig] = None) -> Optional['APIClient']:
        """
        Create APIClient instance from .apisec configuration.

        Args:
            service: Service name from .apisec file (default: 'api-discovery').
            apisec_config: APISecConfig instance (optional, will create new if not provided).

        Returns:
            APIClient instance or None if service not configured.
        """
        if apisec_config is None:
            apisec_config = APISecConfig()

        if not apisec_config.has_service(service):
            print(f"Warning: Service '{service}' not found in .apisec configuration")
            return None

        endpoint = apisec_config.get_endpoint(service)
        token = apisec_config.get_token(service)

        if not endpoint:
            print(f"Warning: No endpoint configured for service '{service}'")
            return None

        return cls(endpoint=endpoint, auth_token=token)

    @classmethod
    def create_for_all_services(cls, apisec_config: Optional[APISecConfig] = None) -> List['APIClient']:
        """
        Create APIClient instances for all services in .apisec configuration.

        Args:
            apisec_config: APISecConfig instance (optional, will create new if not provided).

        Returns:
            List of APIClient instances for configured services.
        """
        if apisec_config is None:
            apisec_config = APISecConfig()

        clients = []
        for service in apisec_config.list_services():
            client = cls.from_apisec_config(service, apisec_config)
            if client:
                clients.append(client)

        return clients

