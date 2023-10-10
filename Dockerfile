FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt requirements.txt
RUN pip3 install --no-cache-dir -r requirements.txt
RUN apt update && apt install -y curl unzip
RUN curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip" && \
    unzip awscliv2.zip && \
    bash ./aws/install

COPY . .

# Copy AWS credentials and config files to /root/.aws/
COPY .aws/credentials /root/.aws/credentials
COPY .aws/config /root/.aws/config

# Run aws eks update-kubeconfig command
RUN aws eks update-kubeconfig --name nba-eks --region ap-northeast-1

#Expose the port your application will run on
EXPOSE 8000

# Start your application using uvicorn
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
