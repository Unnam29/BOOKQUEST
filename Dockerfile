# Use the official Python image from Docker Hub as the base image
FROM python:3.8
# Set working directory
WORKDIR /app
# Copy
COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt

COPY . /app

EXPOSE 3000
# run
CMD [ "python", "./main.py" ]