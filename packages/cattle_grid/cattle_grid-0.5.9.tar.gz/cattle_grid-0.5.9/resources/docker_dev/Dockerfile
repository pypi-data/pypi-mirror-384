FROM helgekr/bovine:0.5.18-python3.11


RUN apk add curl git postgresql

ADD requirements.txt /tmp/requirements.txt
ADD *.whl /tmp/

RUN --mount=type=cache,target=/root/.cache/ pip install -r /tmp/requirements.txt
RUN --mount=type=cache,target=/root/.cache/ pip install /tmp/*.whl || true