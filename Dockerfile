FROM ubuntu:22.04 as base

# Install Nuclei and other dependencies
RUN apt-get update && apt-get install -y wget unzip bash
RUN wget https://github.com/projectdiscovery/nuclei/releases/download/v3.3.0/nuclei_3.3.0_linux_amd64.zip
RUN unzip nuclei_3.3.0_linux_amd64.zip && mv nuclei /usr/local/bin/nuclei && rm nuclei_3.3.0_linux_amd64.zip

# Install Python and dependencies
RUN apt-get -y install python3.11 python3.11-dev python3-pip wget zip
RUN python3.11 -m pip install --upgrade pip

# Install Python virtual environment and set it up
RUN python3.11 -m pip install virtualenv
RUN python3.11 -m virtualenv /venv
RUN /venv/bin/pip install --upgrade pip

# Install required Python packages
COPY req.txt /req.txt
RUN /venv/bin/pip install -r /req.txt

# Copy Python agent files
COPY agent /app/agent
WORKDIR /app

# Set PYTHONPATH
ENV PYTHONPATH=/app

CMD ["/venv/bin/python3.11", "/app/agent/main.py"]
