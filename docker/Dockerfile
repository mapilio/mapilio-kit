FROM ubuntu:20.04

WORKDIR /app

# Update and install necessary dependencies
RUN apt-get update && \
    DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
    python3 \
    python3-pip \
    git \
    bash \
    curl \
    make \
    libjpeg-dev \
    libc-dev \
    libpng-dev \
    libtiff-dev \
    libfftw3-dev \
    ffmpeg \
    exiftool \
    wget \
    && rm -rf /var/lib/apt/lists/*

RUN apt update && apt install build-essential -y make

# Set up the environment and directories
RUN set -e \
    && mkdir -p /app/bin \
    && mkdir -p /app/dependencies

# Clone the max2sphere-batch repository
RUN git -C /app/dependencies clone https://github.com/mcvarer/max2sphere-batch

# Build max2sphere-batch
RUN make -C /app/dependencies/max2sphere-batch -j4

# Copy the max2sphere-batch binary
RUN cp /app/dependencies/max2sphere-batch/MAX2spherebatch /app/bin/

RUN python3 -m pip install --upgrade git+https://github.com/mapilio/mapilio-kit
