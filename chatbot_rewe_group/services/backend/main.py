import logging
import os

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional
from langchain_core.messages import AIMessage, HumanMessage

from adapters.az_table_client import (
    store_message, get_full_chat_history, delete_chat_history, delete_state,
    get_state, update_state, create_initial_state, get_chat_history_by_question,
)
from adapters.az_blob_client import (
    load_json_from_blob, append_message_to_blob, append_data_to_blob,
    delete_blob, upload_json_to_blob,
)
from utils.file_loader import load_prompt, load_topics
from utils.llm_utils import get_llm
from utils.helper_functions import extract_meta_comment
import models.pydantic.PydanticModels as pydantic_models
from interview_graph import build_graph

app = FastAPI()


# ---------------------------------------------------------------------------
# Request Models
# ---------------------------------------------------------------------------

class InterviewAgentRequest(BaseModel):
    message: Optional[str] = None
    role: Optional[str] = ""
    user_id: str
    interview_id: str

class InterviewStatusRequest(BaseModel):
    user_id: str
    interview_id: str

class GetSummaryYggsRequest(BaseModel):
    user_id: str
    interview_id: str
    source_dir: str

class DeleteInterviewHistoryRequest(BaseModel):
    user_id: str
    interview_id: str

class GenerateGeneralYggRequest(BaseModel):
    thought: str

class SaveSummaryRequest(BaseModel):
    id: str
    content: str
    user_id: str
    interview_id: str

class SaveFinalSummaryRequest(BaseModel):
    user_id: str
    interview_id: str
    content: str

