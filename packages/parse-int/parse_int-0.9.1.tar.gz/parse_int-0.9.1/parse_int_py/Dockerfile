FROM docker.io/library/rust:latest

# Install necessary dependencies for building wheels
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    python3-venv \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install maturin for building Python wheels from Rust projects
# RUN pip3 install maturin
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
# Make ~/.local/bin available to all processes/shells
ENV PATH="/root/.local/bin:${PATH}"

# Also add a profile script so interactive/login shells pick it up
RUN mkdir -p /etc/profile.d && \
    echo 'export PATH="$HOME/.local/bin:$PATH"' > /etc/profile.d/local_bin.sh && \
    chmod +x /etc/profile.d/local_bin.sh

# Set the working directory
WORKDIR /app

# Copy the parent directory and the parse_int directory
COPY . ./
# COPY ../parse_int ./parse_int/

# Make sure the build_wheels.sh script is executable
# RUN chmod +x parse_int_py/build_wheels.sh

# Run the build script
CMD ["./parse_int_py/build_wheels.sh"]
