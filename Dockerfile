FROM python:latest

RUN apt update && apt upgrade -y
RUN apt install python3-pip -y
COPY . /TGVCVidioPlayerUB
WORKDIR /TGVCVidioPlayerUB
RUN pip3 install --upgrade pip
RUN pip3 install -U -r requirements.txt
CMD python3 -m bot.py
