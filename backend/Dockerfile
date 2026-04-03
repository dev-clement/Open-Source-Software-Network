FROM python:3.12-slim

# Install system dependencies for Pixi and PostgreSQL
RUN apt-get update && apt-get install -y \
    curl \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Install Pixi
RUN curl -fsSL https://pixi.dev/install.sh | sh
# Add pixi to the path
ENV PATH="/root/.pixi/bin:$PATH"

# Set working directory
WORKDIR /app

# Copy only the manifest fils first to leverage Docker cache
COPY pixi.toml pixi.lock* ./

# Install dependencies using Pixi
# --frozen ensures that we use the exact versions from pixi.lock
RUN pixi install --frozen

# Copy the rest of the application code
COPY . .

# Use 'pixi run' to start the application using the task defined in pixi.toml
CMD ["pixi", "run", "start"]