class GenerateFinalSummaryRequest(BaseModel):
    user_id: str
    interview_id: str


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@app.post("/api/interview_agent")
def interview_agent(req: InterviewAgentRequest):
    message = req.message
    role = req.role or ""
    user_id = req.user_id
    interview_id = req.interview_id

    message_with_feedback = message
    message_without_feedback = message
    feedback = None
    if message:
        message_without_feedback, feedback = extract_meta_comment(message)
        if feedback:
            logging.info(f"Extracted feedback from user message: {feedback}")

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
                message_tag=interview_state.get("current_topic"),
            )
            append_message_to_blob(
                message=message_with_feedback,
                interview_id=interview_id,
                chat_id=interview_state.get("chat_history_id"),
                role=role,
            )
        except Exception as e:
            logging.error(f"Failed to store user message: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to store user message: {e}")

    chat_history_raw = get_chat_history_by_question(
        interview_state.get("chat_history_id"),
        interview_state.get("current_topic"),
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

    if interview_state.get("interview_status") == 2:
        return {
            "ai_message": "Interview bereits beendet.",
            "interview_status": interview_state.get("interview_status"),
        }

    try:
        interview_graph = build_graph()
        result = interview_graph.invoke(interview_state)

        open_topics = result.get("open_topics", [])
        topic_list = load_topics(name="copilot")

        open_topic_names = [t["scope"] for t in topic_list if t["id"] in open_topics]
        completed_topic_names = [
            t["scope"] for t in topic_list
            if t["id"] not in open_topics and t["id"] != result.get("current_topic")
        ]

        return {
            "ai_message": result.get("ai_message", ""),
            "transition_text": result.get("transition_text", ""),
            "interview_status": result.get("interview_status", 0),
            "llm_metadata": result.get("llm_metadata", {}),
            "current_topic": result.get("current_topic_name", ""),
            "open_topics": open_topic_names,
            "completed_topics": completed_topic_names,
        }
    except Exception as e:
        logging.error(f"Interview agent error: {e}")
        raise HTTPException(status_code=500, detail=f"Interview agent error: {e}")


@app.post("/api/interview_status")
def interview_status(req: InterviewStatusRequest):
    user_id = req.user_id
    interview_id = req.interview_id

    interview_state = get_state(user_id, interview_id)
    if not interview_state:
        return {
            "chat_history": [],
            "interview_status": 0,
            "current_topic": "",
            "open_topics": [],
            "completed_topics": [],
        }

    chat_history = get_full_chat_history(interview_state["chat_history_id"])
    interview_status_val = interview_state["interview_status"]
    open_topics = interview_state.get("open_topics", [])
    topic_list = load_topics(name="copilot")
    current_topic = interview_state.get("current_topic_name")

    open_topic_names = [t["scope"] for t in topic_list if t["id"] in open_topics]

    completed_topic_names = []
    for topic in topic_list:
        if topic["id"] not in open_topics and topic["id"] != interview_state.get("current_topic"):
            completed_topic_names.append(topic["scope"])
        elif (
            topic["id"] not in open_topics
            and len(open_topics) == 0
            and interview_state.get("interview_status") == 2
        ):
            current_topic = ""
            completed_topic_names.append(topic["scope"])

    return {
        "chat_history": chat_history,
        "interview_status": interview_status_val,
        "current_topic": current_topic,
        "open_topics": open_topic_names,
        "completed_topics": completed_topic_names,
    }


@app.post("/api/get_summary_yggs")
def get_summary_yggs(req: GetSummaryYggsRequest):
    user_id = req.user_id
    interview_id = req.interview_id
    source_dir = req.source_dir

    interview_state = get_state(user_id, interview_id)
    if interview_state is None:
        return {"summary": "", "ygg_summaries": {}}

    user_information = interview_state.get("user_information", "")
    chat_history_id = interview_state.get("chat_history_id")
    blob_name = f"{source_dir}/topic-summaries/{interview_id}-{chat_history_id}-topic_summaries.json"
    yggs = load_json_from_blob(blob_name)

    if user_information:
        return {"summary": user_information, "ygg_summaries": yggs.get("ygg_summaries", {})}

    logging.info("No user information found.")
    return {"summary": "", "ygg_summaries": {}}


@app.post("/api/delete_interview_history")
def delete_interview_history(req: DeleteInterviewHistoryRequest):
    user_id = req.user_id
    interview_id = req.interview_id

    interview_state = get_state(user_id, interview_id)
    try:
        delete_state(interview_id=interview_id, user_id=user_id)
        if interview_state:
            delete_chat_history(chat_history_id=interview_state["chat_history_id"])
        return {"message": "Deleted history."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error while deleting the history: {e}")


@app.post("/api/generate_general_ygg")
def generate_general_ygg(req: GenerateGeneralYggRequest):
    thought = req.thought

    llm = get_llm()
    if llm is None:
        raise HTTPException(status_code=500, detail="LLM instance could not be created.")

    ygg_prompt = load_prompt(directory="yggs", name="generate_ygg_normal").format(input=thought)
    structured_llm = llm.with_structured_output(schema=pydantic_models.YggList, include_raw=True)
    response = structured_llm.invoke(ygg_prompt)
    parsed_response = response["parsed"]

    yggs = [{"title": ygg.title, "content": ygg.content} for ygg in parsed_response.ygg_list]

    return {"transcription": thought, "summary": "", "yggs": yggs}


@app.post("/api/save_summary")
def save_summary(req: SaveSummaryRequest):
    topic_id = req.id
    content = req.content
    user_id = req.user_id
    interview_id = req.interview_id

    topics = load_topics(name="copilot")

    interview_state = get_state(user_id, interview_id)
    if interview_state is None:
        raise HTTPException(status_code=404, detail="Interview not found.")
    chat_id = interview_state.get("chat_history_id")

    topic_name = next((t["scope"] for t in topics if t["id"] == topic_id), None)
    if not topic_name:
        raise HTTPException(status_code=400, detail=f"Topic id '{topic_id}' not found in topics list.")

    summary_obj = {"topic_id": topic_id, "topic_name": topic_name, "ygg": content}

    try:
        append_data_to_blob("temporary-data", summary_obj, interview_id, user_id, chat_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error saving summary: {str(e)}")

    return {"message": "Summary saved successfully.", "topic_id": topic_id, "summary": content}


@app.post("/api/save_final_summary")
def save_final_summary(req: SaveFinalSummaryRequest):
    user_id = req.user_id
    interview_id = req.interview_id
    content = req.content

    interview_state = get_state(user_id, interview_id)
    if interview_state is None:
        raise HTTPException(status_code=404, detail="Interview not found.")

    final_summary_obj = {"final_summary": content}
    saved_blob_name = f"saved-data/final-summaries/{interview_id}-{user_id}-final_summary.json"
    temp_blob_name = f"temporary-data/final-summaries/{interview_id}-{user_id}-final_summary.json"

    try:
        upload_json_to_blob(saved_blob_name, final_summary_obj)
        delete_blob(temp_blob_name)
    except Exception as e:
        logging.error(f"Error saving final summary: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error saving final summary: {str(e)}")

    chat_id = interview_state.get("chat_history_id")

    # Copy message history from temporary-data to saved-data
    try:
        msg_blob = load_json_from_blob(f"temporary-data/message-history/{interview_id}-{chat_id}-messages.json")
        if msg_blob:
            upload_json_to_blob(f"saved-data/message-history/{interview_id}-{chat_id}-messages.json", msg_blob)
            delete_blob(f"temporary-data/message-history/{interview_id}-{chat_id}-messages.json")
    except Exception as e:
        logging.error(f"Error copying message history: {str(e)}")

    # Copy topic summaries from temporary-data to saved-data
    try:
        topic_blob = load_json_from_blob(f"temporary-data/topic-summaries/{interview_id}-{chat_id}-topic_summaries.json")
        if topic_blob:
            upload_json_to_blob(f"saved-data/topic-summaries/{interview_id}-{chat_id}-topic_summaries.json", topic_blob)
            delete_blob(f"temporary-data/topic-summaries/{interview_id}-{chat_id}-topic_summaries.json")
    except Exception as e:
        logging.error(f"Error copying topic summaries: {str(e)}")

    try:
        interview_state["interview_status"] = 3
        update_state(state=interview_state)
    except Exception as e:
        logging.error(f"Error updating interview status: {str(e)}")

    return {"message": "Final summary saved successfully.", "content": content, "interview_status": 3}


@app.post("/api/generate_final_summary")
def generate_final_summary(req: GenerateFinalSummaryRequest):
    user_id = req.user_id
    interview_id = req.interview_id

    interview_state = get_state(user_id, interview_id)
    if interview_state is None:
        raise HTTPException(status_code=404, detail="Interview not found.")

    interview_status_val = interview_state.get("interview_status")

    if interview_status_val == 3:
        saved_summary = load_json_from_blob(
            f"saved-data/final-summaries/{interview_id}-{user_id}-final_summary.json"
        )
        if saved_summary and saved_summary.get("final_summary"):
            return saved_summary
        raise HTTPException(status_code=500, detail="Final summary submitted but not found in storage.")

    if interview_status_val != 2:
        raise HTTPException(status_code=400, detail="Interview is not yet completed.")

    chat_history_id = interview_state.get("chat_history_id")
    final_summary_blob_name = f"temporary-data/final-summaries/{interview_id}-{user_id}-final_summary.json"

    existing_summary = load_json_from_blob(final_summary_blob_name)
    if existing_summary and existing_summary.get("final_summary"):
        return existing_summary

    try:
        yggs_data = load_json_from_blob(
            f"temporary-data/topic-summaries/{interview_id}-{chat_history_id}-topic_summaries.json"
        )
    except Exception as e:
        logging.error(f"Error loading summaries from blob: {e}")
        raise HTTPException(status_code=500, detail="Could not load topic summaries.")

    ygg_summaries = yggs_data.get("ygg_summaries", [])
    if not ygg_summaries:
        raise HTTPException(status_code=400, detail="No topic summaries found.")

    topic_summaries_text = "".join(
        f"\n\n## {s.get('topic_name', 'Unbekanntes Thema')}\n{s.get('ygg', '')}"
        for s in ygg_summaries
    )

    try:
        final_summary_prompt = load_prompt(directory="report", name="final_summary").format(
            topic_summaries=topic_summaries_text
        )
    except Exception as e:
        logging.error(f"Error loading prompt template: {e}")
        raise HTTPException(status_code=500, detail="Could not load prompt template.")

    llm = get_llm()
    if llm is None:
        raise HTTPException(status_code=500, detail="LLM instance could not be created.")

    try:
        response = llm.invoke(final_summary_prompt)
        final_summary = response.content
    except Exception as e:
        logging.error(f"Error generating final summary: {e}")
        raise HTTPException(status_code=500, detail=f"Error generating final summary: {str(e)}")

    final_summary_data = {"final_summary": final_summary}

    try:
        upload_json_to_blob(final_summary_blob_name, final_summary_data)
    except Exception as e:
        logging.error(f"Error saving final summary to blob: {e}")

    return final_summary_data
