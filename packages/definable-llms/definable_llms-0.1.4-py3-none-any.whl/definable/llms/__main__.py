"""Entry point for running the LLM Library API server via python -m src.libs.llms."""

from .api.main import run_server

if __name__ == "__main__":
  run_server()
