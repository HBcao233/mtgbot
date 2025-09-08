FROM python:3.9.19
RUN apt-get update && apt-get install ffmpeg -y
RUN mkdir /tgbot
WORKDIR /tgbot
COPY requirements.txt /tgbot
RUN python3 -m pip install -r requirements.txt
# COPY . /tgbot
CMD ["python3", "/tgbot/main.py"] 