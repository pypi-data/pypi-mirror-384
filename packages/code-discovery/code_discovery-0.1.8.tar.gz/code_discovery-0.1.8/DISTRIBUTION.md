# Distribution Guide for Code Discovery

This guide explains how to distribute Code Discovery to your customers across different deployment models.

## Distribution Options

### 1. 📦 Python Package (PyPI)

**Best for**: Customers who want to install via pip

#### Setup

1. **Prepare for PyPI**:
```bash
# Install build tools
pip install build twine

# Build the package
python -m build

# Test on TestPyPI first
twine upload --repository testpypi dist/*

# Upload to PyPI
twine upload dist/*
```

2. **Customer Installation**:
```bash
pip install code-discovery
code-discovery --repo-path .
```

3. **Update `setup.py`** for proper packaging:
```python
setup(
    name="code-discovery",
    version="0.1.0",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        # ... dependencies from requirements.txt
    ],
    entry_points={
        "console_scripts": [
            "code-discovery=src.main:main",
        ],
    },
)
```

---

### 2. 🐳 Docker Container

**Best for**: Consistent execution across all environments

#### Create Dockerfile

```dockerfile
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    default-jdk \
    wget \
    && rm -rf /var/lib/apt/lists/*

# Install .NET (optional, for .NET projects)
RUN wget https://dot.net/v1/dotnet-install.sh && \
    chmod +x dotnet-install.sh && \
    ./dotnet-install.sh --channel 8.0 && \
    rm dotnet-install.sh

ENV PATH="$PATH:/root/.dotnet"

# Set working directory
WORKDIR /app

# Copy application
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ ./src/
COPY setup.py .

# Install the package
RUN pip install -e .

# Set entrypoint
ENTRYPOINT ["python", "-m", "src.main"]
```

#### Build and Push

```bash
# Build
docker build -t yourcompany/code-discovery:latest .

# Test locally
docker run -v $(pwd):/workspace yourcompany/code-discovery --repo-path /workspace

# Push to registry
docker push yourcompany/code-discovery:latest

# Or push to GitHub Container Registry
docker tag yourcompany/code-discovery:latest ghcr.io/yourcompany/code-discovery:latest
docker push ghcr.io/yourcompany/code-discovery:latest
```

#### Customer Usage

**GitHub Actions**:
```yaml
- name: Run API Discovery
  run: |
    docker run -v ${{ github.workspace }}:/workspace \
      yourcompany/code-discovery:latest --repo-path /workspace
```

**GitLab CI**:
```yaml
api-discovery:
  image: yourcompany/code-discovery:latest
  script:
    - code-discovery --repo-path .
```

---

### 3. 🔌 GitHub App/Action

**Best for**: Native GitHub integration

#### Option A: GitHub Action (Recommended)

1. **Create action.yml**:
```yaml
name: 'API Discovery'
description: 'Automatically discover and document API endpoints'
author: 'Your Company'

branding:
  icon: 'search'
  color: 'blue'

inputs:
  repo-path:
    description: 'Path to repository'
    required: false
    default: '.'
  
  config-path:
    description: 'Path to config file'
    required: false
    default: '.codediscovery.yml'
  
  output-format:
    description: 'Output format (yaml/json)'
    required: false
    default: 'yaml'
  
  auto-commit:
    description: 'Auto-commit the spec'
    required: false
    default: 'true'

runs:
  using: 'docker'
  image: 'Dockerfile'
  args:
    - '--repo-path'
    - ${{ inputs.repo-path }}
    - '--config'
    - ${{ inputs.config-path }}
    - '--format'
    - ${{ inputs.output-format }}
```

2. **Publish to GitHub Marketplace**:
   - Create a public repository
   - Add the action.yml
   - Create a release
   - Publish to Marketplace

3. **Customer Usage**:
```yaml
- name: Discover APIs
  uses: yourcompany/code-discovery-action@v1
  with:
    repo-path: '.'
    output-format: 'yaml'
    auto-commit: 'true'
  env:
    API_DISCOVERY_TOKEN: ${{ secrets.API_DISCOVERY_TOKEN }}
```

