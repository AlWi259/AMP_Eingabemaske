FROM python:3.12-slim

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app

# Copy shared source from az_functions/llm
# Build context must be services/ (see docker-compose.yml)
COPY az_functions/llm/adapters ./adapters
COPY az_functions/llm/models ./models
COPY az_functions/llm/state_nodes ./state_nodes
COPY az_functions/llm/utils ./utils
COPY az_functions/llm/interview_graph.py ./interview_graph.py
COPY az_functions/llm/prompt_templates ./prompt_templates
COPY az_functions/llm/interview ./interview

# Copy FastAPI app
COPY backend/requirements.txt ./requirements.txt
COPY backend/main.py ./main.py

RUN uv pip install --system --no-cache -r requirements.txt

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
