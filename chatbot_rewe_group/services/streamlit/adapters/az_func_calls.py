import requests
import os

from dotenv import load_dotenv
load_dotenv()

import streamlit as st

RETRIEVAL_FUNC_URL = os.environ.get("FUNCTION_RETRIEVAL_URL", "http://localhost:7074/api/graph_agent")
STORE_YGG_FUNC_URL = os.environ.get("FUNCTION_STORE_URL", "http://localhost:7071/api/embed_and_insert")
GENERATE_GENERAL_YGG_FUNC_URL = os.environ.get("FUNCTION_GENERATE_URL", "http://localhost:7071/api/generate_general_ygg")
GRAPHITI_UPLOAD_FUNC_URL = os.environ.get("FUNCTION_GRAPHITI_UPLOAD_URL", "http://localhost:7071/api/upload_to_graphiti")
CLUSTER_ANSWERS_FUNC_URL = os.environ.get("FUNCTION_CLUSTER_URL", "http://localhost:7071/api/cluster_answers")
SIMULATION_FUNC_URL = os.environ.get("FUNCTION_SIMULATE_USER_URL", "http://localhost:7071/api/simulate_user_response")
FUNCTION_STATUS_URL = os.environ.get("FUNCTION_STATUS_URL", "http://localhost:7071/api/interview_status")
FUNCTION_DELETE_URL = os.environ.get("FUNCTION_DELETE_URL", "http://localhost:7071/api/delete_interview_history")
FUNCTION_AGENT_URL = os.environ.get("FUNCTION_AGENT_URL", "http://localhost:7071/api/interview_agent")
FUNCTION_SUMMARY_URL = os.environ.get("FUNCTION_SUMMARY_URL", "http://localhost:7071/api/get_summary_yggs")
FUNCTION_SAVE_SUMMARY_URL = os.environ.get("FUNCTION_SAVE_SUMMARY_URL", "http://localhost:7071/api/save_summary")
FUNCTION_FINAL_SUMMARY_URL = os.environ.get("FUNCTION_FINAL_SUMMARY_URL", "http://localhost:7071/api/generate_final_summary")
FUNCTION_SAVE_FINAL_SUMMARY_URL = os.environ.get("FUNCTION_SAVE_FINAL_SUMMARY_URL", "http://localhost:7071/api/save_final_summary")

def retrieve_search_results(query):
    payload = {
        "query": query
    }

    response = requests.post(
        url=RETRIEVAL_FUNC_URL,
        json=payload
    )

    
    return response.text

def generate_yggs_from_text(thought):
    payload = {
        "thought": thought
    }

    response = requests.post(
        url=GENERATE_GENERAL_YGG_FUNC_URL,
        json=payload
    )

    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f"Error generating Yggs: {response.text}")

def store_ygg_in_db(ygg, title, group_id):
    payload = {
        "ygg": ygg,
        "title": title,
        "group_id": group_id
    }

    response = requests.post(
        url=GRAPHITI_UPLOAD_FUNC_URL,
        json=payload
    )

    if response.status_code == 200:
        return True
    else:
        raise Exception(f"Fehler beim Hinzufügen des Ygg zum Graph: {response.text}")

def simulate_user_response(last_question, persona):
    payload = {
        "persona": persona,
        "ai_msg": last_question
    }

    response = requests.post(
        url=SIMULATION_FUNC_URL,
        json=payload
    )

    return response.text

def fetch_interview_status(user_id, interview_id):
    try:
        response = requests.post(
            url=FUNCTION_STATUS_URL,
            json={
                "user_id": user_id,
                "interview_id": interview_id
            }
        )
        response.raise_for_status()
        data = response.json()

        chat_history = data["chat_history"]
        interview_status = data["interview_status"]
        current_topic = data.get("current_topic", "")
        open_topics = data.get("open_topics", [])
        completed_topics = data.get("completed_topics", [])

        return chat_history, interview_status, current_topic, open_topics, completed_topics
    except Exception as e:
        print(f"Fehler beim Laden der Antworten: {e}")
        return [], None, "", [], []
    
