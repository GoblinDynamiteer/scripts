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
RUN python3 -m pip install aiofiles
RUN python3 -m pip install jinja2
RUN python3 -m pip install pyfiglet
EXPOSE 8000/tcp
COPY . /scripts
WORKDIR /scripts
ENTRYPOINT ["python3", "-u", "ripper_scheduler.py", "--web", "--verbose"]
