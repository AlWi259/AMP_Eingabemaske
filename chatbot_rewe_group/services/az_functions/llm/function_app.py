# --- Standard Library Imports ---
import logging
import os
import json

# --- Third-Party Imports ---
import azure.functions as func
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient
from openai import AzureOpenAI
from langchain_core.messages import AIMessage, HumanMessage

# --- Local Imports ---
from adapters.az_table_client import (
    store_message, get_full_chat_history, delete_chat_history, delete_state, get_state, update_state, get_table_client_jobstatus, create_initial_state, get_chat_history_by_question, store_anwser, get_all_answers
)
from adapters.az_blob_client import load_json_from_blob, append_message_to_blob, append_data_to_blob, delete_blob, delete_data_from_blob
from adapters.graphiti_client import get_graphiti_client, add_episodes_to_graph
from utils.file_loader import load_prompt, load_topics
from utils.llm_utils import get_llm
from utils.helper_functions import extract_meta_comment
import models.pydantic.PydanticModels as pydantic_models
from interview_graph import *

import asyncio

# --- Request/Response Helpers ---

def parse_json_body(req: func.HttpRequest) -> dict:
    """
    Safely parse JSON body from an Azure Function HTTP request.
    Returns:
        dict: Parsed JSON body, or empty dict if parsing fails or body is not JSON.
    """
    try:
        return req.get_json()
    except Exception:
        return {}

def get_param(req: func.HttpRequest, key: str, default=None) -> str:
    """
    Retrieve a parameter from either the query string or JSON body of the request.
    Args:
        req (func.HttpRequest): The HTTP request object.
        key (str): The parameter key to retrieve.
        default (Any, optional): Default value if parameter is not found. Defaults to None.
    Returns:
        str: The parameter value, or default if not found.
    """
    val = req.params.get(key)
    if val is not None:
        return val
    body = parse_json_body(req)
    return body.get(key, default)

def error_response(message: str, status_code: int = 400) -> func.HttpResponse:
    """
    Return a standardized error response for Azure Functions.
    Args:
        message (str): Error message to return in the response body.
        status_code (int, optional): HTTP status code. Defaults to 400.
    Returns:
        func.HttpResponse: The error response object.
    """
    return func.HttpResponse(
        json.dumps({"error": message}),
        status_code=status_code,
        mimetype="application/json"
    )


app = func.FunctionApp()

##################################
###### Define AZ Functions #######
##################################

