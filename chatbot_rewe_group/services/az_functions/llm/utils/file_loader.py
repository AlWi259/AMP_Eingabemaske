from pathlib import Path
import json

import logging


def load_prompt(directory: str, name: str) -> str:
    """
    Load a prompt template as a string from the prompt_templates directory.
    Args:
        directory (str): Subdirectory under prompt_templates.
        name (str): Name of the prompt file (without extension).
    Returns:
        str: The contents of the prompt file as a string.
    Raises:
        FileNotFoundError: If the prompt file does not exist.
        UnicodeDecodeError: If the file cannot be decoded as UTF-8.
    """
    path = Path(__file__).parent.parent / "prompt_templates" / str(directory) / f"{name}.txt"
    try:
        return path.read_text(encoding="utf-8")
    except Exception as e:
        logging.error(f"Failed to load prompt '{name}' from '{directory}': {e}")
        raise

def load_topics(name: str) -> list:
    """
    Load a list of topics from a JSON file in the interview directory.
    Args:
        name (str): Name of the interview/topic set (subdirectory under interview).
    Returns:
        list: List of topics loaded from the JSON file.
    Raises:
        FileNotFoundError: If the topics file does not exist.
        KeyError: If the 'topics' key is missing in the JSON.
        json.JSONDecodeError: If the file is not valid JSON.
    """
    path = Path(__file__).parent.parent / "interview" / name / "topics.json"
    try:
        data = path.read_text(encoding="utf-8")
        topics = json.loads(data)["topics"]
        return topics
    except Exception as e:
        logging.error(f"Failed to load topics for '{name}': {e}")
        raise