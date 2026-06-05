# VeriAgent Docker Image
# Based on picker base image with verification tools
FROM ghcr.io/xs-mlvp/picker:latest

# The picker base image already provides Node.js, npm, Python 3.11, and pip.
USER root
ARG CODEX_APP_SERVER_PACKAGE=""
RUN node --version && \
    npm --version && \
    python3 --version && \
    python3 -m pip --version

# Install Code Agent CLIs.
RUN npm install -g @anthropic-ai/claude-code @openai/codex && \
    claude --version && \
    codex --version

# Set working directory
WORKDIR /workspace/VeriAgent

# Copy project files
COPY . .
COPY examples/05-formal/requirements.txt ./requirements-formal.txt

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONPATH=/workspace/VeriAgent

# Install VeriAgent and dependencies into the image.
RUN python3 -m pip install . && \
    if [ -n "$CODEX_APP_SERVER_PACKAGE" ]; then \
      echo "Installing Codex app-server SDK from CODEX_APP_SERVER_PACKAGE"; \
      python3 -m pip install "$CODEX_APP_SERVER_PACKAGE"; \
      python3 -c "import codex_app_server; print('ok: codex_app_server import')"; \
    else \
      echo "CODEX_APP_SERVER_PACKAGE is empty; skipping private Codex app-server SDK install"; \
    fi && \
    python3 -m pip install -r requirements-formal.txt && \
    node --version && npm --version && python3 --version && veriagent --check

# Default command: interactive shell
CMD ["/bin/bash"]
