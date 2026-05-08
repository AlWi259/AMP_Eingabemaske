#!/bin/bash
PYTHONPATH=../az_functions/llm uv run --env-file .env uvicorn main:app --reload --port 8000