#### Option B: GitHub App

1. **Register GitHub App**:
   - Go to GitHub Settings → Developer settings → GitHub Apps
   - Create new app with permissions:
     - Repository contents: Read & Write
     - Pull requests: Read & Write
   - Generate private key

2. **Deploy webhook handler** (separate service needed)

---

### 4. 🦊 GitLab Template Project

**Best for**: GitLab users

#### Create Template Repository

1. **Create a GitLab template project**:
```yaml
# .gitlab-ci.yml
include:
  - remote: 'https://gitlab.com/yourcompany/code-discovery-template/-/raw/main/api-discovery.yml'

api_discovery:
  extends: .api-discovery
  variables:
    API_DISCOVERY_TOKEN: $API_DISCOVERY_TOKEN
```

2. **Publish template**:
```yaml
# api-discovery.yml (in template repo)
.api-discovery:
  image: yourcompany/code-discovery:latest
  stage: discover
  script:
    - code-discovery
  artifacts:
    paths:
      - openapi-spec.*
```

3. **Customer Usage**:
   - Import template project
   - Configure variables
   - Run pipeline

---

### 5. 🌐 SaaS / Managed Service

**Best for**: Customers who don't want to self-host

#### Architecture

```
Customer Repo → Webhook → Your Service → Worker → Generate Spec → Push to Repo
```

#### Components Needed

1. **API Gateway/Webhook Receiver**:
```python
# webhook_handler.py
from fastapi import FastAPI, BackgroundTasks
from src.core.orchestrator import Orchestrator

app = FastAPI()

@app.post("/webhook/github")
async def github_webhook(payload: dict, background_tasks: BackgroundTasks):
    # Verify signature
    # Queue job
    background_tasks.add_task(process_repository, payload)
    return {"status": "queued"}

async def process_repository(payload: dict):
    # Clone repo (in secure sandbox)
    # Run orchestrator
    # Push results back
    pass
```

2. **Job Queue** (Celery, RQ, or cloud-native):
```python
from celery import Celery
from src.core.orchestrator import Orchestrator

celery = Celery('tasks', broker='redis://localhost:6379')

@celery.task
def discover_apis(repo_url, branch, commit_sha):
    # Clone to temp directory
    # Run discovery
    # Commit results
    pass
```

3. **Deployment**:
   - Deploy on AWS/GCP/Azure
   - Use Kubernetes for scaling
   - Secure sandboxing for code execution

#### Customer Onboarding

1. **Sign up page** → Create account
2. **Connect VCS** → OAuth integration
3. **Select repositories** → Enable discovery
4. **Configure webhooks** → Auto-setup
5. **Done** → Automatic discovery on every push

---

### 6. 📋 Installation Script

**Best for**: Quick setup for any customer

Create an installer script:

```bash
#!/bin/bash
# install-code-discovery.sh

set -e

echo "🔍 Installing Code Discovery..."

# Detect VCS platform
if [ -n "$GITHUB_ACTIONS" ]; then
    VCS="github"
elif [ -n "$GITLAB_CI" ]; then
    VCS="gitlab"
elif [ -n "$CIRCLECI" ]; then
    VCS="circleci"
elif [ -n "$JENKINS_HOME" ]; then
    VCS="jenkins"
else
    VCS="local"
fi

echo "Detected platform: $VCS"

# Install Python dependencies
pip install code-discovery

# Copy appropriate config
case $VCS in
    github)
        mkdir -p .github/workflows
        curl -o .github/workflows/api-discovery.yml \
            https://raw.githubusercontent.com/yourcompany/code-discovery/main/.github/workflows/api-discovery.yml
        ;;
    gitlab)
        curl -o .gitlab-ci.yml \
            https://raw.githubusercontent.com/yourcompany/code-discovery/main/.gitlab-ci.yml
        ;;
    circleci)
        mkdir -p .circleci
        curl -o .circleci/config.yml \
            https://raw.githubusercontent.com/yourcompany/code-discovery/main/.circleci/config.yml
        ;;
    jenkins)
        curl -o Jenkinsfile \
            https://raw.githubusercontent.com/yourcompany/code-discovery/main/Jenkinsfile
        ;;
    local)
        echo "Run: code-discovery --repo-path ."
        ;;
esac

# Create example config
curl -o .codediscovery.yml \
    https://raw.githubusercontent.com/yourcompany/code-discovery/main/.codediscovery.example.yml

echo "✅ Installation complete!"
echo "Next steps:"
echo "1. Edit .codediscovery.yml"
echo "2. Set API_DISCOVERY_TOKEN environment variable (if using external API)"
echo "3. Commit and push to trigger discovery"
```

