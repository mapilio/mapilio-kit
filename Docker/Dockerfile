FROM ubuntu:20.04

ENV DEBIAN_FRONTEND noninteractive

ARG DATASET_PATH
ARG USER_NAME
ARG USER_EMAIL
ARG USER_PASSWORD

WORKDIR /mapilio_kit

RUN apt-get clean
RUN apt-get update -y && apt-get install -y python3 python3-pip git && apt-get install -y --no-install-recommends ffmpeg
RUN apt-get install exiftool -y
RUN apt-get install libjpeg-turbo8-dev
RUN apt-get install wget

RUN python3 -m pip install --upgrade git+https://github.com/mapilio/mapilio-kit

RUN set -e && mkdir -p bin && mkdir -p dependencies

RUN git -C dependencies  clone https://github.com/mcvarer/max2sphere-batch

RUN make -C dependencies/max2sphere-batch -j

RUN cp dependencies/max2sphere-batch/MAX2spherebatch bin/

RUN set -e && mkdir -p datasets

COPY $DATASET_PATH /mapilio_kit/datasets

RUN mapilio_kit --version
RUN mapilio_kit authenticate --user_name=$USER_NAME --user_email=$USER_EMAIL --user_password=$USER_PASSWORD
