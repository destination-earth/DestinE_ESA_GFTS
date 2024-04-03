FROM quay.io/pangeo/pangeo-notebook:2024.03.22

# install some extra things with requirements.txt
COPY requirements.txt /tmp/requirements.txt
ENV PIP_CACHE_DIR=/tmp/pip-cache
RUN  --mount=type=cache,target=$PIP_CACHE_DIR pip install --no-cache -r /tmp/requirements.txt

# disable "Jupyter news" pop-up
RUN jupyter labextension disable "@jupyterlab/apputils-extension:announcements"

WORKDIR /home/$NB_USER
COPY jupyter_server_config.py /etc/jupyter/jupyter_server_config.py
