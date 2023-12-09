FROM python:3.10.11
# Set working directory
WORKDIR /app
# Copy
COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt

COPY . /app

EXPOSE 3000
# run
CMD [ "python", "./main.py" ]