ARG RENKU_BASE_IMAGE=renku/renkulab-py:3.10-59fcea4
########################################################
#        Renku install section - do not edit           #

FROM ${RENKU_BASE_IMAGE} as builder

USER root

# RENKU_VERSION determines the version of the renku CLI
# that will be used in this image. To find the latest version,
# visit https://pypi.org/project/renku/#history.
ARG RENKU_VERSION=2.7.0

# Install renku from pypi or from github if a dev version
RUN if [ -n "$RENKU_VERSION" ] ; then \
        source .renku/venv/bin/activate ; \
        currentversion=$(renku --version) ; \
        if [ "$RENKU_VERSION" != "$currentversion" ] ; then \
            pip uninstall renku -y ; \
            gitversion=$(echo "$RENKU_VERSION" | sed -n "s/^[[:digit:]]\+\.[[:digit:]]\+\.[[:digit:]]\+\(rc[[:digit:]]\+\)*\(\.dev[[:digit:]]\+\)*\(+g\([a-f0-9]\+\)\)*\(+dirty\)*$/\4/p") ; \
            if [ -n "$gitversion" ] ; then \
                pip install --no-cache-dir --force "git+https://github.com/SwissDataScienceCenter/renku-python.git@$gitversion" ;\
            else \
                pip install --no-cache-dir --force renku==${RENKU_VERSION} ;\
            fi \
        fi \
    fi
#             End Renku install section                #

USER root

# install juicefs
COPY juicefs /usr/bin/

RUN cd /usr/bin ; wget https://github.com/filebrowser/filebrowser/releases/download/v2.27.0/linux-amd64-filebrowser.tar.gz ; tar xvfz linux-amd64-filebrowser.tar.gz filebrowser ; rm linux-amd64-filebrowser.tar.gz


USER ${NB_USER}

########################################################

FROM ${RENKU_BASE_IMAGE}

USER root
COPY --from=builder /usr/local /usr/local
COPY --from=builder /usr/bin/filebrowser /usr/bin/filebrowser
COPY ./sudoers.apt /etc/sudoers.d/apt
RUN chmod go-rwx /etc/sudoers.d/apt
RUN apt-get update && apt-get install -y --no-install-recommends apt-utils emacs-nox libgl1 file xvfb libgl1-mesa-glx libgl1-mesa-dev libglu1-mesa-dev ffmpeg s3fs fuse libpq-dev python3-dev python3-webdav zip unzip lsof gnuplot rubber texlive-latex-extra gfortran ghostscript poppler-utils htop && apt -y clean && rm -rf /var/lib/apt/lists/*

COPY env-vars.sh /etc/profile.d/
RUN chmod +x /etc/profile.d/env-vars.sh
RUN echo "source /etc/profile.d/env-vars.sh" >> /etc/bash.bashrc

COPY entrypoint.sh /entrypoint.sh
RUN cat /entrypoint.sh

USER ${NB_USER}

COPY environment.yml /tmp/

RUN mamba env update -q -f /tmp/environment.yml && \
    mamba clean -y --all && \
    mamba env export -n "root" && \
    rm -rf ${HOME}/.renku/venv

COPY --from=builder ${HOME}/.renku/venv ${HOME}/.renku/venv

ARG SOLIDIPES_VERSION=main
RUN cd /tmp && git clone https://gitlab.com/solidipes/solidipes.git && cd /tmp/solidipes && git checkout ${SOLIDIPES_VERSION} && /opt/conda/bin/pip install --no-cache-dir /tmp/solidipes && rm -r /tmp/solidipes

# install the python dependencies
RUN /opt/conda/bin/pip list
COPY filebrowser.db /tmp/

RUN /opt/conda/bin/pip list


COPY .streamlit ${HOME}/.streamlit/
COPY jupyter_notebook_config.py ${HOME}/.jupyter/
LABEL org.opencontainers.image.source="https://gitlab.com/solidipes/solidipes/-/blob/main/docker/Dockerfile"
