#!/bin/bash

cd /fastapi_service

CHROMEVER=$(google-chrome --product-version | grep -o "[^\.]*" | head -1)
DRIVERVER=$(curl -s "https://chromedriver.storage.googleapis.com/LATEST_RELEASE_$CHROMEVER")

if [[ "$DRIVERVER" == *"NoSuchKey"* ]] || [[ "$DRIVERVER" == "" ]]; then
  CHROMEVER=$(google-chrome --product-version | grep -o "[^\.]*\.[^\.]*\.[^\.]*[^\.]*\.[^\.]*")
  wget -q --continue -P ./chromedriver "https://edgedl.me.gvt1.com/edgedl/chrome/chrome-for-testing/$CHROMEVER/linux64/chromedriver-linux64.zip";
  unzip ./chromedriver/chromedriver*.zip -d ./chromedriver;
  cp ./chromedriver/chromedriver*/chromedriver ./chromedriver; else
  wget -q --continue -P ./chromedriver "https://chromedriver.storage.googleapis.com/$DRIVERVER/chromedriver_linux64.zip";
  unzip ./chromedriver/chromedriver*.zip -d ./chromedriver;
fi

gunicorn main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker --bind=0.0.0.0:8000