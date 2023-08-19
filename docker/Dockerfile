FROM tiangolo/uvicorn-gunicorn-fastapi:python3.9

RUN mkdir /fastapi_service

WORKDIR /fastapi_service

COPY requirements.txt /fastapi_service/requirements.txt

RUN pip install -r /fastapi_service/requirements.txt

COPY ../ /fastapi_service

RUN chmod a+x build.sh

RUN apt-get update && \
    apt-get install -y gnupg wget curl unzip --no-install-recommends && \
    wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add - && \
    echo "deb http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google.list && \
    apt-get update -y && \
    apt-get install -y google-chrome-stable