def delete_interview_history(user_id, interview_id):
    try:
        payload = {
            "user_id": user_id,
            "interview_id": interview_id
        }
        response = requests.post(
            url=FUNCTION_DELETE_URL, 
            json=payload
        )
        response.raise_for_status()

        return st.info("Historie erfolgreich gelöscht.")
    except Exception as e:
        return st.error("Historie konnte nicht gelöscht werden.")
    
def prompt_interview_agent(prompt, user_id, interview_id):
    try:
        payload = {
            "user_id": user_id,
            "interview_id": interview_id,
            "message": prompt,
            "role": "user"
        }

        response = requests.post(
            url=FUNCTION_AGENT_URL, 
            json=payload,
            timeout=60
        )
        response.raise_for_status()

        data = response.json()

        llm_metadata = data.get("llm_metadata", {})
        ai_message = data.get("ai_message", "Keine Antwort erhalten.")
        transition_text = data.get("transition_text", "")
        current_topic = data.get("current_topic", "")
        open_topics = data.get("open_topics", [])
        completed_topics = data.get("completed_topics", [])
        interview_status = data.get("interview_status", 1)
        print(f"Zurückgegebene Daten: {data}")

        return ai_message, transition_text, llm_metadata, current_topic, open_topics, completed_topics, interview_status
    except Exception as e:
        ai_message = f"Agent nicht erreichbar: {e}"
        llm_metadata = {}
        return ai_message, "", llm_metadata, "", [], [], 1

def cluster_answers(answers, labels):
    payload = {
        "answers": answers,
        "labels": labels
    }

    response = requests.post(
        url=CLUSTER_ANSWERS_FUNC_URL,
        json=payload
    )

    return response.text

def get_interview_summary(user_id, interview_id, source_dir):
    try:
        print(f"Fetching interview summary for user_id: {user_id}, interview_id: {interview_id}")  # Debugging line
        payload = {
            "user_id": user_id,
            "interview_id": interview_id,
            "source_dir": source_dir
        }

        response = requests.post(
            url=FUNCTION_SUMMARY_URL,
            json=payload
        )
        response.raise_for_status()
        data = response.json()

        summary = data.get("summary", "")
        ygg_summaries = data.get("ygg_summaries", {})
        return summary, ygg_summaries
    except Exception as e:
        return f"Fehler beim Abrufen der Zusammenfassung: {e}"
    
def save_summary(user_id, interview_id, topic_id, content):
    try:
        print(f"Saving summary for user_id: {user_id}, interview_id: {interview_id}, topic_id: {topic_id}")  # Debugging line
        payload = {
            "user_id": user_id,
            "interview_id": interview_id,
            "id": topic_id,
            "content": content
        }

        response = requests.post(
            url=FUNCTION_SAVE_SUMMARY_URL,
            json=payload
        )
        response.raise_for_status()
        return st.success("Zusammenfassung erfolgreich gespeichert.")
    except Exception as e:
        return st.error(f"Fehler beim Speichern der Zusammenfassung: {e}")

def generate_final_summary(user_id, interview_id):
    try:
        payload = {
            "user_id": user_id,
            "interview_id": interview_id
        }

        response = requests.post(
            url=FUNCTION_FINAL_SUMMARY_URL,
            json=payload,
            timeout=120
        )
        response.raise_for_status()
        data = response.json()
        return data.get("final_summary", "")
    except Exception as e:
        print(f"Error generating final summary: {e}")
        return None

def save_final_summary(user_id, interview_id, content):
    try:
        print(f"Saving final summary for user_id: {user_id}, interview_id: {interview_id}")  # Debugging line
        payload = {
            "user_id": user_id,
            "interview_id": interview_id,
            "content": content
        }

        response = requests.post(
            url=FUNCTION_SAVE_FINAL_SUMMARY_URL,
            json=payload
        )
        response.raise_for_status()
        return st.success("Finale Zusammenfassung erfolgreich gespeichert.")
    except Exception as e:
        return st.error(f"Fehler beim Speichern der finalen Zusammenfassung: {e}")
