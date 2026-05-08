import copy
from langchain_core.messages import HumanMessage
from utils.file_loader import load_prompt, load_topics
from utils.llm_utils import store_token_usage

from typing import Any, Dict

def formulate_expert_prompts(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Prepares expert prompts for psychological and technical analysis.
    Args:
        state: The current interview state dictionary.
    Returns:
        The updated interview state dictionary.
    """
    

    
    return state

def topic_expert(state: Dict[str, Any], llm=None) -> str:
    """
    Checks if all points from the current cluster (topic area) are fulfilled/covered in the interview state.
    Args:
        state: The current interview state dictionary.
    Returns:
        The name of the next node as a string ("choose_next_question" if not all points are covered, else "summarize_answer" or next cluster node).
    """
    chat_history = copy.deepcopy(state["chat_history"])

    if llm is None:
        raise ValueError("LLM instance must be provided to evaluate_topic.")

    # load prompt evaluate_topic
    evaluate_topic_prompt = load_prompt(directory="interview", name="topic_expert").format(
        topic=state["current_topic_name"],
        points=state["current_topic_points"],
        budget=state["probing_count"]  # Use probing_count as question budget
    )
    message = HumanMessage(content=evaluate_topic_prompt)
    chat_history.append(message)

    response = llm.invoke(chat_history)
    state["llm_metadata"] = store_token_usage(response, state["llm_metadata"])
    state["topic_analysis"] = response.content

    return state

def probing_expert(state: Dict[str, Any], llm=None) -> Dict[str, str]:
    """
    Invokes the LLM for analyzing if a probing is necessary.
    Args:
        state: The current interview state dictionary.
        llm: The language model instance to use.
    Returns:
        Dict with 'probing_analysis'.
    """
    if llm is None:
        raise ValueError("llm instance must be provided to probing_expert")
    chat_history = copy.deepcopy(state["chat_history"])
    probing_prompt = load_prompt(directory="interview", name="probing_expert").format(
        topic=state["current_topic_name"],
        topic_points=state["current_topic_points"]
    )
    message = HumanMessage(content=probing_prompt)
    chat_history.append(message)
    response = llm.invoke(chat_history)
    state["llm_metadata"] = store_token_usage(response, state["llm_metadata"])
    return {
        "probing_analysis": response.content
    }

def psychological_expert(state: Dict[str, Any], llm=None) -> Dict[str, str]:
    """
    Invokes the LLM for psychological analysis and recommendation.
    Args:
        state: The current interview state dictionary.
        llm: The language model instance to use.
    Returns:
        Dict with 'psychological_analysis' and 'psychological_recommendation'.
    """
    if llm is None:
        raise ValueError("llm instance must be provided to psychological_expert")
    from models.pydantic.PydanticModels import PsychologicalExpert
    chat_history = copy.deepcopy(state["chat_history"])

    # Prepare psychological expert prompt
    psychological_prompt = load_prompt(directory="interview", name="psychological_expert")
    psychological_prompt_message = HumanMessage(content=psychological_prompt)

    chat_history.append(psychological_prompt_message)
    response = llm.invoke(chat_history)
    state["llm_metadata"] = store_token_usage(response, state["llm_metadata"])
    return {
        "psychological_recommendation": response.content
    }

def technical_expert(state: Dict[str, Any], llm=None) -> Dict[str, str]:
    """
    Invokes the LLM for technical analysis of the answer.
    Args:
        state: The current interview state dictionary.
        llm: The language model instance to use.
    Returns:
        Dict with 'technical_analysis'.
    """
    if llm is None:
        raise ValueError("llm instance must be provided to technical_expert")
    chat_history = copy.deepcopy(state["chat_history"])

    # Prepare technical expert prompt
    technical_prompt = load_prompt(directory="interview", name="technical_expert")
    technical_prompt_message = HumanMessage(content=technical_prompt)

    chat_history.append(technical_prompt_message)
    response = llm.invoke(chat_history)
    state["llm_metadata"] = store_token_usage(response, state["llm_metadata"])
    return {
        "technical_analysis": response.content
    }
