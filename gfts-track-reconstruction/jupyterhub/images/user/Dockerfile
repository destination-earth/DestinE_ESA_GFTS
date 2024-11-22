# trigger rebuild: 2024-11-22
FROM quay.io/pangeo/pangeo-notebook:2024.08.18
# Install fusermount3 command and open GL library
USER root
RUN apt-get update && apt-get install -y fuse3 libgl1 xvfb

USER $NB_USER
# install some extra packages
# first, install conda packages from conda-requirements.txt
COPY conda-requirements.txt /tmp/conda-requirements.txt
RUN mamba install -y -n notebook --file /tmp/conda-requirements.txt \
 && mamba clean --all -y

# next pip pacakges from requirements.txt
COPY requirements.txt /tmp/requirements.txt
ARG PIP_CACHE_DIR=/tmp/pip-cache
RUN --mount=type=cache,target=$PIP_CACHE_DIR pip install --no-cache -r /tmp/requirements.txt

# disable "Jupyter news" pop-up
RUN jupyter labextension disable "@jupyterlab/apputils-extension:announcements"

WORKDIR /home/$NB_USER
COPY jupyter_server_config.py /etc/jupyter/jupyter_server_config.py