@app.route(route="interview_agent", auth_level=func.AuthLevel.FUNCTION)
def interview_agent(req: func.HttpRequest) -> func.HttpResponse:
    """
    Main endpoint for the interview agent. Handles user messages and runs the interview state machine.
    Args:
        req (func.HttpRequest): The HTTP request containing user message and parameters.
    Returns:
        func.HttpResponse: The response containing the AI message and interview status.
    """
    message = get_param(req, "message")
    role = get_param(req, "role", "")
    user_id = get_param(req, "user_id")
    interview_id = get_param(req, "interview_id")
    if not user_id or not interview_id:
        return error_response("Missing required parameters: user_id and interview_id.", 400)

    # Extract meta comment (feedback) from message if present
    message_with_feedback = message
    message_without_feedback = message
    feedback = None
    if message:
        message_without_feedback, feedback = extract_meta_comment(message)
        if feedback:
            logging.info(f"Extracted feedback from user message: {feedback}")

    # Retrieve or create interview state
    interview_state = get_state(user_id, interview_id)
    if not interview_state:
        logging.info("Interview state doesn't exist yet, creating new initial state.")
        interview_state = create_initial_state(user_id, interview_id)
    elif role == "user" and message_with_feedback:
        try:
            store_message(
                chat_history_id=interview_state.get("chat_history_id"),
                role=role,
                message=message_without_feedback,
                message_tag=interview_state.get("current_topic")
            )

            append_message_to_blob(
                message=message_with_feedback,
                interview_id=interview_id,
                chat_id=interview_state.get("chat_history_id"),
                role=role
            )

        except Exception as e:
            logging.error(f"Failed to store user message: {e}")
            return error_response(f"Failed to store user message: {e}", 500)

    # Build chat history for the current question
    chat_history_raw = get_chat_history_by_question(
        interview_state.get("chat_history_id"),
        interview_state.get("current_topic")
    )
    chat_history = []
    if chat_history_raw:
        for chat_msg in chat_history_raw:
            msg_role = chat_msg.get("role")
            content = chat_msg.get("content", "")
            if msg_role == "user":
                chat_history.append(HumanMessage(content=content))
            elif msg_role == "assistant":
                chat_history.append(AIMessage(content=content))

    interview_state["chat_history"] = chat_history

    # If interview is already finished
    if interview_state.get("interview_status") == 2:
        response = {
            "ai_message": "Interview bereits beendet.",
            "interview_status": interview_state.get("interview_status")
        }
        return func.HttpResponse(
            json.dumps(response),
            status_code=200,
            mimetype="application/json"
        )

    # Run the interview state machine
    try:
        interview_graph = build_graph()
        result = interview_graph.invoke(interview_state)

        open_topics = result.get("open_topics", [])
        topic_list = load_topics(name="copilot")

        # Get all topic names for open topics
        open_topic_names = []
        for topic in topic_list:
            if topic["id"] in open_topics:
                open_topic_names.append(topic["scope"])

        # Get all topic names for completed topics
        completed_topic_names = []
        for topic in topic_list:
            if topic["id"] not in open_topics and topic["id"] != result.get("current_topic"):
                completed_topic_names.append(topic["scope"])

        response = {
            "ai_message": result.get("ai_message", ""),
            "transition_text": result.get("transition_text", ""),
            "interview_status": result.get("interview_status", 0),
            "llm_metadata": result.get("llm_metadata", {}),
            "current_topic": result.get("current_topic_name", ""),
            "open_topics": open_topic_names,
            "completed_topics": completed_topic_names,
        }
        return func.HttpResponse(
            json.dumps(response),
            status_code=200,
            mimetype="application/json"
        )
    except Exception as e:
        logging.error(f"Interview agent error: {e}")
        return error_response(f"Interview agent error: {e}", 500)

@app.route(route="interview_status", auth_level=func.AuthLevel.FUNCTION)
def interview_status(req: func.HttpRequest) -> func.HttpResponse:
    """
    Returns the full chat history and interview status for a given user/interview.
    Args:
        req (func.HttpRequest): The HTTP request containing user_id and interview_id.
    Returns:
        func.HttpResponse: The response containing chat history and interview status.
    """
    user_id = get_param(req, 'user_id')
    interview_id = get_param(req, 'interview_id')
    if not user_id or not interview_id:
        return error_response("Missing required parameters: user_id and interview_id.", 400)

    interview_state = get_state(user_id, interview_id)
    if interview_state:
        chat_history = get_full_chat_history(interview_state["chat_history_id"])
        interview_status_val = interview_state["interview_status"]
    else:
        response = {
            "chat_history": [],
            "interview_status": 0,
            "current_topic": "",
            "open_topics": [],
            "completed_topics": []
        }
        return func.HttpResponse(
            json.dumps(response, ensure_ascii=False, indent=2),
            mimetype="application/json",
            status_code=200
        )

    open_topics = interview_state.get("open_topics", [])
    topic_list = load_topics(name="copilot")
    current_topic = interview_state.get("current_topic_name")

    # Get all topic names for open topics
    open_topic_names = []
    for topic in topic_list:
        if topic["id"] in open_topics:
            open_topic_names.append(topic["scope"])

    # Get all topic names for completed topics
    completed_topic_names = []
    for topic in topic_list:
        if topic["id"] not in open_topics and topic["id"] != interview_state.get("current_topic"):
            completed_topic_names.append(topic["scope"])
        elif topic["id"] not in open_topics and len(open_topics) == 0 and interview_state.get("interview_status") == 2:
            current_topic = ""
            completed_topic_names.append(topic["scope"])

    response = {
        "chat_history": chat_history,
        "interview_status": interview_status_val,
        "current_topic": current_topic,
        "open_topics": open_topic_names,
        "completed_topics": completed_topic_names,
    }
    return func.HttpResponse(
        json.dumps(response, ensure_ascii=False, indent=2),
        mimetype="application/json",
        status_code=200
    )

