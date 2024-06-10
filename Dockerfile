FROM docker.io/library/python:3.12.4-alpine AS base

FROM base as builder

RUN \
  apk add --no-cache \
    gcc=13.2.1_git20231014-r0 \
    libffi-dev=3.4.4-r3 \
    musl-dev=1.2.4_git20230717-r4 \
  && \
  mkdir /install

WORKDIR /install

COPY requirements.txt /requirements.txt

RUN python3 -m pip install --no-cache-dir --prefix=/install -r /requirements.txt

FROM base
ENV FLASK_APP illallangi.coreview
WORKDIR /project
COPY --from=builder /install /usr/local
COPY . /project

ENTRYPOINT ["python", "-m", "flask", "run", "--host=0.0.0.0"]
