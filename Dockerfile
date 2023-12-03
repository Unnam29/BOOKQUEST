# Use the official Python image from Docker Hub as the base image
FROM python:3.10.11
# Set working directory
WORKDIR /usr/src/app
# Copy
COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt

COPY . .
# run
CMD [ "python", "./main.py" ]