FROM ubuntu:24.04

# Environment variables
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHON_VERSION=3.10.14
ENV PATH="/usr/local/bin:$PATH"
ENV LD_LIBRARY_PATH="/usr/local/lib"

# Install system dependencies
RUN apt update && apt install -y --no-install-recommends \
  build-essential wget curl git pkg-config \
  libssl-dev libbz2-dev libreadline-dev libsqlite3-dev \
  libffi-dev zlib1g-dev liblzma-dev xz-utils \
  libgl1-mesa-dev libgles2-mesa-dev \
  libsdl2-dev libsdl2-image-dev libsdl2-mixer-dev libsdl2-ttf-dev \
  libavdevice-dev libavfilter-dev libopus-dev \
  libasound2-dev libpulse-dev libx11-dev libxcursor-dev libxrandr-dev libxinerama-dev libxi-dev \
  && rm -rf /var/lib/apt/lists/*

# Build and install Python from source
RUN cd /usr/src && \
  wget --no-check-certificate https://www.python.org/ftp/python/3.10.14/Python-3.10.14.tgz && \
  tar xzf Python-${PYTHON_VERSION}.tgz && \
  cd Python-${PYTHON_VERSION} && \
  ./configure --enable-optimizations --enable-shared && \
  make -j$(nproc) && \
  make altinstall

# Upgrade pip and install Python packages
RUN python3.10 -m ensurepip && \
  python3.10 -m pip install --upgrade pip && \
  pip3.10 install --no-cache-dir kivy pillow pyinstaller

# Default working directory
WORKDIR /src

# Entrypoint to use PyInstaller directly
ENTRYPOINT ["pyinstaller"]
