ARG PYTHON_VERSION=latest
FROM python:${PYTHON_VERSION}

# Install non-Python dependencies
RUN apt update && apt install -y --no-install-recommends \
	firefox-esr \
	libgl1 \
    libjpeg-dev \
	xvfb \
	&& rm -rf /var/lib/apt/lists/*

# Install Python dependencies
ENV PIP_DISABLE_PIP_VERSION_CHECK=1 \
	PIP_NO_CACHE_DIR=1
WORKDIR /app
COPY . /app
RUN pip install -e .[test]
RUN rm -rf /app/* /app/.[!.]*

# Uninstall Solidipes and plugins
RUN pip list --format=freeze | grep ^solidipes | cut -d'=' -f1 | xargs -n1 pip uninstall -y
