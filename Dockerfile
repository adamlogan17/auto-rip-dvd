# Can't use python image as this causes errors when installing makemkv
FROM ubuntu:latest

WORKDIR /code

RUN apt-get update
RUN apt-get install -y software-properties-common

RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    python3-venv \
    && apt-get clean

RUN pip3 install --break-system-packages uv

RUN add-apt-repository -y ppa:stebbins/handbrake-releases || true
RUN apt-get update
RUN apt-get install -y handbrake-cli
ENV HANDBRAKE=/usr/bin/HandBrakeCLI

RUN add-apt-repository -y ppa:heyarje/makemkv-beta
RUN apt-get update
RUN apt-get install -y makemkv-bin makemkv-oss
ENV MAKEMKV=/usr/bin/makemkvcon

ENV PATH="/usr/bin:${PATH}"

COPY src /code/src
COPY pyproject.toml /code/pyproject.toml
COPY uv.lock /code/uv.lock
COPY README.md /code/README.md


# 'uv run --frozen' installs dependencies from uv.lock, without updating them
ENTRYPOINT [ "uv", "run", "--frozen", "auto-rip-dvd" ]

# Below is to keep the container running for debugging purposes, the above line should be commented out when using this
# CMD ["/bin/bash"]