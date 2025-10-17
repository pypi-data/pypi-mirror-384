"""Core data models for API discovery."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class HTTPMethod(str, Enum):
    """HTTP methods supported by APIs."""

    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    DELETE = "DELETE"
    PATCH = "PATCH"
    HEAD = "HEAD"
    OPTIONS = "OPTIONS"


class FrameworkType(str, Enum):
    """Supported framework types."""

    SPRING_BOOT = "spring-boot"
    MICRONAUT = "micronaut"
    FASTAPI = "fastapi"
    FLASK = "flask"
    ASPNET_CORE = "aspnet-core"
    UNKNOWN = "unknown"


class AuthenticationType(str, Enum):
    """Types of authentication supported."""

    NONE = "none"
    BASIC = "basic"
    BEARER = "bearer"
    API_KEY = "apiKey"
    OAUTH2 = "oauth2"
    OPENID_CONNECT = "openIdConnect"
    CUSTOM = "custom"


class ParameterLocation(str, Enum):
    """Location of API parameters."""

    QUERY = "query"
    PATH = "path"
    HEADER = "header"
    COOKIE = "cookie"
    BODY = "body"


@dataclass
class APIParameter:
    """Represents an API parameter."""

    name: str
    location: ParameterLocation
    required: bool = False
    type: str = "string"
    description: Optional[str] = None
    default_value: Optional[Any] = None
    schema: Optional[Dict[str, Any]] = None
    example: Optional[Any] = None


@dataclass
class APIResponse:
    """Represents an API response."""

    status_code: int
    description: Optional[str] = None
    content_type: str = "application/json"
    schema: Optional[Dict[str, Any]] = None
    example: Optional[Any] = None


@dataclass
class AuthenticationRequirement:
    """Represents authentication requirements for an endpoint."""

    type: AuthenticationType
    scheme: Optional[str] = None
    bearer_format: Optional[str] = None
    flows: Optional[Dict[str, Any]] = None
    openid_connect_url: Optional[str] = None
    description: Optional[str] = None
    in_location: Optional[str] = None  # For API key
    name: Optional[str] = None  # For API key


@dataclass
class APIEndpoint:
    """Represents a discovered API endpoint."""

    path: str
    method: HTTPMethod
    summary: Optional[str] = None
    description: Optional[str] = None
    operation_id: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    parameters: List[APIParameter] = field(default_factory=list)
    request_body: Optional[Dict[str, Any]] = None
    responses: List[APIResponse] = field(default_factory=list)
    authentication: Optional[AuthenticationRequirement] = None
    deprecated: bool = False
    source_file: Optional[str] = None
    source_line: Optional[int] = None


@dataclass
class DiscoveryResult:
    """Result of the API discovery process."""

    framework: FrameworkType
    endpoints: List[APIEndpoint] = field(default_factory=list)
    base_path: str = ""
    version: Optional[str] = None
    title: str = "Discovered API"
    description: Optional[str] = None
    servers: List[Dict[str, str]] = field(default_factory=list)
    global_security: List[AuthenticationRequirement] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class VCSContext:
    """Context information from the VCS platform."""

    platform: str  # github, gitlab, jenkins, etc.
    repository_url: str
    repository_path: str
    branch: str
    commit_sha: Optional[str] = None
    event_type: Optional[str] = None  # push, pull_request, etc.
    environment_vars: Dict[str, str] = field(default_factory=dict)

