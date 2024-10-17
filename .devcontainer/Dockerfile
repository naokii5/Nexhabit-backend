FROM mcr.microsoft.com/devcontainers/python:3.12-bullseye

RUN apt update && apt install -y libxtst6 curl \
    && python3 -m pip install --upgrade pip \
    && pip install poetry


WORKDIR /workspace/
COPY pyproject.toml poetry.lock /workspace/
RUN poetry config virtualenvs.create false \
    && poetry lock \
    && poetry install