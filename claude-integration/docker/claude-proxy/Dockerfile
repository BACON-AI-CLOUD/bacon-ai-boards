# Claude Code CLI Proxy Service
# Wraps Claude Code CLI for HTTP API access using subscription-based licensing

FROM node:20-slim

# Install Claude Code CLI
RUN npm install -g @anthropic-ai/claude-code

# Create app user
RUN useradd -m -s /bin/bash appuser

# Create app directory
WORKDIR /app

# Copy application files
COPY --chown=appuser:appuser server.js package.json ./

# Install dependencies
RUN npm install

# Switch to app user
USER appuser

# Create Claude config directory
RUN mkdir -p /home/appuser/.claude

# Expose port
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

# Start server
CMD ["node", "server.js"]
