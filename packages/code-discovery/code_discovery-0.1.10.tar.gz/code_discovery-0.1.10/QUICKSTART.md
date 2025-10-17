# Quick Start Guide

Get started with Code Discovery in minutes!

## Installation

### Option 1: Install from Source

```bash
git clone https://github.com/yourusername/codediscovery.git
cd codediscovery
pip install -r requirements.txt
python setup.py install
```

### Option 2: Use as a Standalone Tool

```bash
pip install -r requirements.txt
python -m src.main --repo-path /path/to/your/repo
```

## Basic Usage

### 1. Run on Current Directory

```bash
python -m src.main
```

### 2. Run on a Specific Repository

```bash
python -m src.main --repo-path /path/to/repo
```

### 3. Generate JSON Output

```bash
python -m src.main --format json
```

### 4. Dry Run (No Commits)

```bash
python -m src.main --dry-run
```

## Configuration

Create a `.codediscovery.yml` file in your repository root:

```yaml
api_discovery:
  enabled: true
  
  frameworks:
    - spring-boot
    - fastapi
  
  openapi:
    version: "3.0.0"
    output_path: "openapi-spec.yaml"
    output_format: "yaml"
  
  vcs:
    auto_commit: true
    commit_message: "chore: update OpenAPI specification"
```

## Platform-Specific Setup

### GitHub Actions

1. Copy `.github/workflows/api-discovery.yml` to your repository
2. Set up secret: `API_DISCOVERY_TOKEN` (if using external API)
3. Push to trigger the workflow

### GitLab CI

1. Copy `.gitlab-ci.yml` to your repository root
2. Set up CI/CD variable: `API_DISCOVERY_TOKEN`
3. Pipeline runs automatically on push

### CircleCI

1. Copy `.circleci/config.yml` to your repository
2. Set up context: `api-discovery-secrets`
3. Add environment variable: `API_DISCOVERY_TOKEN`

### Jenkins

1. Copy `Jenkinsfile` to your repository
2. Create Jenkins credential: `api-discovery-token`
3. Create a pipeline job pointing to the Jenkinsfile

### Harness

1. Import `.harness/api-discovery-pipeline.yml`
2. Set up secret: `api_discovery_token`
3. Configure connector and codebase

## Example Output

After running Code Discovery, you'll get an OpenAPI specification:

```yaml
openapi: 3.0.0
info:
  title: Discovered API
  version: 1.0.0
paths:
  /api/users:
    get:
      summary: Get all users
      operationId: getUsers
      responses:
        '200':
          description: Successful response
  /api/users/{id}:
    get:
      summary: Get user by ID
      operationId: getUsersId
      parameters:
        - name: id
          in: path
          required: true
          schema:
            type: string
      responses:
        '200':
          description: Successful response
```

## Supported Frameworks

- ✅ Java Spring Boot
- ✅ Java Micronaut
- ✅ Python FastAPI
- ✅ Python Flask
- ✅ ASP.NET Core

## What's Discovered?

Code Discovery automatically extracts:

- ✅ **Endpoints**: All API routes/paths
- ✅ **HTTP Methods**: GET, POST, PUT, DELETE, PATCH
- ✅ **Parameters**: Path, query, header parameters
- ✅ **Request Bodies**: Expected input schemas
- ✅ **Responses**: Status codes and response schemas
- ✅ **Authentication**: Auth requirements per endpoint

## Troubleshooting

### No frameworks detected

Ensure your project has the required dependency files:
- Java: `pom.xml` or `build.gradle`
- Python: `requirements.txt`, `Pipfile`, or `pyproject.toml`
- .NET: `*.csproj` files

### No endpoints found

Make sure your API controllers/routes use standard annotations:
- Spring Boot: `@RestController`, `@GetMapping`, etc.
- Micronaut: `@Controller`, `@Get`, etc.
- FastAPI: `@app.get()`, `@router.post()`, etc.
- Flask: `@app.route()`, `@blueprint.route()`, etc.
- ASP.NET: `[ApiController]`, `[HttpGet]`, etc.

### VCS commit failed

Check:
- Git is configured with user.name and user.email
- You have write permissions to the repository
- The branch exists and is not protected

## Next Steps

1. **Customize Configuration**: Edit `.codediscovery.yml` to match your needs
2. **Set Up CI/CD**: Use the provided platform configurations
3. **External API Integration**: Configure the external API endpoint for notifications
4. **Extend Support**: Add parsers for additional frameworks

## Need Help?

- 📚 [Full Documentation](README.md)
- 🤝 [Contributing Guide](CONTRIBUTING.md)
- 🐛 [Report Issues](https://github.com/yourusername/codediscovery/issues)
- 💬 [Discussions](https://github.com/yourusername/codediscovery/discussions)