@app.route(route="get_summary_yggs", auth_level=func.AuthLevel.FUNCTION)
def get_summary_yggs(req: func.HttpRequest) -> func.HttpResponse:
    """
    Returns user summaries for a given user/interview.
    Args:
        req (func.HttpRequest): The HTTP request containing user_id and interview_id.
    Returns:
        func.HttpResponse: The response containing summary as JSON.
    """
    user_id = get_param(req, 'user_id')
    interview_id = get_param(req, 'interview_id')
    source_dir = get_param(req, 'source_dir')
    if not user_id or not interview_id or not source_dir:
        return error_response("Missing required parameters: user_id, interview_id, and source_dir.", 400)

    interview_state = get_state(user_id, interview_id)
    if interview_state is None:
        return func.HttpResponse(
            json.dumps({
                "summary": "",
                "ygg_summaries": {}
            }),
            status_code=200,
            mimetype="application/json"
        )
    user_information = interview_state.get("user_information", "")

    chat_history_id = interview_state.get("chat_history_id")
    blob_name = f"{source_dir}/topic-summaries/{interview_id}-{chat_history_id}-topic_summaries.json"
    yggs = load_json_from_blob(blob_name)

    if user_information:
        return func.HttpResponse(
            json.dumps({"summary": user_information,
                        "ygg_summaries": yggs.get("ygg_summaries", {})},
                       ensure_ascii=False, indent=2),
            status_code=200,
            mimetype="application/json"
        )
    else:
        logging.info("No user information found.")
        return func.HttpResponse(
            json.dumps({
                "summary": "",
                "ygg_summaries": {}
            }),
            status_code=200,
            mimetype="application/json"
        )
    

@app.route(route="delete_interview_history", auth_level=func.AuthLevel.FUNCTION)
def delete_interview_history(req: func.HttpRequest) -> func.HttpResponse:
    """
    Deletes the interview state and chat history for a given user/interview.
    Args:
        req (func.HttpRequest): The HTTP request containing user_id and interview_id.
    Returns:
        func.HttpResponse: The response indicating success or error.
    """
    user_id = get_param(req, 'user_id')
    interview_id = get_param(req, 'interview_id')
    if not user_id or not interview_id:
        return error_response("Missing required parameters: user_id and interview_id.", 400)

    interview_state = get_state(user_id, interview_id)
    try:
        delete_state(interview_id=interview_id, user_id=user_id)
        if interview_state:
            delete_chat_history(chat_history_id=interview_state["chat_history_id"])
        return func.HttpResponse(
            "Deleted history.",
            status_code=200
        )
    except Exception as e:
        return error_response(f"Error while deleting the history: {e}", 500)

