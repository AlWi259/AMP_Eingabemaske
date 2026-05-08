import re


def get_topic_ids(topic_list: list) -> list:
    """
    Extracts topic IDs from a list of topic dictionaries.

    Args:
        topic_list (list): List of topic dictionaries, each containing an 'id' key.

    Returns:
        list: List of topic IDs.
    """
    return [topic["id"] for topic in topic_list if "id" in topic]


def extract_meta_comment(message: str) -> tuple[str, str | None]:
    """
    Extract meta comment from user message using regex.
    Meta comments have the format: ### <feedback text> ###

    Args:
        message (str): The user message potentially containing a meta comment.

    Returns:
        tuple[str, str | None]: A tuple containing (message_without_feedback, feedback).
                                 If no meta comment found, feedback will be None.
    """
    # Regex pattern to match ### <text> ###
    pattern = r'###\s*(.+?)\s*###'

    match = re.search(pattern, message)
    if match:
        feedback = match.group(1).strip()
        message_without_feedback = re.sub(pattern, '', message).strip()
        return message_without_feedback, feedback

    return message, None