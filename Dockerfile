# Can't use python image as this causes errors when installing makemkv
FROM ubuntu:latest

RUN apt-get update
RUN apt-get install -y software-properties-common

RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    python3-venv \
    && apt-get clean

RUN pip3 install --break-system-packages pipenv

RUN add-apt-repository -y ppa:stebbins/handbrake-releases || true
RUN apt-get update
# /usr/bin/HandBrakeCLI is the command line interface for HandBrake
RUN apt-get install -y handbrake-cli

RUN add-apt-repository -y ppa:heyarje/makemkv-beta
RUN apt-get update
RUN apt-get install -y makemkv-bin makemkv-oss

ENV PATH="/usr/bin:${PATH}"

COPY get_movie_info.py .
COPY auto-rip.py .
COPY Pipfile .
COPY Pipfile.lock .

# should use pipenv sync instead (might encounter the env issue)
RUN pipenv requirements > requirements.txt
RUN pip3 install --break-system-packages -r requirements.txt

ENTRYPOINT [ "python3", "auto-rip.py" ]