FROM python:3

COPY . /app
WORKDIR /app

RUN pip install pipenv

RUN pipenv install --system

#Run Postgres Locally 
RUN apt-get update && apt-get install -y postgresql

CMD ["python", "run.py"]