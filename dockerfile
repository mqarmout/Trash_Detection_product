FROM python:3.10 as base

ADD . /backend
WORKDIR /backend

RUN pip install -r requirements.txt

ENTRYPOINT ["python"]

CMD ["app.py"]