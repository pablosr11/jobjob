FROM python:buster
RUN pip install uvicorn fastapi feedparser requests sqlalchemy psycopg2 python-multipart lxml
WORKDIR /home/ubuntu/jobjob
CMD ["uvicorn", "spider_app.spider_api:app",  "--host", "0.0.0.0", "--port", "8001", "--reload"]

# FROM python:buster
# RUN pip install uvicorn
# COPY ./spider_app
# CMD /bin/bash -c 'uvicorn uvicorn spider_app.spider_api:app --host 0.0.0.0 --port 8001 --reload'


# workdir?
# build environment