import copy
import json
import os
from typing import Any, Dict
from adapters.az_table_client import get_all_answers, store_message, update_state
from adapters.az_blob_client import append_message_to_blob
from utils.file_loader import load_prompt, load_topics
from langchain_core.messages import HumanMessage
from models.pydantic.PydanticModels import AnswerEvaluation
from utils.llm_utils import store_token_usage
import logging

def check_interview_status(state: Dict[str, Any]) -> str:
    """
    Decide the next node based on the current interview status.
    Args:
        state: The current interview state dictionary.
    Returns:
        The name of the next node as a string.
    """
    if state["interview_status"] == 0:
        return "interview_intro"
    elif state["interview_status"] == 1:
        return "flow_util_node_1"
    
def check_if_interview_finished(state: Dict[str, Any]) -> str:
    """
    Checks if the interview is finished based on the current state.
    Args:
        state: The current interview state dictionary.
    Returns:
        The name of the next node as a string ("end_interview" if finished, else "transition_next_question").
    """
    if len(state["open_topics"]) == 0:

        # state["interview_status"] = 2
        logging.info("All topics are covered, ending interview.")
        return "end_interview"
    else:
        return "transition_next_question"
    
def flow_util_node_1(state: Dict[str, Any]) -> str:
    """
    Placeholder function for flow purposes.
    This function does not perform any operations and simply returns the current state.
    Args:
        state: The current interview state dictionary.
    Returns:
        state: The current interview state dictionary.
    """
    # This is a placeholder needed for flow purposes, it just returns the current state.
    return state

def flow_util_node_2(state: Dict[str, Any]) -> str:
    """
    Placeholder function for flow purposes.
    This function does not perform any operations and simply returns the current state.
    Args:
        state: The current interview state dictionary.
    Returns:
        state: The current interview state dictionary.
    """
    # This is a placeholder needed for flow purposes, it just returns the current state.
    return state

def flow_util_node_3(state: Dict[str, Any]) -> str:
    """
    Placeholder function for flow purposes.
    This function does not perform any operations and simply returns the current state.
    Args:
        state: The current interview state dictionary.
    Returns:
        state: The current interview state dictionary.
    """
    # This is a placeholder needed for flow purposes, it just returns the current state.

    return state

def flow_util_node_4(state: Dict[str, Any]) -> str:
    """
    Placeholder function for flow purposes.
    This function does not perform any operations and simply returns the current state.
    Args:
        state: The current interview state dictionary.
    Returns:
        state: The current interview state dictionary.
    """
    # This is a placeholder needed for flow purposes, it just returns the current state.
    return state

def evaluate_next_step(state: Dict[str, Any], llm=None) -> str:
    """
    Checks what next step in the interview should be taken.
    Args:
        state: The current interview state dictionary.
    Returns:
        The name of the next node as a string ("choose_next_question" if not all points are covered, else "summarize_answer" or next cluster node).
    """
    chat_history = copy.deepcopy(state["chat_history"])

    if llm is None:
        raise ValueError("LLM instance must be provided to evaluate_topic.")

    # load prompt evaluate_next_step
    evaluate_topic_prompt = load_prompt(directory="interview", name="evaluate_next_step").format(
        psychological_report=state["psychological_recommendation"],
        technical_report=state["technical_analysis"],
        probing_recommendation=state["probing_analysis"],
        topic_overview=state["topic_analysis"],
        budget=state["probing_count"]
    )
    message = HumanMessage(content=evaluate_topic_prompt)
    chat_history.append(message)

    response = llm.invoke(chat_history)
    state["llm_metadata"] = store_token_usage(response, state["llm_metadata"])

    # Update state with parsed response
    if response.content == "fertig":
        state["next_step_suggestion"] = "fertig"
        logging.info(f"Topic {state["current_topic_name"]} is covered.")
    else:
        state["next_step_suggestion"] = response.content

    return state

