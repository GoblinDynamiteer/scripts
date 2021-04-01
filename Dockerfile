FROM ubuntu:latest
RUN apt-get -y update
RUN apt-get install python3 -y
RUN apt-get install ffmpeg -y
RUN apt-get install python3-pip -y
RUN apt-get install curl -y
RUN python3 -m pip install uvicorn
RUN python3 -m pip install fastapi
RUN python3 -m pip install youtube_dl
RUN python3 -m pip install requests
RUN python3 -m pip install svtplay-dl
EXPOSE 8000/tcp
COPY . /scripts
CMD python3 -u /scripts/ripper_scheduler.py --web -f --verbose
