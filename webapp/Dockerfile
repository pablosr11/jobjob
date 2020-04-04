FROM python:buster
RUN pip install uvicorn fastapi feedparser requests sqlalchemy psycopg2 python-multipart lxml
WORKDIR /home/ubuntu/jobjob
CMD ["uvicorn", "webapp.main:app",  "--host", "0.0.0.0", "--port", "8000", "--reload"]
