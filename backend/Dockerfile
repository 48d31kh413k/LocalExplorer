#Dockerfile is responsible for the configuration. It specifies a set of software that we want to deploy inside this container.
# We are using the official Python image from Docker Hub as our base image.
# slim version of the image is used to reduce the size of the image.
FROM python:3.11-slim

# Set the working directory in the container to /app
WORKDIR /app

# ENV is used to set the environment variables in the container.
# PYTHONUNBUFFERED is set to 1 to avoid buffering the output of the Python application.
ENV PYTHONUNBUFFERED=1

# RUN is used to execute the commands in the container.
# We are installing the required dependencies for the Python application.
RUN apt-get update && apt-get install -y \
     gcc \
    && rm -rf /var/lib/apt/lists/*
 # Copy the requirements.txt file from the local machine to the /app directory in the container.
 COPY requirements.txt .

 # --no-cache-dir is used to avoid caching the downloaded packages.
 RUN pip install --no-cache-dir -r requirements.txt

 # Copy the entire local directory to the /app directory in the container.
 COPY . .

 # EXPOSE is used to expose the port 8000 in the container.
 EXPOSE 8000

 #0.0.0.0:8000 is used to run the Django application on all available network interfaces.
 CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]