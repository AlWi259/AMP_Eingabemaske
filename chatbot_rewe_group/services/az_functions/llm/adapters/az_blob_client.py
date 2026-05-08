from azure.storage.blob import BlobServiceClient
import json
from io import BytesIO
import os

STORAGE_CONNECTION = os.environ["AzureWebJobsStorage"]
CONTAINER_NAME = "interview-yggs"

BLOB_SERVICE_CLIENT = BlobServiceClient.from_connection_string(STORAGE_CONNECTION)

def load_json_from_blob(blob_name):
    blob_client = BLOB_SERVICE_CLIENT.get_blob_client(container=CONTAINER_NAME, blob=blob_name)
    try:
        download_stream = blob_client.download_blob()
        return json.loads(download_stream.readall())
    except Exception:
        return {}
    
def upload_json_to_blob(blob_name, data):
    blob_client = BLOB_SERVICE_CLIENT.get_blob_client(container=CONTAINER_NAME, blob=blob_name)
    json_bytes = json.dumps(data, indent=2).encode("utf-8")
    blob_client.upload_blob(json_bytes, overwrite=True)

def delete_blob(blob_name):
    """
    Delete a blob from the container.
    Args:
        blob_name (str): The name (path) of the blob to delete.
    Returns:
        bool: True if deleted successfully, False otherwise.
    """
    blob_client = BLOB_SERVICE_CLIENT.get_blob_client(container=CONTAINER_NAME, blob=blob_name)
    try:
        blob_client.delete_blob()
        return True
    except Exception as e:
        print(f"Error deleting blob {blob_name}: {e}")
        return False

def append_data_to_blob(dir, data, interview_id, user_id, chat_id):
    blob_name = f"{dir}/topic-summaries/{interview_id}-{chat_id}-topic_summaries.json"

    current_data = load_json_from_blob(blob_name)

    try:
        # Check if topic exists in ygg_summaries and update
        for idx, item in enumerate(current_data.get("ygg_summaries", [])):
            print(f"Comparing item topic_id: {item.get('topic_id')} with data topic_id: {data.get('topic_id')}")
            if item.get("topic_id") == data.get("topic_id"):
                print(f"Updating existing topic_id: {data.get('topic_id')}")
                current_data["ygg_summaries"][idx] = data
                break
            else:
                print(f"No match for topic_id: {data.get('topic_id')} in item topic_id: {item.get('topic_id')}")
        else:
            print(f"Appending new topic_id: {data.get('topic_id')}")
            current_data["ygg_summaries"].append(data)
    except KeyError:
        current_data["ygg_summaries"] = [data]

    upload_json_to_blob(blob_name, current_data)

def delete_data_from_blob(blob_name, topic_id, list_key="ygg_summaries"):
    """
    Delete one item from a JSON list in a blob by key/value.
    Args:
        blob_name (str): The blob to update.
        key (str): The key to match in the list items.
        value: The value to match for deletion.
        list_key (str): The key of the list in the JSON (default: 'ygg_summaries').
    Returns:
        bool: True if deleted, False if not found.
    """
    data = load_json_from_blob(blob_name)
    items = data.get(list_key, [])
    new_items = [item for item in items if item.get("topic_id") != topic_id]
    if len(new_items) == len(items):
        return False  # Nothing deleted
    data[list_key] = new_items
    upload_json_to_blob(blob_name, data)
    return True

def append_message_to_blob(message, interview_id, chat_id, role):
    blob_name = f"temporary-data/message-history/{interview_id}-{chat_id}-messages.json"

    current_data = load_json_from_blob(blob_name)

    current_data["chat_id"] = chat_id

    try:
        if role == "user":
            current_data["answers"].append(message)
        elif role == "assistant":
            current_data["questions"].append(message)
    except KeyError:
        if role == "user":
            current_data["answers"] = [message]
        elif role == "assistant":
            current_data["questions"] = [message]

    upload_json_to_blob(blob_name, current_data)