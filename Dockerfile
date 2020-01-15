FROM python:3.8.1-alpine3.10
COPY ./src /root
WORKDIR /root
RUN pip install rpyc toml
VOLUME /data

CMD ["python"]