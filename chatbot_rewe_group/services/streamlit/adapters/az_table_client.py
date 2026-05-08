from azure.data.tables import TableClient
from azure.identity import DefaultAzureCredential

from datetime import datetime

import os 
import logging

import streamlit as st

STORAGE_ACCOUNT_NAME = os.environ.get("STORAGE_ACCOUNT", "staygg")

def get_table_client(table_name):
    table_endpoint = f"https://{STORAGE_ACCOUNT_NAME}.table.core.windows.net"
    credentials = DefaultAzureCredential()

    try:
        storage_connection = os.environ["AzureWebJobsStorage"]
        table_client = TableClient.from_connection_string(storage_connection, table_name=table_name)
        logging.info(f"TableClient erfolgreich über Storage Connection erhalten.")
        return table_client
    except KeyError:
        table_client = TableClient(
            endpoint=table_endpoint,
            table_name=table_name,
            credential=credentials
        )
        logging.info(f"BlobClient erfolgreich über Azure Default Credentials erhalten.")
        return table_client
    except Exception as e:
        error_message = f"BlobClient konnte nicht erstellt werden. Unbekannter Fehler: {e}"
        logging.error(error_message)
        return None

    