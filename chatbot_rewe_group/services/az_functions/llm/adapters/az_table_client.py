import os
import json
import uuid
from datetime import datetime
import logging

from azure.data.tables import TableClient
from azure.core.exceptions import ResourceNotFoundError

from utils.file_loader import load_topics

from models.interview.InterviewState import InterviewState
from models.llm.LLMMetadata import LLMMetadata

##################################
######### Table States ###########
##################################

def get_storage_connection():
    return os.environ.get("AzureWebJobsStorage")

def get_interview_id():
    return os.environ.get("INTERVIEW_ID", "copilot")

def get_table_client_states():
    return TableClient.from_connection_string(get_storage_connection(), table_name="interviewstates")

def get_state_entity(user_id, interview_id):
    try:
        table_client = get_table_client_states()
        entity = table_client.get_entity(partition_key=interview_id, row_key=user_id)
        logging.info(f"Successfully loaded state entity for user with with id {user_id} from interview {interview_id}.")
    except ResourceNotFoundError:
        logging.info(f"State entity for user with id {user_id} from interview {interview_id} doesn't exist yet.")
        entity = None
    except Exception as e:
        logging.error(f"Unknown exception while loading state entity: {e}")
        entity = None

    return entity

def get_state(user_id, interview_id, chat_history=[]):
    interview_id = get_interview_id()
    logging.info(f"Interview-ID aus ENV: {interview_id}")

    interview_id_temp = "copilot"
    topics = load_topics(interview_id_temp)
    entity = get_state_entity(user_id, interview_id)
    active_question = ""

    if entity:
        for topic in topics:
            if topic["id"] == entity["CurrentTopic"]:
                current_topic_name = topic["scope"]
                current_topic_points = topic["points"]
                current_topic_probing_limit = topic["probing_limit"]
                break

        llm_metadata = LLMMetadata(
            prompt_tokens=0,
            completion_tokens=0,
            total_tokens=0
        )

        interview_state = InterviewState(
            user_id=entity["RowKey"],
            interview_id=entity["PartitionKey"],
            interview_status=entity["InterviewStatus"],
            user_information=entity["UserInformation"],
            intro_iterations=entity["IntroIterations"],
            active_question=active_question,
            current_topic=entity["CurrentTopic"],
            current_topic_name=current_topic_name,
            current_topic_points=current_topic_points,
            current_topic_probing_limit=current_topic_probing_limit,
            probing_count=entity["ProbingCount"],
            open_topics=json.loads(entity["OpenTopics"]),
            chat_history_id=entity["ChatHistoryId"],
            llm_metadata=llm_metadata
        )

        return interview_state
    else:
        return None

def create_initial_state(user_id, interview_id):
    interview_id = get_interview_id()
    topics = load_topics(interview_id)

    llm_metadata = LLMMetadata(
            prompt_tokens=0,
            completion_tokens=0,
            total_tokens=0
        )
    
    initial_topic = topics[0]
    initial_interview_state = InterviewState(
        interview_id=interview_id, # Set PartitionKey for TableState
        user_id=user_id, # Set RowKey for TableState
        interview_status=0, # Set initial status to 0 => Interview not started yet
        user_information="",
        intro_iterations=0,
        open_topics=[topic["id"] for topic in topics], # Get all framework questions for this interview and save them
        current_topic=initial_topic["id"], # Set current topic to the first topic
        current_topic_name=initial_topic["scope"], # Set current topic name to the first topic name
        current_topic_points=initial_topic["points"], # Set current topic points to the first topic points
        probing_count=initial_topic["probing_limit"], # Set probing limit for the first topic
        chat_history_id=str(uuid.uuid4()), # Generate unique id for the ChatHistory (which is used as PartitionKey for all messages in this interview)
        chat_history=None, # Set chat history to None, will be filled later
        llm_metadata=llm_metadata
    )
    
    return initial_interview_state

def update_state(state: InterviewState):
    state_entity = {
        "PartitionKey": state["interview_id"],
        "RowKey": state["user_id"],
        "InterviewStatus": state["interview_status"],
        "UserInformation": state["user_information"],
        "IntroIterations": state["intro_iterations"],
        "OpenTopics": json.dumps(state["open_topics"]),
        "CurrentTopic": state["current_topic"],
        "ProbingCount": state["probing_count"],
        "ChatHistoryId": state["chat_history_id"]
    }

    table_client = get_table_client_states()
    table_client.upsert_entity(entity=state_entity, mode="replace")

def delete_state(interview_id, user_id):
    try:
        table_client = get_table_client_states()
        table_client.delete_entity(partition_key=interview_id, row_key=user_id)
        return True, "Succesfully deleted"
    except Exception as e:
        return False, f"Not deleted:"
    
##################################
######## Table Messages ##########
##################################

