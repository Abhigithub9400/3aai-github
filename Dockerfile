# Use the official Ubuntu 22.04 image as the base
FROM ubuntu:24.04

# Set environment variable to avoid interactive prompts
ENV DEBIAN_FRONTEND=noninteractive

# Set working directory
WORKDIR /app

# Install required system packages and clean up to reduce image size
RUN apt-get update && apt-get install -y \
    software-properties-common \
    && add-apt-repository ppa:deadsnakes/ppa \
    && apt-get update && apt-get install -y \
    curl \
    gcc \
    python3.12 \
    python3.12-venv \
    python3.12-dev \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Create a virtual environment and activate it
RUN python3.12 -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Upgrade pip and install dependencies
COPY ./requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r /app/requirements.txt

# Copy application code
COPY ./chat_bot /app/chat_bot

# Create the "static" directory
RUN mkdir -p /app/static

# Copy the specific `workflow.png` from `chat_bot/static` to `/app/static`
RUN cp /app/chat_bot/static/workflow.png /app/static/

# Set entrypoint and default command
ENTRYPOINT ["python", "chat_bot/main.py", "--environment"]
CMD ["production"]

# Add a health check for container monitoring
HEALTHCHECK --interval=30s \
    --start-period=10s \
    --timeout=3s \
    --retries=3 \
    CMD curl --fail http://localhost:80/ || exit 1

# Expose port
EXPOSE 80