# E2E Test Environment for mcpi
#
# Provides complete testing environment with:
# - Python 3.12
# - Node.js 20 (npm, npx)
# - uv package manager
# - Isolated home directory
#
# Build: docker build -f e2e-tests/Dockerfile -t mcpi-e2e .
# Run: docker run --rm -e MCPI_E2E_MODE=1 mcpi-e2e

FROM python:3.12-slim

# System dependencies
RUN apt-get update && apt-get install -y \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Node.js 20 LTS
RUN curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs \
    && npm install -g npm@latest

# uv package manager
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.local/bin:$PATH"

# Create non-root test user
RUN useradd -m -s /bin/bash testuser

# Switch to test user
USER testuser
WORKDIR /home/testuser

# Create Claude Code directory structure (mimics real environment)
RUN mkdir -p \
    ~/.claude \
    ~/.config/claude \
    ~/.local/bin

# Copy mcpi source
COPY --chown=testuser:testuser . /home/testuser/mcpi
WORKDIR /home/testuser/mcpi

# Install mcpi and dependencies
RUN /root/.local/bin/uv sync --dev

# Set environment
ENV MCPI_E2E_MODE=1
ENV PATH="/home/testuser/.local/bin:$PATH"

# Default command runs e2e tests
ENTRYPOINT ["/root/.local/bin/uv", "run", "pytest"]
CMD ["e2e-tests/", "-v", "--tb=short"]