def get_table_client_messages():
    return TableClient.from_connection_string(get_storage_connection(), table_name="interviewmessages")

def store_message(chat_history_id, role, message, message_tag=""):
    message_entity = {
        "PartitionKey": chat_history_id, # PartitionKey for all messages in this interview
        "RowKey": str(int(datetime.now().timestamp() * 1000)), # Generated RowKey - Unix Timestamp of message
        "role": role, # Author of message (user or assistant)
        "message": message, # Message content
        "MessageTag": message_tag
    }

    table_client = get_table_client_messages()
    table_client.upsert_entity(entity=message_entity)

def get_chat_history_by_question(chat_history_id, question_id):
    chat_history = []

    try:
        table_client = get_table_client_messages()
        entities = list(table_client.query_entities(f"PartitionKey eq '{chat_history_id}' and MessageTag eq '{question_id}'"))
    except ResourceNotFoundError:
        logging.info(f"No message entities for chat history id {chat_history_id} and question {question_id} could be found.")
        entities = None
    except Exception as e:
        logging.error(f"Unknown exception while loading message entities for chat history id {chat_history_id}: {e}")
        entities = None

    if entities:
        # Convert message entities into new format
        messages = [
            {
                "role": entity["role"],
                "content": entity["message"],
                "timestamp": int(entity["RowKey"])
            }
            for entity in entities
        ]

        # Sort messages by timestamp
        sorted_messages = sorted(messages, key=lambda x: x["timestamp"])
        # Just keep role and content
        chat_history = [{"role": item["role"], "content": item["content"]} for item in sorted_messages]

        return chat_history
    else:
        return chat_history

def get_full_chat_history(chat_history_id):
    try:
        table_client = get_table_client_messages()
        entities = list(table_client.query_entities(f"PartitionKey eq '{chat_history_id}'"))

        if not entities:
            logging.info(f"No Answers found for Chat {chat_history_id}")
            return []
        
        # Entities abrufen und in gewünschtes Format bringen, inklusive RowKey für Sortierung
        items = [
            {
                "role": entity["role"],
                "content": entity["message"],
                "timestamp": int(entity["RowKey"])
            }
            for entity in entities
        ]

        # Nach Timestamp sortieren
        sorted_result = sorted(items, key=lambda x: x["timestamp"])

        # Nur Rolle und Inhalt behalten
        chat_history = [{"role": item["role"], "content": item["content"]} for item in sorted_result]

        return chat_history
    
    except Exception as e:
        logging.error(f"[Table] Failed to fetch interview status for partition {chat_history_id}: {type(e).__name__} - {e}")
        return []
    
def delete_chat_history(chat_history_id):
    try:
        table_client = get_table_client_messages()
        entities = table_client.query_entities(f"PartitionKey eq '{chat_history_id}'")

        for entity in entities:
            table_client.delete_entity(partition_key=entity["PartitionKey"], row_key=entity["RowKey"])
            
        return True, "Succesfully deleted"
    except Exception as e:
        return False, f"Not deleted:"
    
##################################
######## Table Answers ###########
##################################

def get_table_client_answers():
    return TableClient.from_connection_string(get_storage_connection(), table_name="interviewanswers")

def store_anwser(chat_history_id, question_id, summary):
    answer_entity = {
        "PartitionKey": chat_history_id, # PartitionKey for all answer summaries in this interview
        "RowKey": question_id, # Generated RowKey - Unix Timestamp of message
        "Summary": summary # Answer summary for this question
    }

    table_client = get_table_client_answers()
    table_client.upsert_entity(entity=answer_entity)

def get_all_answers(chat_history_id):
    try:
        table_client = get_table_client_answers()
        entities = list(table_client.query_entities(f"PartitionKey eq '{chat_history_id}'"))

        if not entities:
            logging.info(f"No Answers found for Chat {chat_history_id}")
            return []
        
        summaries = [entity["Summary"] for entity in entities]

        return summaries
    
    except Exception as e:
        logging.error(f"[Table] Failed to fetch interview status for partition {chat_history_id}: {type(e).__name__} - {e}")
        return []
    
def get_answer(chat_history_id, question_id):
    try:
        table_client = get_table_client_answers()
        entity = table_client.get_entity(partition_key=chat_history_id, row_key=question_id)

        if not entity:
            logging.info(f"No Answer found for Question {question_id} in Chat {chat_history_id}")
            return ""
        else:
            return entity["summary"]
    
    except Exception as e:
        logging.error(f"[Table] Failed to query answer for partition {chat_history_id}: {type(e).__name__} - {e}")
        return ""
    
##################################
####### Table Jobstatus ##########
##################################

def get_table_client_jobstatus():
    return TableClient.from_connection_string(get_storage_connection(), table_name="jobstatus")