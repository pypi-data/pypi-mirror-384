# Build stage
FROM python:3.12-slim AS builder

# Set working directory
WORKDIR /app

# Copy only the files needed for installation
COPY pyproject.toml .
COPY src/ src/
COPY README.md .

# Install build dependencies and the package
RUN pip install --no-cache-dir build && \
    pip wheel --no-deps --wheel-dir dist .

# Runtime stage
FROM python:3.12-slim

# Create a non-root user
RUN useradd -m -u 1000 pybedca

# Set working directory
WORKDIR /app

# Copy only the built wheel from builder
COPY --from=builder /app/dist/*.whl .

# Install runtime dependencies and the package
RUN pip install --no-cache-dir ./*.whl && \
    rm -f ./*.whl && \
    chown -R pybedca:pybedca /app

# Switch to non-root user
USER pybedca

# Expose MCP server port (if needed)
# EXPOSE 3000

# Run MCP server
CMD ["python", "-m", "pybedca.mcp_server"]
