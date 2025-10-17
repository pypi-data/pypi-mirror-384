# Code Discovery - Automatic API Discovery System

[![GitHub release](https://img.shields.io/github/v/release/YOUR_USERNAME/code-discovery)](https://github.com/YOUR_USERNAME/code-discovery/releases)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)

## Overview

Code Discovery is an automated system that discovers API endpoints in code repositories and generates OpenAPI specifications. It supports multiple version control systems and frameworks, running entirely within your VCS runners for maximum security.

## ⚡ Quick Start

```bash
# 1. Clone the repository
git clone https://github.com/YOUR_USERNAME/code-discovery.git
cd code-discovery

# 2. Install
pip install -r requirements.txt
pip install -e .

# 3. Run on your project
code-discovery --repo-path /path/to/your/api/project
```

✅ That's it! Your OpenAPI spec is generated at `openapi-spec.yaml`

📖 **Detailed Instructions**: See [INSTALL_INSTRUCTIONS.md](INSTALL_INSTRUCTIONS.md)

## Features

- **Multi-VCS Support**: GitHub, GitLab, Jenkins, CircleCI, Harness
- **Multi-Framework Support**:
  - Java: Spring Boot, Micronaut
  - Python: FastAPI, Flask
  - .NET: ASP.NET Core
- **Automatic OpenAPI Generation**: Discovers endpoints, inputs, outputs, and authentication requirements
- **Secure Execution**: Runs entirely on your infrastructure - code never leaves your VCS environment
- **Extensible Architecture**: Easy to add new frameworks and VCS platforms

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    VCS Platform                         │
│  (GitHub/GitLab/Jenkins/CircleCI/Harness)              │
└─────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────┐
│                   Orchestrator                          │
│  - Coordinates the discovery workflow                   │
│  - Manages VCS interactions                            │
└─────────────────────────────────────────────────────────┘
                          │
            ┌─────────────┼─────────────┐
            ▼             ▼             ▼
    ┌──────────┐   ┌──────────┐   ┌──────────┐
    │ Detectors│   │  Parsers │   │Generator │
    │          │   │          │   │          │
    │Framework │   │API Info  │   │ OpenAPI  │
    │Detection │   │Extraction│   │   Spec   │
    └──────────┘   └──────────┘   └──────────┘
```

## Installation

### Method 1: Install from GitHub (Recommended)

```bash
# Clone the repository
git clone https://github.com/YOUR_USERNAME/code-discovery.git
cd code-discovery

# Install dependencies and package
pip install -r requirements.txt
pip install -e .

# Verify installation
code-discovery --version
```

📖 **Full installation guide**: [INSTALL_INSTRUCTIONS.md](INSTALL_INSTRUCTIONS.md)

### Method 2: CI/CD Integration

**GitHub Actions** - Add to `.github/workflows/api-discovery.yml`:
```yaml
- name: Install Code Discovery
  run: |
    git clone https://github.com/YOUR_USERNAME/code-discovery.git /tmp/code-discovery
    cd /tmp/code-discovery
    pip install -r requirements.txt
    pip install -e .

- name: Run Discovery
  run: code-discovery --repo-path .
```

**GitLab CI** - Add to `.gitlab-ci.yml`:
```yaml
before_script:
  - git clone https://github.com/YOUR_USERNAME/code-discovery.git /tmp/code-discovery
  - cd /tmp/code-discovery && pip install -r requirements.txt && pip install -e .
  - cd $CI_PROJECT_DIR

script:
  - code-discovery --repo-path .
```

See example configurations in `.github/workflows/`, `.gitlab-ci.yml`, `Jenkinsfile`, etc.

## Configuration

Create a `.codediscovery.yml` file in your repository root:

```yaml
# API Discovery Configuration
api_discovery:
  enabled: true
  
  # Frameworks to scan (leave empty to auto-detect all)
  frameworks:
    - spring-boot
    - micronaut
    - fastapi
    - flask
    - aspnet-core
  
  # OpenAPI specification settings
  openapi:
    version: "3.0.0"
    output_path: "openapi-spec.yaml"
    include_examples: true
  
  # External API endpoint (optional)
  external_api:
    enabled: true
    endpoint: "https://api.example.com/openapi/upload"
    auth_token_env: "API_DISCOVERY_TOKEN"
```

## Usage

### Automatic (Recommended)

Once installed as a VCS app, the system automatically:
1. Triggers on push/PR events
2. Scans the repository for API frameworks
3. Extracts API endpoint information
4. Generates OpenAPI specification
5. Commits the spec back to the repository
6. Notifies your external API endpoint

### Manual Execution

```bash
# Run discovery on current directory
python -m src.main

# Specify repository path
python -m src.main --repo-path /path/to/repo

# Dry run (don't commit back)
python -m src.main --dry-run
```

## Extending the System

### Adding a New Framework

1. Create a detector in `src/detectors/your_framework.py`:
```python
from src.detectors.base import BaseDetector

class YourFrameworkDetector(BaseDetector):
    def detect(self) -> bool:
        # Detection logic
        pass
```

2. Create a parser in `src/parsers/your_framework_parser.py`:
```python
from src.parsers.base import BaseParser

class YourFrameworkParser(BaseParser):
    def parse(self) -> List[APIEndpoint]:
        # Parsing logic
        pass
```

### Adding a New VCS Platform

Implement the `BaseVCSAdapter` interface in `src/vcs/your_platform.py`:
```python
from src.vcs.base import BaseVCSAdapter

class YourPlatformAdapter(BaseVCSAdapter):
    def get_repository_path(self) -> str:
        pass
    
    def commit_file(self, file_path: str, message: str):
        pass
```

## Security Considerations

- Code never leaves your VCS environment
- Runs on your own runners/agents
- Supports secret management via environment variables
- OpenAPI specs are committed to your repository under your control

## License

MIT License - See LICENSE file for details

## Contributing

Contributions are welcome! Please read CONTRIBUTING.md for guidelines.

