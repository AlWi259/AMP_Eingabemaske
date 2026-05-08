from typing import TypedDict, List
from langchain_core.messages import HumanMessage
from models.llm.LLMMetadata import LLMMetadata

class InterviewState(TypedDict):
    """
    Represents the full state of an interview session for a user.
    
    Attributes:
        interview_id (str): Unique identifier for the interview.
        user_id (str): Unique identifier for the user.
        interview_status (bool): 1 for started, 0 for not started.
        department (str): Department of the interviewee.
        open_questions (List[int]): List of IDs for open questions.
        chat_history (List): List of chat messages (AI and user).
        chat_history_id (str): Unique identifier for the chat history.
        intro_iterations (int): Number of introduction iterations.
        active_question_id (int): ID of the currently active question.
        active_question (str): Text of the currently active question.
        active_question_context (str): Context for the active question.
        active_question_iterations (int): Number of iterations for the active question.
        last_question (str): The last question asked.
        ai_message (str): The last AI message sent.
        psychological_prompt (HumanMessage): Prompt for psychological analysis.
        psychological_analysis (str): Result of psychological analysis.
        psychological_recommendation (str): Recommendation from psychological expert.
        technical_prompt (HumanMessage): Prompt for technical analysis.
        technical_analysis (str): Result of technical analysis.
        followup (bool): Whether a follow-up is required.
        user_information (str): Additional user information.
        llm_metadata (LLMMetadata): Metadata about LLM token usage.
    """
    interview_id: str
    user_id: str
    interview_status: bool # (1 for started, 0 for not started)
    department: str
    open_topics: List[str]
    chat_history: List
    chat_history_id: str
    intro_iterations: int
    active_question_iterations: int
    last_question: str
    ai_message: str
    next_step_suggestion: str # Suggestion for the next step in the interview process
    psychological_prompt: HumanMessage
    psychological_analysis: str
    psychological_recommendation: str
    technical_prompt: HumanMessage
    technical_analysis: str
    followup: bool
    user_information: str
    llm_metadata: LLMMetadata
    current_topic: str  # ID of the currently active topic/cluster
    current_topic_name: str  # Name of the currently active topic/cluster
    current_topic_points: List[str]  # Points of the currently active topic/cluster
    current_topic_probing_limit: int  # Probing limit for the current topic
    probing_analysis: str  # Evaluation of probing needs
    topic_analysis: str  # Analysis of the current topic
    topic_summary: str  # Summary of the current topic
    probing_count: int  # Number of questions left to ask in the current topic
    transition_text: str  # First two paragraphs of transition (closing + motivation)
