FROM ubuntu:22.04

USER root
ENV DEBIAN_FRONTEND noninteractive
COPY apt.txt /tmp/apt.txt
RUN rm -vf /etc/apt/apt.conf.d/docker-clean
RUN --mount=type=cache,target=/var/cache/apt apt-get update && apt-get -yq dist-upgrade \
 && apt-get install -yq --no-install-recommends \
    $(cat /tmp/apt.txt | grep -v '^#' | sort) \
 && rm -rf /var/lib/apt/lists/*

RUN echo "en_US.UTF-8 UTF-8" > /etc/locale.gen \
 && locale-gen

ENV NB_UID=1000 \
    NB_USER=user \
    CONDA_DIR=/opt/conda \
    SHELL=/bin/bash \
    LANG=en_US.UTF-8

RUN useradd -m -s /bin/bash -N -u $NB_UID $NB_USER

# setup conda env
ENV PATH=$CONDA_DIR/bin:$PATH
COPY conda-linux-64.lock /tmp/conda.lock
COPY install-miniconda.bash /tmp/install-miniconda.bash
RUN --mount=type=cache,target=/tmp/conda bash /tmp/install-miniconda.bash
COPY condarc $CONDA_DIR/.condarc

USER $NB_UID

# install some extra things with requirements.txt
# COPY requirements.txt /tmp/requirements.txt
# ENV PIP_CACHE_DIR=/tmp/pip-cache
# RUN  --mount=type=cache,target=$PIP_CACHE_DIR pip install --no-cache -r /tmp/requirements.txt

# enable nbdime globally
USER root
RUN nbdime config-git --enable --system
USER $NB_UID

WORKDIR /home/$NB_USER
COPY jupyter_server_config.py /etc/jupyter/jupyter_server_config.py

USER root
# setup entrypoint
RUN ln -s $CONDA_DIR/etc/profile.d/conda.sh /etc/profile.d/conda.sh
ADD entrypoint.sh /usr/local/bin/docker-entrypoint
USER $NB_UID
ENTRYPOINT ["/usr/local/bin/docker-entrypoint"]
CMD ["jupyter", "lab", "--ip=0.0.0.0"]
