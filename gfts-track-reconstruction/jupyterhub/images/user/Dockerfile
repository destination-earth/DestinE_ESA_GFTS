# Use Chainguard's Python dev image as builder (includes shell and apk)
FROM cgr.dev/chainguard/python:latest-dev AS builder

# Set working directory
WORKDIR /app

# Install system dependencies needed for runtime and build
USER root
RUN apk add --no-cache \
    fuse3 \
    mesa-gl \
    xvfb-run \
    bash \
    curl \
    ca-certificates \
    build-base \
    nodejs \
    npm

# Copy requirements files
COPY conda-requirements.txt /tmp/conda-requirements.txt
COPY requirements.txt /tmp/requirements.txt

# Install micromamba (lightweight conda alternative)
RUN curl -Ls https://micro.mamba.pm/api/micromamba/linux-64/latest | tar -xvj -C /usr/local bin/micromamba

# Create conda environment and install packages including jupyterlab
ENV MAMBA_ROOT_PREFIX=/opt/conda
RUN micromamba create -n notebook python=3.11 jupyterlab nodejs -c conda-forge -y && \
    micromamba install -n notebook --file /tmp/conda-requirements.txt -c conda-forge -y && \
    micromamba clean --all -y

# Install pip packages
ARG PIP_CACHE_DIR=/tmp/pip-cache
RUN --mount=type=cache,target=$PIP_CACHE_DIR \
    /opt/conda/envs/notebook/bin/pip install --no-cache-dir -r /tmp/requirements.txt

# Disable JupyterLab announcements (make it optional in case it fails)
RUN /opt/conda/envs/notebook/bin/jupyter labextension disable "@jupyterlab/apputils-extension:announcements" || \
    echo "Warning: Could not disable JupyterLab announcements extension"

# Final stage - use the dev image (which has shell) but cleaned up
FROM cgr.dev/chainguard/python:latest-dev

USER root

# Install only runtime dependencies
RUN apk add --no-cache \
    fuse3 \
    mesa-gl \
    xvfb-run \
    bash \
    nodejs

# Copy conda environment from builder
COPY --from=builder /opt/conda /opt/conda

# Set up non-root user
ENV NB_USER=nonroot
ENV HOME=/home/nonroot
ENV PATH=/opt/conda/envs/notebook/bin:$PATH

# Create home directory with proper permissions
RUN mkdir -p /home/nonroot /etc/jupyter && \
    chown -R nonroot:nonroot /home/nonroot /opt/conda /etc/jupyter

# Copy Jupyter configuration
COPY jupyter_server_config.py /etc/jupyter/jupyter_server_config.py
RUN chown nonroot:nonroot /etc/jupyter/jupyter_server_config.py

# Switch to non-root user
USER nonroot
WORKDIR /home/nonroot

# Set conda environment activation
ENV CONDA_DEFAULT_ENV=notebook
ENV CONDA_PREFIX=/opt/conda/envs/notebook