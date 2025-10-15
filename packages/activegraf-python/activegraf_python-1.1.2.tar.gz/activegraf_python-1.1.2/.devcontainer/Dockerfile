FROM python:3.12-slim-bookworm

RUN apt-get update && \
    apt-get install -y \
      git \
      gcc \
      g++ \
    && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

RUN python3 -m pip install --upgrade build twine

RUN useradd -u 1000 -m developer

USER developer
