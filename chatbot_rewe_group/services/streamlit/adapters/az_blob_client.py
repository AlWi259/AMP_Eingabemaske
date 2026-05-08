import os
import streamlit as st

from azure.storage.blob import BlobServiceClient, BlobClient
from azure.identity import DefaultAzureCredential

import logging
import json

STORAGE_ACCOUNT_NAME = os.environ.get("STORAGE_ACCOUNT", "styggdrasil")

def get_blob_client(container_name, blob_name):
    credentials = DefaultAzureCredential()
    storage_url = f"https://{STORAGE_ACCOUNT_NAME}.blob.core.windows.net"

    try:
        storage_connection = os.environ["AzureWebJobsStorage"]
        blob_service_client = BlobServiceClient.from_connection_string(storage_connection)
        blob_client = blob_service_client.get_blob_client(container=container_name, blob=blob_name)
        logging.info(f"BlobClient erfolgreich über Storage Connection erhalten.")
        return blob_client
    except KeyError:
        blob_client = BlobClient(
            account_url=storage_url,
            container_name=container_name,
            blob_name=blob_name,
            credential=credentials
        )
        logging.info(f"BlobClient erfolgreich über Azure Default Credentials erhalten.")
        return blob_client
    except Exception as e:
        error_message = f"BlobClient konnte nicht erstellt werden. Unbekannter Fehler: {e}"
        logging.error(error_message)
        return None

def upload_audio_file(file, blob_name, metadata={}):
    blob_client = get_blob_client("audio-raw", blob_name)

    if not blob_client:
        return st.error(f"Verbindung zum Dateiserver konnte nicht hergestellt werden.")

    try:
        blob_client.upload_blob(
            data=file,
            overwrite=True,
            metadata=metadata
        )
        success_message = "Datei erfolgreich hochgeladen."
        logging.info(success_message)
        return st.success("Datei-Upload erfolgreich.")
    except Exception as e:
        error_message = f"Datei konnte nicht hochgeladen werden. Unbekannter Fehler: {e}"
        logging.error(error_message)
        return st.error(f"Datei-Upload fehlgeschlagen.")

def upload_text_thought(text_data, blob_name, metadata={}):
    blob_client = get_blob_client("audio-transcripts", blob_name)

    if not blob_client:
        return st.error(f"Verbindung zum Dateiserver konnte nicht hergestellt werden.")

    try:
        print(f"Metadaten: {metadata}")
        blob_client.upload_blob(
            data=text_data,
            overwrite=True,
            metadata=metadata
        )
        success_message = "Datei erfolgreich hochgeladen."
        logging.info(success_message)
        return st.success("Datei-Upload erfolgreich.")
    except Exception as e:
        error_message = f"Datei konnte nicht hochgeladen werden. Unbekannter Fehler: {e}"
        logging.error(error_message)
        return st.error(f"Datei-Upload fehlgeschlagen.")

def get_transcription_text(job_id):
    blob_name = f"{job_id}.json"
    blob_client = get_blob_client("audio-transcripts", blob_name)

    if not blob_client:
        return st.error(f"Verbindung zum Dateiserver konnte nicht hergestellt werden.")
    
    try:
        download_stream = blob_client.download_blob()
        response_json = json.loads(download_stream.readall())
        return response_json["text"]
    except Exception:
        return ""
    
def get_audio_processing_result(job_id):
    blob_name = f"{job_id}.json"
    blob_client = get_blob_client("yggs-summarized", blob_name)

    if not blob_client:
        return st.error(f"Verbindung zum Dateiserver konnte nicht hergestellt werden.")
    
    try:
        download_stream = blob_client.download_blob()
        response_json = json.loads(download_stream.readall())
        return response_json
    except Exception:
        return ""