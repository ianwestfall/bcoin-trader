FROM python:3.10.1-alpine as builder

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV APP_HOME=/home/app/web

RUN mkdir -p $APP_HOME
WORKDIR $APP_HOME

RUN apk update && \
    apk add --no-cache build-base gcc python3-dev libffi-dev brotli

RUN pip install --upgrade pip
RUN pip install pipenv
COPY ./Pipfile .
COPY ./Pipfile.lock .

RUN pipenv lock -r --keep-outdated > requirements.txt
RUN pip wheel --no-cache-dir --no-deps --wheel-dir $APP_HOME/wheels -r requirements.txt

FROM python:3.10.1-alpine

RUN addgroup -S app && adduser -S app -G app

ENV APP_HOME=/home/app/web
RUN mkdir -p $APP_HOME
WORKDIR $APP_HOME

COPY --from=builder $APP_HOME/wheels /wheels
COPY --from=builder $APP_HOME/requirements.txt .
RUN pip install --upgrade pip
RUN pip install --no-cache /wheels/*

COPY . $APP_HOME

RUN chown -R app:app $APP_HOME

ENTRYPOINT [ "python", "bot.py" ]
