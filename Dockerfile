FROM python:3.10-slim

# 필요한 라이브러리 설치
RUN apt-get update && \
    apt-get install -y software-properties-common && \
    add-apt-repository 'deb http://archive.ubuntu.com/ubuntu trusty universe' && \
    apt-get update && \
    apt-get install -y mysql-client && \
    apt-get clean

WORKDIR /app

COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