def check_topic_evaluation(state: Dict[str, Any]) -> str:
    """
    Checks the topic evaluation to determine the next node.
    Args:
        state: The current interview state dictionary.
    Returns:
        The name of the next node as a string.
    """
    if state["next_step_suggestion"] == "fertig":
        return "flow_util_node_2"
    else:
        return "formulate_question"

def transition_next_question(state: Dict[str, Any], llm=None) -> Dict[str, Any]:
    """
    Handles the transition to the next question, updating state and context.
    Args:
        state: The current interview state dictionary.
    Returns:
        The updated interview state dictionary.
    """
    if llm is None:
        raise ValueError("LLM instance must be provided to transition_next_question.")
    
    chat_history = copy.deepcopy(state["chat_history"])

    topics = load_topics(name="copilot")
    next_topic_id = state["open_topics"][0]
    

    for topic in topics:
        if next_topic_id == topic["id"]:
            next_topic_name = topic["scope"]
            next_topic_points = topic["points"]
            next_topic_probing_limit = topic["probing_limit"]
            break

    open_topics_length = len(state["open_topics"])
    completed_topics_length = len(topics) - open_topics_length

    # Remove the new topic from open topics
    state["open_topics"].remove(next_topic_id)

    transition_next_question_prompt = load_prompt(directory="interview", name="transition_next_question").format(
        current_topic = state["current_topic_name"],
        new_topic = next_topic_name,
        new_topic_points = next_topic_points,
        completed_topics_length=completed_topics_length,
        topics_length=len(topics)
    )
    message = HumanMessage(content=transition_next_question_prompt)
    chat_history.append(message)
    response = llm.invoke(chat_history)
    state["llm_metadata"] = store_token_usage(response, state["llm_metadata"])

    # Split response into paragraphs (separated by double newlines)
    paragraphs = [p.strip() for p in response.content.split('\n\n') if p.strip()]

    # First two paragraphs are transition text, third is the question
    if len(paragraphs) >= 3:
        transition_text = '\n\n'.join(paragraphs[:2])
        ai_message = paragraphs[2]
    else:
        # Fallback if format is unexpected
        transition_text = ""
        ai_message = response.content

    state["transition_text"] = transition_text
    state["ai_message"] = ai_message

    state["current_topic"] = next_topic_id
    state["current_topic_name"] = next_topic_name
    state["current_topic_points"] = next_topic_points
    state["probing_count"] = next_topic_probing_limit - 1  # Reset probing count for the new topic

    if transition_text:
        store_message(chat_history_id=state["chat_history_id"], role="assistant", message=transition_text, message_tag=state["current_topic"])
    store_message(chat_history_id=state["chat_history_id"], role="assistant", message=ai_message, message_tag=state["current_topic"])

    append_message_to_blob(message=response.content, interview_id=state["interview_id"], chat_id=state["chat_history_id"], role="assistant")
    update_state(state=state)
    return state

def end_interview(state: Dict[str, Any], llm=None) -> Dict[str, Any]:
    """
    Ends the interview and generates a closing message.
    Args:
        state: The current interview state dictionary.
    Returns:
        The updated interview state dictionary.
    """
    if llm is None:
        raise ValueError("LLM instance must be provided to end_interview.")
    chat_history = copy.deepcopy(state["chat_history"])
    end_prompt = """
Du bist ein virtueller Interviewer, der ein strukturiertes Interview über die
Nutzung von Microsoft 365 Copilot führt.

Das Interview kann jetzt beendet werden, da alle Fragen hinreichend beantwortet wurden und/oder der Nutzer keine weiteren Informationen mehr liefern kann.

Bitte beende das Interview entsprechend und verabschiede dich.
"""
    message = HumanMessage(content=end_prompt)
    chat_history.append(message)
    response = llm.invoke(chat_history)
    state["llm_metadata"] = store_token_usage(response, state["llm_metadata"])
    state["ai_message"] = response.content
    state["interview_status"] = 2
    store_message(chat_history_id=state["chat_history_id"], role="assistant", message=response.content)
    append_message_to_blob(message=response.content, interview_id=state["interview_id"], chat_id=state["chat_history_id"], role="assistant")
    update_state(state=state)
    return state