**Customer usage**:
```bash
curl -sSL https://install.code-discovery.io | bash
```

---

### 7. 🏢 Enterprise Distribution

**Best for**: Large enterprise customers

#### Self-Hosted Options

1. **Private PyPI Server**:
```bash
# Host your own PyPI
pip install pypiserver
pypi-server -p 8080 ./packages

# Customer installs from your server
pip install --index-url http://your-pypi-server:8080 code-discovery
```

2. **Private Container Registry**:
```bash
# Host on customer's infrastructure
docker tag code-discovery customer-registry.internal/code-discovery:latest
docker push customer-registry.internal/code-discovery:latest
```

3. **Air-gapped Installation**:
```bash
# Create offline bundle
pip download -r requirements.txt -d ./offline-packages
tar -czf code-discovery-offline.tar.gz src/ offline-packages/ setup.py

# Customer installation
tar -xzf code-discovery-offline.tar.gz
pip install --no-index --find-links=./offline-packages -r requirements.txt
pip install -e .
```

---

## Distribution Checklist

### Pre-Distribution

- [ ] Complete all unit tests
- [ ] Security audit completed
- [ ] Documentation finalized
- [ ] License file included
- [ ] Version numbers consistent
- [ ] Changelog created

### Package Distribution

- [ ] PyPI package published
- [ ] Docker images built and pushed
- [ ] GitHub Action published to Marketplace
- [ ] Documentation website deployed
- [ ] Example repositories created

### Customer Onboarding

- [ ] Quick start guide available
- [ ] Video tutorials created
- [ ] Support channels established
- [ ] Pricing/licensing decided
- [ ] Terms of service created

### Post-Distribution

- [ ] Monitor usage and errors
- [ ] Collect customer feedback
- [ ] Regular updates and patches
- [ ] Security advisories process
- [ ] Community building

---

## Recommended Approach

For most customers, we recommend a **hybrid approach**:

1. **Primary**: Docker container + GitHub Action/GitLab template
   - Easy to use
   - Consistent across platforms
   - No installation hassle

2. **Secondary**: PyPI package for advanced users
   - Flexibility for customization
   - Integration into existing workflows

3. **Enterprise**: Self-hosted + private registry
   - Full control
   - Air-gapped support
   - Custom branding

---

## Monetization Options

### Free Tier
- Basic framework support
- Community support
- Public repositories only

### Pro Tier ($X/month)
- All frameworks
- Private repositories
- Priority support
- External API integration

### Enterprise Tier (Custom pricing)
- Self-hosted
- Custom frameworks
- SLA guarantees
- Dedicated support
- Custom integrations

---

## Support & Updates

### Documentation
- Host on: docs.code-discovery.io
- Include: API reference, examples, troubleshooting

### Updates
- Semantic versioning
- Release notes for each version
- Automated update notifications

### Support Channels
- GitHub Issues (community)
- Email support (paid)
- Slack/Discord community
- Stack Overflow tag

---

## Legal Considerations

1. **License**: MIT (already included)
2. **Terms of Service**: Create for SaaS offering
3. **Privacy Policy**: If collecting any data
4. **Security**: Responsible disclosure policy
5. **Export Compliance**: Check if applicable

---

## Next Steps

1. **Choose distribution method(s)** based on target market
2. **Set up infrastructure** (PyPI, Docker Hub, etc.)
3. **Create customer onboarding flow**
4. **Launch marketing website**
5. **Announce on relevant channels**

For questions or assistance, contact: support@code-discovery.io

