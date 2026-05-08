import json
import re
import logging

def get_client_information(headers):
    """
    Get client information from Azure App Service headers (Entra ID).

    Priority:
    1. Azure App Service headers (X-Ms-Client-Principal-*)
    2. Dev mode (fallback)

    Args:
        headers: Request headers from st.context.headers

    Returns:
        tuple: (dev_mode: bool, client_info: dict)
    """
    # Check for Azure App Service headers
    if 'X-Ms-Client-Principal-Name' in headers:
        dev_mode = False
        client_info = {
            'principal_name': headers['X-Ms-Client-Principal-Name'],
            'principal_id': headers['X-Ms-Client-Principal-Id'],
            'principal_idp': headers['X-Ms-Client-Principal-Idp'],
            'principal': headers['X-Ms-Client-Principal']
        }
        return dev_mode, client_info

    # Fallback to dev mode with hardcoded principal_id
    dev_mode = True
    client_info = {
        'principal_name': 'dev',
        'principal_id': 'dev-user-123',
        'principal_idp': 'dev',
        'principal': 'dev'
    }
    return dev_mode, client_info

def load_interview_results():
    try:
        with open("interview_results.json", "r", encoding="utf-8") as json_data:
            data = json.load(json_data)
        logging.info("Interview-Resultate erfolgreich geladen.")
        return data
    except Exception as e:
        print(f"Fehler beim Laden der Interview-Resultate: {e}")
        return {}
    
def load_questions():
    try:
        with open("questions.json", "r", encoding="utf-8") as json_data:
            data = json.load(json_data)
        logging.info("Interview-Resultate erfolgreich geladen.")
        return data["questions"]
    except Exception as e:
        print(f"Fehler beim Laden der Interview-Resultate: {e}")
        return {}
    
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