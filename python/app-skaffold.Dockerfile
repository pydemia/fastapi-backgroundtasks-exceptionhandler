FROM --platform=amd64 python:3.10-slim

ENV HOST=0.0.0.0
ENV PORT=8000
ENV DEBUG_PORT=5678

WORKDIR /workdir

COPY ./fastapi_app /workdir/fastapi_app
COPY ./setup.py /workdir/setup.py
COPY ./logging.conf /workdir/logging.conf
COPY ./gunicorn_conf.py /workdir/gunicorn_conf.py
COPY ./requirements.txt /workdir/requirements.txt

RUN pip install -r ./requirements.txt && \
    pip install ./ --no-cache-dir

CMD gunicorn fastapi_app.main:app --reload -k=uvicorn.workers.UvicornWorker --log-config logging.conf -c gunicorn_conf.py