@app.route(route="generate_general_ygg", auth_level=func.AuthLevel.FUNCTION)
def generate_general_ygg(req: func.HttpRequest) -> func.HttpResponse:
    """
    Endpoint for generating a summary from input_text.
    Args:
        req (func.HttpRequest): The HTTP request containing 'input_text' parameter.
    Returns:
        func.HttpResponse: The response with the summary.
    """
    thought = get_param(req, 'thought')
    if not thought:
        return error_response("Missing required parameter: thought.", 400)

    llm = get_llm()
    if llm is None:
        return error_response("LLM instance could not be created.", 500)
    
    ygg_prompt = load_prompt(directory="yggs", name="generate_ygg_normal").format(
            input=thought
        )
    
    # Load the prompt for generating general Ygg
    structured_llm = llm.with_structured_output(schema=pydantic_models.YggList, include_raw=True)
    response = structured_llm.invoke(ygg_prompt)
    parsed_response = response["parsed"]

    yggs = []
    for ygg in parsed_response.ygg_list:
        logging.info(f"Hier ist ein Ygg: {ygg}")
        yggs.append({"title": ygg.title, "content": ygg.content})

    result = {
        "transcription": thought,
        "summary": "",
        "yggs": yggs
    }

    return func.HttpResponse(
        json.dumps(result, ensure_ascii=False, indent=2),
        status_code=200,
        mimetype="application/json"
    )

