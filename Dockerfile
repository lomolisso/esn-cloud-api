FROM python:3.10

# requirements for app are installed
COPY ./requirements.txt /tmp/requirements.txt
RUN pip3 install --upgrade pip
RUN pip install -r /tmp/requirements.txt

# run backend app
WORKDIR /app
EXPOSE $CLOUD_API_PORT
CMD uvicorn app.main:app --host 0.0.0.0 --port $CLOUD_API_PORT --reload