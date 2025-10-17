# Contributing to Code Discovery

Thank you for your interest in contributing to Code Discovery! This document provides guidelines for contributing to the project.

## Development Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/codediscovery.git
   cd codediscovery
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   pip install -e .
   ```

4. **Run tests**
   ```bash
   pytest
   ```

## Project Structure

```
codediscovery/
├── src/
│   ├── core/           # Core models and orchestrator
│   ├── vcs/            # VCS adapters (GitHub, GitLab, etc.)
│   ├── detectors/      # Framework detectors
│   ├── parsers/        # API parsers for each framework
│   ├── generators/     # OpenAPI generator
│   └── utils/          # Utilities (config, API client)
├── tests/              # Test files
├── .github/            # GitHub Actions workflows
├── .gitlab-ci.yml      # GitLab CI configuration
├── .circleci/          # CircleCI configuration
├── Jenkinsfile         # Jenkins pipeline
└── .harness/           # Harness CI configuration
```

## Adding a New Framework

### 1. Create a Detector

Create a new detector in `src/detectors/your_framework.py`:

```python
from .base import BaseDetector
from ..core.models import FrameworkType

class YourFrameworkDetector(BaseDetector):
    def detect(self) -> bool:
        # Implement detection logic
        return self.check_dependency("requirements.txt", "your-framework")
    
    def get_framework_type(self) -> FrameworkType:
        return FrameworkType.YOUR_FRAMEWORK
    
    def get_source_paths(self) -> List[Path]:
        # Return paths to source files
        return [self.repo_path / "src"]
```

### 2. Create a Parser

Create a new parser in `src/parsers/your_framework_parser.py`:

```python
from .base import BaseParser
from ..core.models import DiscoveryResult, FrameworkType

class YourFrameworkParser(BaseParser):
    def parse(self) -> DiscoveryResult:
        # Implement parsing logic
        endpoints = []
        # ... parse source files
        return DiscoveryResult(
            framework=FrameworkType.YOUR_FRAMEWORK,
            endpoints=endpoints,
        )
    
    def get_framework_type(self) -> FrameworkType:
        return FrameworkType.YOUR_FRAMEWORK
```

### 3. Register in Orchestrator

Update `src/core/orchestrator.py` to include your framework:

```python
FRAMEWORK_HANDLERS = {
    # ... existing frameworks
    FrameworkType.YOUR_FRAMEWORK: (YourFrameworkDetector, YourFrameworkParser),
}
```

### 4. Add to Models

Update `src/core/models.py` to add your framework type:

```python
class FrameworkType(str, Enum):
    # ... existing frameworks
    YOUR_FRAMEWORK = "your-framework"
```

## Adding a New VCS Platform

### 1. Create an Adapter

Create a new adapter in `src/vcs/your_platform.py`:

```python
from .base import BaseVCSAdapter
from ..core.models import VCSContext

class YourPlatformAdapter(BaseVCSAdapter):
    def detect_platform(self) -> bool:
        return os.getenv("YOUR_PLATFORM_CI") == "true"
    
    def get_context(self) -> VCSContext:
        # Return platform context
        pass
    
    # Implement other required methods...
```

### 2. Register in Factory

Update `src/vcs/factory.py`:

```python
from .your_platform import YourPlatformAdapter

class VCSAdapterFactory:
    ADAPTERS = [
        # ... existing adapters
        YourPlatformAdapter,
    ]
```

## Code Style

- Follow PEP 8 style guide
- Use type hints for function parameters and return values
- Write docstrings for all public functions and classes
- Keep functions focused and small
- Use meaningful variable names

## Testing

- Write unit tests for new features
- Ensure all tests pass before submitting PR
- Aim for good test coverage
- Test edge cases and error conditions

## Pull Request Process

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Run tests and linters
5. Commit your changes (`git commit -m 'Add amazing feature'`)
6. Push to your fork (`git push origin feature/amazing-feature`)
7. Open a Pull Request

### PR Guidelines

- Provide a clear description of the changes
- Reference any related issues
- Include examples if adding new features
- Update documentation as needed
- Ensure CI/CD passes

## Code Review

All submissions require review. We use GitHub pull requests for this purpose.

## Questions?

Feel free to open an issue for:
- Bug reports
- Feature requests
- Questions about the code
- Suggestions for improvements

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

