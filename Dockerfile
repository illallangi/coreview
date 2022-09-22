FROM docker.io/library/python:3.10.7-alpine AS base

FROM base as builder

RUN apk add gcc musl-dev libffi-dev openssl-dev
RUN mkdir /install
WORKDIR /install

COPY requirements.txt /requirements.txt

RUN python3 -m pip install --prefix=/install -r /requirements.txt

FROM base
ENV FLASK_APP illallangi.coreview
WORKDIR /project
COPY --from=builder /install /usr/local
ADD . /project

ENTRYPOINT ["python", "-m", "flask", "run", "--host=0.0.0.0"]
