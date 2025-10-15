ARG PYTHON_VERSION=3.11
FROM python:${PYTHON_VERSION}-slim AS app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

ARG DJANGO_VERSION=5.2.*
ENV DJANGO_VERSION=${DJANGO_VERSION}

COPY . /app/
RUN pip install -r requirements.txt

CMD ["sh", "-c", "python manage.py migrate && python manage.py runserver 0.0.0.0:8080"]

FROM app AS instrumented-app

RUN mkdir /tmp/logs

RUN apt-get update && apt-get install -y build-essential git

RUN python manage.py makemigrations testapp
RUN python manage.py migrate
RUN DJANGO_SUPERUSER_PASSWORD=password python manage.py createsuperuser --noinput --username admin --email user@example.com

ENV CONTRAST__AGENT__LOGGER__PATH=/tmp/logs/agent.log
ENV CONTRAST__AGENT__LOGGER__LEVEL=DEBUG
ENV CONTRAST__REPORTING__LOGGING__FILE_DIRECTORY=/tmp/logs
ENV CONTRAST__REPORTING__LOGGING__LEVEL=TRACE

CMD ["sh", "-c", "pip install /agent && contrast-python-run -- python manage.py runserver 0.0.0.0:8080 | tee /tmp/logs/app.log"]