@app.route(route="save_summary", auth_level=func.AuthLevel.FUNCTION)
def save_summary(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Python HTTP trigger function processed a request.')

    # Expect 'id', 'content', 'user_id', 'interview_id', 'chat_id', 'source_dir' as parameters
    topic_id = get_param(req, 'id')
    content = get_param(req, 'content')
    user_id = get_param(req, 'user_id')
    interview_id = get_param(req, 'interview_id')

    topics = load_topics(name="copilot")

    # Print debugging info
    logging.info(f"Received parameters - id: {topic_id}, user_id: {user_id}, interview_id: {interview_id}")

    interview_state = get_state(user_id, interview_id)
    chat_id = interview_state.get("chat_history_id")

    # Validate required parameters
    if not topic_id or not isinstance(topic_id, str):
        return error_response("Missing or invalid 'id' parameter. Please provide a string topic id.", 400)
    if not content or not isinstance(content, str):
        return error_response("Missing or invalid 'content' parameter. Please provide the summary text.", 400)
    if not user_id or not interview_id or not chat_id:
        return error_response("Missing required parameters: user_id, interview_id, chat_id.", 400)

    # find topic name for topic_id from list
    topic_name = next((topic["scope"] for topic in topics if topic["id"] == topic_id), None)
    if not topic_name:
        return error_response(f"Topic id '{topic_id}' not found in topics list.", 400)

    # Compose the summary object
    summary_obj = {
        "topic_id": topic_id,
        "topic_name": topic_name,
        "ygg": content
    }

    # Store using append_data_to_blob in temporary-data during interview
    # Will be copied to saved-data when final summary is submitted
    try:
        append_data_to_blob('temporary-data', summary_obj, interview_id, user_id, chat_id)
    except Exception as e:
        return error_response(f"Error saving summary: {str(e)}", 500)

    return func.HttpResponse(
        json.dumps({
            "message": "Summary saved successfully.",
            "topic_id": topic_id,
            "summary": content
        }),
        status_code=200,
        mimetype="application/json"
    )

@app.route(route="save_final_summary", auth_level=func.AuthLevel.FUNCTION)
def save_final_summary(req: func.HttpRequest) -> func.HttpResponse:
    """
    Saves the edited final summary to saved-data blob storage and updates interview status to 3.
    Args:
        req (func.HttpRequest): The HTTP request containing user_id, interview_id, and content.
    Returns:
        func.HttpResponse: The response indicating success or error.
    """
    user_id = get_param(req, 'user_id')
    interview_id = get_param(req, 'interview_id')
    content = get_param(req, 'content')

    logging.info(f"Received save_final_summary request - user_id: {user_id}, interview_id: {interview_id}")

    # Validate required parameters
    if not user_id or not interview_id:
        return error_response("Missing required parameters: user_id and interview_id.", 400)
    if not content or not isinstance(content, str):
        return error_response("Missing or invalid 'content' parameter. Please provide the summary text.", 400)

    # Get interview state
    interview_state = get_state(user_id, interview_id)
    if interview_state is None:
        return error_response("Interview not found.", 404)

    # Compose the final summary object
    final_summary_obj = {
        "final_summary": content
    }

    # Define blob paths
    saved_blob_name = f"saved-data/final-summaries/{interview_id}-{user_id}-final_summary.json"
    temp_blob_name = f"temporary-data/final-summaries/{interview_id}-{user_id}-final_summary.json"

    # Save to saved-data and delete from temporary-data
    try:
        from adapters.az_blob_client import upload_json_to_blob, delete_blob, load_json_from_blob
        upload_json_to_blob(saved_blob_name, final_summary_obj)
        delete_blob(temp_blob_name)
        logging.info(f"Final summary saved successfully for user {user_id}, interview {interview_id}")
    except Exception as e:
        logging.error(f"Error saving final summary: {str(e)}")
        return error_response(f"Error saving final summary: {str(e)}", 500)

    # Copy message history and topic summaries from temporary-data to saved-data
    chat_id = interview_state.get("chat_history_id")

    # Copy message history
    temp_message_history_blob = f"temporary-data/message-history/{interview_id}-{chat_id}-messages.json"
    saved_message_history_blob = f"saved-data/message-history/{interview_id}-{chat_id}-messages.json"

    try:
        message_history = load_json_from_blob(temp_message_history_blob)
        if message_history:
            upload_json_to_blob(saved_message_history_blob, message_history)
            logging.info(f"Message history copied to saved-data for user {user_id}, interview {interview_id}")
            delete_blob(temp_message_history_blob)
        else:
            logging.warning(f"No message history found in temporary-data for user {user_id}, interview {interview_id}")
    except Exception as e:
        logging.error(f"Error copying message history: {str(e)}")
        # Don't fail the request if message history copy fails - final summary is already saved

    # Copy topic summaries
    temp_topic_summaries_blob = f"temporary-data/topic-summaries/{interview_id}-{chat_id}-topic_summaries.json"
    saved_topic_summaries_blob = f"saved-data/topic-summaries/{interview_id}-{chat_id}-topic_summaries.json"

    try:
        topic_summaries = load_json_from_blob(temp_topic_summaries_blob)
        if topic_summaries:
            upload_json_to_blob(saved_topic_summaries_blob, topic_summaries)
            logging.info(f"Topic summaries copied to saved-data for user {user_id}, interview {interview_id}")
            delete_blob(temp_topic_summaries_blob)
        else:
            logging.warning(f"No topic summaries found in temporary-data for user {user_id}, interview {interview_id}")
    except Exception as e:
        logging.error(f"Error copying topic summaries: {str(e)}")
        # Don't fail the request if topic summaries copy fails - final summary is already saved

    # Update interview status to 3 (final summary submitted)
    try:
        interview_state["interview_status"] = 3
        update_state(state=interview_state)
        logging.info(f"Interview status updated to 3 for user {user_id}, interview {interview_id}")
    except Exception as e:
        logging.error(f"Error updating interview status: {str(e)}")
        # Don't fail the request if status update fails - summary is already saved

    return func.HttpResponse(
        json.dumps({
            "message": "Final summary saved successfully.",
            "content": content,
            "interview_status": 3
        }),
        status_code=200,
        mimetype="application/json"
    )

@app.route(route="generate_final_summary", auth_level=func.AuthLevel.FUNCTION)
def generate_final_summary(req: func.HttpRequest) -> func.HttpResponse:
    """
    Generates a comprehensive final summary from all topic summaries.
    Checks if summary already exists in blob storage before generating.
    Args:
        req (func.HttpRequest): The HTTP request containing user_id and interview_id.
    Returns:
        func.HttpResponse: The response containing the final summary.
    """
    user_id = get_param(req, 'user_id')
    interview_id = get_param(req, 'interview_id')

    if not user_id or not interview_id:
        return error_response("Missing required parameters: user_id and interview_id.", 400)

    # Get interview state
    interview_state = get_state(user_id, interview_id)
    if interview_state is None:
        return error_response("Interview not found.", 404)

    interview_status = interview_state.get("interview_status")

    # If status is 3 (final summary submitted), return the saved summary
    if interview_status == 3:
        saved_summary_blob_name = f"saved-data/final-summaries/{interview_id}-{user_id}-final_summary.json"
        saved_summary = load_json_from_blob(saved_summary_blob_name)
        if saved_summary and saved_summary.get("final_summary"):
            logging.info(f"Interview status is 3. Returning saved final summary for user {user_id}, interview {interview_id}.")
            return func.HttpResponse(
                json.dumps(saved_summary, ensure_ascii=False, indent=2),
                status_code=200,
                mimetype="application/json"
            )
        else:
            return error_response("Final summary has been submitted but not found in storage.", 500)

    # Check if interview is completed
    if interview_status != 2:
        return error_response("Interview is not yet completed.", 400)

    chat_history_id = interview_state.get("chat_history_id")

    # Check if final summary already exists in temporary blob storage
    final_summary_blob_name = f"temporary-data/final-summaries/{interview_id}-{user_id}-final_summary.json"
    existing_summary = load_json_from_blob(final_summary_blob_name)

    if existing_summary and existing_summary.get("final_summary"):
        logging.info(f"Final summary already exists in temporary storage for user {user_id}, interview {interview_id}. Returning cached version.")
        return func.HttpResponse(
            json.dumps(existing_summary, ensure_ascii=False, indent=2),
            status_code=200,
            mimetype="application/json"
        )

    # Get all topic summaries from temporary-data (they are copied to saved-data only when final summary is submitted)
    topic_summaries_blob_name = f"temporary-data/topic-summaries/{interview_id}-{chat_history_id}-topic_summaries.json"

    try:
        yggs_data = load_json_from_blob(topic_summaries_blob_name)
    except Exception as e:
        logging.error(f"Error loading summaries from blob: {e}")
        return error_response("Could not load topic summaries.", 500)

    ygg_summaries = yggs_data.get("ygg_summaries", [])

    if not ygg_summaries or len(ygg_summaries) == 0:
        return error_response("No topic summaries found. Please ensure all summaries are submitted.", 400)

    # Format topic summaries for the prompt
    topic_summaries_text = ""
    for summary in ygg_summaries:
        topic_name = summary.get("topic_name", "Unbekanntes Thema")
        content = summary.get("ygg", "")
        topic_summaries_text += f"\n\n## {topic_name}\n{content}"

    # Load prompt template
    try:
        final_summary_prompt = load_prompt(directory="report", name="final_summary").format(
            topic_summaries=topic_summaries_text
        )
    except Exception as e:
        logging.error(f"Error loading prompt template: {e}")
        return error_response("Could not load prompt template.", 500)

    # Generate final summary using LLM
    llm = get_llm()
    if llm is None:
        return error_response("LLM instance could not be created.", 500)

    try:
        response = llm.invoke(final_summary_prompt)
        final_summary = response.content
    except Exception as e:
        logging.error(f"Error generating final summary: {e}")
        return error_response(f"Error generating final summary: {str(e)}", 500)

    # Save final summary to blob storage
    final_summary_data = {
        "final_summary": final_summary
    }

    try:
        from adapters.az_blob_client import upload_json_to_blob
        upload_json_to_blob(final_summary_blob_name, final_summary_data)
        logging.info(f"Final summary saved to blob: {final_summary_blob_name}")
    except Exception as e:
        logging.error(f"Error saving final summary to blob: {e}")
        # Continue anyway - return the summary even if saving fails

    return func.HttpResponse(
        json.dumps(final_summary_data, ensure_ascii=False, indent=2),
        status_code=200,
        mimetype="application/json"
    )



###################
### Not needed for Rewe prod interview, but for dev purposes and classical YGG app.
###################

# @app.blob_trigger(arg_name="myblob", path="audio-transcripts/{name}",
#                                connection="AzureWebJobsStorage") 
# def summarize_transcript(myblob: func.InputStream) -> None:

#     """
#     Azure Blob Trigger function to summarize a transcript using the LLM.
#     Reads a JSON transcript from a blob, summarizes it, and saves the result to another blob and updates job status in Table Storage.
#     Args:
#         myblob (func.InputStream): The input blob stream containing the transcript JSON.
#     Returns:
#         None
#     """
#     openai_api_version = "2024-12-01-preview"

#     file_name = os.path.basename(myblob.name)
#     logging.info(f"Received blob: {file_name}, size: {myblob.length} bytes")

#     # Get job entity from table using adapter helper
#     try:
#         job_id = os.path.splitext(os.path.basename(myblob.name))[0]
#         filter_str = f"RowKey eq '{job_id}'"
#         table_client = get_table_client_jobstatus()
#         job_entity = list(table_client.query_entities(query_filter=filter_str))[0]
#     except Exception as e:
#         logging.error(f"[Table] Failed to read job entity for {file_name}: {type(e).__name__} - {e}")
#         return

#     # Step 1: Reading Secrets from Key Vault (Whisper Endpoint)
#     try:
#         key_vault_url = os.environ["KEY_VAULT_URL"]
#         credential = DefaultAzureCredential()
#         client = SecretClient(vault_url=key_vault_url, credential=credential)

#         openai_url = client.get_secret("openai-api-url").value
#         openai_key = client.get_secret("openai-api-key").value

#         logging.info(f"[KeyVault] Successfully retrieved secrets from Key Vault.")
#     except Exception as e:
#         logging.error(f"[KeyVault] Could not retrieve secrets: {type(e).__name__} - {e}")
#         return
    
#     # Step 2: Read Blob content & validate file type
#     try:
#         if not file_name.lower().endswith(('.json')):
#             logging.warning(f"[Validation] File {file_name} does not appear to be a json file. Skipping.")
#             return
        
#         data = myblob.read()
#         json_data = json.loads(data)
#         if not json_data:
#             logging.warning(f"[Blob] Blob {file_name} is empty.")
#             return
#         else:
#             transcription = json_data["text"]
#     except Exception as e:
#         logging.error(f"[Blob] Failed to read blob {file_name}: {type(e).__name__} - {e}")
#         return
    
#     # Step 3: Send content to LLM
#     try:
#         client = AzureOpenAI(
#             api_version=openai_api_version,
#             azure_endpoint=openai_url,
#             api_key=openai_key
#         )

#         ygg_prompt = load_prompt(directory="yggs", name="generate_ygg_normal").format(
#             input=transcription
#         )
#         llm = get_llm()
#         structured_llm = llm.with_structured_output(schema=pydantic_models.YggList, include_raw=True)
#         response = structured_llm.invoke(ygg_prompt)
#         parsed_response = response["parsed"]

#         yggs = []
#         for ygg in parsed_response.ygg_list:
#             logging.info(f"Hier ist ein Ygg: {ygg}")
#             yggs.append({"title": ygg.title, "content": ygg.content})

#         result = {
#             "transcription": transcription,
#             "summary": "",
#             "yggs": yggs
#         }

#         logging.info(f"[LLM] LLM summarization succeeded for {file_name}")
#         logging.info(f"[LLM] Full response: {response}")
#         logging.info(f"[LLM] Response text: {ygg}")
#     except Exception as e:
#         logging.error(f"[LLM] Unexpected error: {type(e).__name__} - {e}")
#         return
    
#     # Save result to container and update job status
#     try:
#         output_container = os.environ.get("SUMMARY_OUTPUT_CONTAINER", "yggs-summarized")

#         job_entity["status"] = "summarized"
#         table_client.update_entity(mode="replace", entity=job_entity)
#         logging.info(f"[Table] Status for Job {file_name} updated.")

#         # Use adapter helper for blob upload
#         from adapters.az_blob_client import upload_json_to_blob
#         blob_name = f"{job_id}.json"
#         upload_json_to_blob(blob_name, result)

#         logging.info(f"[Blob] LLM summary saved to {output_container}/{job_id}.json")
#     except Exception as e:
#         logging.error(f"[Blob] Failed to save transcription: {e}")

# @app.route(route="upload_to_graphiti", auth_level=func.AuthLevel.FUNCTION)
# def upload_to_graphiti(req: func.HttpRequest) -> func.HttpResponse:
#     """
#     Endpoint for uploading Yggs to Graphiti.
#     Args:
#         req (func.HttpRequest): The HTTP request containing 'yggs' parameter.
#     Returns:
#         func.HttpResponse: The response indicating success or error.
#     """
#     ygg = get_param(req, 'ygg')
#     title = get_param(req, 'title')
#     group_id = get_param(req, 'group_id')
#     if not ygg or not title:
#         return error_response("Missing required parameters: ygg and title.", 400)
#     if group_id is None:
#         return error_response("Missing required parameter: group_id.", 400)
    
#     episode = {
#         "title": title,
#         "content": ygg,
#         "group_id": group_id
#     }

#     graphiti_client = get_graphiti_client()
#     if graphiti_client:
#         try:
#             asyncio.run(add_episodes_to_graph(graphiti_client, [episode]))
#             logging.info("Ygg uploaded to Graphiti successfully.")
#         except Exception as e:
#             logging.error(f"Failed to upload Ygg to Graphiti: {e}")
#             return error_response(f"Failed to upload Ygg to Graphiti: {e}", 500)

#     return func.HttpResponse(
#         "Ygg uploaded successfully.",
#         status_code=200
#     )

# @app.route(route="cluster_answers", auth_level=func.AuthLevel.FUNCTION)
# def cluster_answers(req: func.HttpRequest) -> func.HttpResponse:
#     """
#     Clusters answers using the LLM and returns the result.
#     Args:
#         req (func.HttpRequest): The HTTP request containing 'answers' and optional 'labels'.
#     Returns:
#         func.HttpResponse: The response containing clustered answers as JSON.
#     """
#     answers = get_param(req, 'answers')
#     cluster_labels = get_param(req, 'labels')
#     if not answers:
#         return error_response("Missing required parameter: answers.", 400)

#     cluster_prompt = load_prompt(directory="report", name="cluster_answers").format(
#         cluster_labels=cluster_labels,
#         responses=answers
#     )
#     llm = get_llm()
#     response = llm.invoke(cluster_prompt)
#     response = json.loads(response.content)

#     return func.HttpResponse(
#         json.dumps(response, ensure_ascii=False, indent=2),
#         mimetype="application/json",
#         status_code=200
#     )

# @app.route(route="simulate_user_response", auth_level=func.AuthLevel.FUNCTION)
# def simulate_user_response(req: func.HttpRequest) -> func.HttpResponse:
#     """
#     Simulates a user response using the LLM and persona data.
#     Args:
#         req (func.HttpRequest): The HTTP request containing 'persona' and 'ai_msg'.
#     Returns:
#         func.HttpResponse: The simulated user response as plain text.
#     """
#     persona = get_param(req, 'persona')
#     ai_msg = get_param(req, 'ai_msg')
#     if not persona:
#         return error_response("Missing required parameter: persona.", 400)

#     simulation_prompt = load_prompt(directory="simulation", name="simulate_user").format(
#         name=persona["name"],
#         role=persona["role"],
#         experience=persona["experience"],
#         department=persona["department"],
#         technical_affinity=persona["technical_affinity"],
#         tools=persona["tools"],
#         copilot_usage=persona["copilot_usage"],
#         ki_opinion=persona["ki_opinion"],
#         answer_style=persona["answer_style"],
#         last_question=ai_msg
#     )

#     llm = get_llm()

#     response = llm.invoke(simulation_prompt)
#     result = response.content
#     return func.HttpResponse(
#         result,
#         status_code=200
#     )

