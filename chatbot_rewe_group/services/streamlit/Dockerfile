FROM python:3.12-slim

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app

RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    iputils-ping \
    && rm -rf /var/lib/apt/lists/*

# Copy all files
COPY . .

RUN uv pip install --system --no-cache -r requirements.txt

# Expose port 8501 for streamlit
EXPOSE 8501
# Healtcheck (able to listen to port?)
HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health

# Streamlit entry point
ENTRYPOINT ["streamlit", "run", "Interview.py", "--server.port=8501", "--server.address=0.0.0.0"]