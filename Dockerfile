FROM python:3.8-slim

# Install Google Cloud SDK
RUN apt-get update -y && apt-get install -y curl
RUN curl -sSL https://sdk.cloud.google.com | bash

# Add gcloud to the path
ENV PATH $PATH:/root/google-cloud-sdk/bin

# Install your application's dependencies
COPY requirements.txt /app/requirements.txt
WORKDIR /app
RUN pip install -r requirements.txt

# Copy your application's code into the container
COPY . /app

# Expose the port
EXPOSE 5000

# Set the command
CMD ["gunicorn", "-b", "0.0.0.0:5000", "app:app"]