FROM python:3.11-slim
WORKDIR /app
COPY . .
RUN mkdir -p /app/data
EXPOSE 8000
CMD ["python3", "server.py"]
