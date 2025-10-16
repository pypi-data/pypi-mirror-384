# Multi-stage Dockerfile for both Node.js and Python MCP Portfolio Server

# =============================================================================
# Node.js Stage
# =============================================================================
FROM node:20-alpine AS nodejs

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm ci --only=production

# Copy source code
COPY src/index.js ./src/
COPY sample-data.json ./

# Create non-root user
RUN addgroup -g 1001 -S nodejs && \
    adduser -S mcp -u 1001

# Change ownership
RUN chown -R mcp:nodejs /app
USER mcp

EXPOSE 3000

CMD ["node", "src/index.js"]

# =============================================================================
# Python Stage
# =============================================================================
FROM python:3.11-slim AS python

WORKDIR /app

# Copy Python project files
COPY pyproject.toml ./
COPY README.md ./
COPY src/mcp_portfolio_server/ ./src/mcp_portfolio_server/
COPY sample-data.json ./

# Install Python dependencies
RUN pip install --no-cache-dir -e .

# Create non-root user
RUN addgroup --gid 1001 python && \
    adduser --disabled-password --gecos '' --uid 1001 --gid 1001 mcp

# Change ownership
RUN chown -R mcp:python /app
USER mcp

EXPOSE 3000

CMD ["python", "-m", "mcp_portfolio_server.server"]

# =============================================================================
# Multi-runtime Stage (Both Node.js and Python)
# =============================================================================
FROM ubuntu:22.04 AS multi

# Install Node.js and Python
RUN apt-get update && apt-get install -y \
    curl \
    python3 \
    python3-pip \
    && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy all source files
COPY package*.json ./
COPY pyproject.toml ./
COPY README.md ./
COPY src/ ./src/
COPY sample-data.json ./

# Install dependencies for both runtimes
RUN npm ci --only=production
RUN pip3 install --no-cache-dir -e .

# Create non-root user
RUN addgroup --gid 1001 mcp && \
    adduser --disabled-password --gecos '' --uid 1001 --gid 1001 mcp

# Change ownership
RUN chown -R mcp:mcp /app
USER mcp

EXPOSE 3000

# Default to Node.js, but can be overridden
CMD ["node", "src/index.js"]