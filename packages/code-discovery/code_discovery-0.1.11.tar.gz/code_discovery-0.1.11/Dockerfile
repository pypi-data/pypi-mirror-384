FROM python:3.11-slim

# Metadata
LABEL maintainer="Code Discovery Team"
LABEL description="Automatic API discovery and OpenAPI specification generator"
LABEL version="0.1.0"

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    default-jdk \
    wget \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install .NET SDK (for .NET projects)
RUN wget https://dot.net/v1/dotnet-install.sh -O dotnet-install.sh && \
    chmod +x dotnet-install.sh && \
    ./dotnet-install.sh --channel 8.0 && \
    rm dotnet-install.sh

ENV PATH="$PATH:/root/.dotnet"

# Set working directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source
COPY src/ ./src/
COPY setup.py .
COPY README.md .

# Install the package
RUN pip install -e .

# Create workspace directory
WORKDIR /workspace

# Set entrypoint
ENTRYPOINT ["python", "-m", "src.main"]

# Default command (can be overridden)
CMD ["--repo-path", "/workspace"]

