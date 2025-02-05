# pull official base image
FROM python:3.12.3-alpine

# set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# set work directory
WORKDIR /backend

RUN apk update
RUN apk add gcc python3-dev musl-dev zlib-dev jpeg-dev

# Install dependencies
COPY ./requirements.txt /backend/
RUN pip install --upgrade pip
RUN apk add libffi-dev
RUN pip install -r requirements.txt

# Copy project
COPY . /backend/