# VeriAgent Docker Image
# Based on picker base image with verification tools
FROM ghcr.io/xs-mlvp/picker:latest

# The picker base image already provides Node.js, npm, Python 3.11, and pip.
USER root
ARG OPENAI_CODEX_REPO="https://github.com/openai/codex"
ARG OPENAI_CODEX_REF="main"
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
    PYTHONPATH=/workspace/VeriAgent \
    CODEX_BIN=/usr/local/bin/codex

# Install VeriAgent, dependencies, and the OpenAI Codex app-server SDK.
RUN python3 -m pip install . && \
    git clone --depth 1 --branch "$OPENAI_CODEX_REF" "$OPENAI_CODEX_REPO" /opt/openai-codex && \
    python3 -m pip install -e /opt/openai-codex/sdk/python && \
    python3 -c "import codex_app_server; print('ok: codex_app_server import')" && \
    python3 -m pip install -r requirements-formal.txt && \
    node --version && npm --version && python3 --version && veriagent --check

# Default command: interactive shell
CMD ["/bin/bash"]
