# Use Ubuntu 20.04 as the base image
FROM ubuntu:20.04

# Update package lists and install necessary packages
RUN apt-get update && apt-get install -y \
    python3.10 \
    python3.10-dev \
    python3.10-distutils \
    python3-pip \
    default-libmysqlclient-dev \
    build-essential

# Set the working directory
WORKDIR /app

# Copy the requirements.txt file and install dependencies
COPY requirements.txt requirements.txt
RUN pip3 install --no-cache-dir -r requirements.txt

# Copy the rest of your application code
COPY . .

# Expose the port your application will run on
EXPOSE 8000

# Start your application using uvicorn
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
