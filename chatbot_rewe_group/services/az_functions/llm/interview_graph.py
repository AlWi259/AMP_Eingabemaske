"""
Main LangGraph state machine wiring for the interview agent.
Imports all node functions from state_nodes submodules and exposes build_graph().
"""

from langgraph.graph import StateGraph, START, END
from models.interview.InterviewState import InterviewState

from state_nodes.intro_nodes import interview_intro
from state_nodes.expert_nodes import formulate_expert_prompts, psychological_expert, technical_expert, probing_expert, topic_expert
from state_nodes.question_nodes import formulate_question, polish_question
from state_nodes.summary_nodes import summarize_chat_history, generate_interview_yggs
from state_nodes.flow_nodes import flow_util_node_1, flow_util_node_2, flow_util_node_3, flow_util_node_4, check_topic_evaluation, transition_next_question, end_interview, evaluate_next_step, check_interview_status, check_if_interview_finished

from utils.llm_utils import get_llm

class InterviewAgent:
    def __init__(self, llm):
        self.llm = llm

    def interview_intro(self, state):
        return interview_intro(state, llm=self.llm)

    def evaluate_next_step(self, state):
        return evaluate_next_step(state, llm=self.llm)
    
    def summarize_chat_history(self, state):
        return summarize_chat_history(state, llm=self.llm)
    
    def generate_interview_yggs(self, state):
        return generate_interview_yggs(state, llm=self.llm)

    def formulate_expert_prompts(self, state):
        return formulate_expert_prompts(state)

    def topic_expert(self, state):
        return topic_expert(state, llm=self.llm)
    
    def probing_expert(self, state):
        return probing_expert(state, llm=self.llm)

    def technical_expert(self, state):
        return technical_expert(state, llm=self.llm)

    def psychological_expert(self, state):
        return psychological_expert(state, llm=self.llm)

    def transition_next_question(self, state):
        return transition_next_question(state, llm=self.llm)
    
    def formulate_question(self, state):
        return formulate_question(state, llm=self.llm)

    def polish_question(self, state):
        return polish_question(state, llm=self.llm)

    def end_interview(self, state):
        return end_interview(state, llm=self.llm)

    # Add more methods as needed for other nodes

def build_graph() -> StateGraph:
    llm = get_llm()
    agent = InterviewAgent(llm)
    graph_builder = StateGraph(InterviewState)

    graph_builder.add_node("interview_intro", agent.interview_intro)
    graph_builder.add_node("flow_util_node_1", flow_util_node_1)
    graph_builder.add_node("flow_util_node_2", flow_util_node_2)
    graph_builder.add_node("flow_util_node_3", flow_util_node_3, defer=True)
    graph_builder.add_node("flow_util_node_4", flow_util_node_4, defer=True)
    graph_builder.add_node("topic_expert", agent.topic_expert)
    graph_builder.add_node("probing_expert", agent.probing_expert)
    graph_builder.add_node("evaluate_next_step", agent.evaluate_next_step, defer=True)
    graph_builder.add_node("formulate_expert_prompts", agent.formulate_expert_prompts)
    graph_builder.add_node("technical_expert", agent.technical_expert)
    graph_builder.add_node("psychological_expert", agent.psychological_expert)
    graph_builder.add_node("summarize_chat_history", agent.summarize_chat_history)
    graph_builder.add_node("generate_interview_yggs", agent.generate_interview_yggs, defer=True)
    graph_builder.add_node("transition_next_question", agent.transition_next_question, defer=True)
    graph_builder.add_node("formulate_question", agent.formulate_question, defer=True)
    graph_builder.add_node("polish_question", agent.polish_question)
    graph_builder.add_node("end_interview", agent.end_interview)

    # Add your edges as before...
    graph_builder.add_conditional_edges(START, check_interview_status)

    graph_builder.add_edge("flow_util_node_1", "topic_expert")
    graph_builder.add_edge("flow_util_node_1", "probing_expert")
    graph_builder.add_edge("flow_util_node_1", "technical_expert")
    graph_builder.add_edge("flow_util_node_1", "psychological_expert")
    graph_builder.add_edge("topic_expert", "evaluate_next_step")
    graph_builder.add_edge("probing_expert", "evaluate_next_step")
    graph_builder.add_edge("technical_expert", "evaluate_next_step")
    graph_builder.add_edge("psychological_expert", "evaluate_next_step")
    graph_builder.add_conditional_edges("evaluate_next_step", check_topic_evaluation)

    graph_builder.add_edge("flow_util_node_2", "generate_interview_yggs")
    graph_builder.add_edge("flow_util_node_2", "summarize_chat_history")
    graph_builder.add_edge("summarize_chat_history", "flow_util_node_3")
    graph_builder.add_conditional_edges("flow_util_node_3", check_if_interview_finished)
    graph_builder.add_edge("transition_next_question", "flow_util_node_4")
    graph_builder.add_edge("flow_util_node_4", END)

    graph_builder.add_edge("formulate_question", "polish_question")
    graph_builder.add_edge("polish_question", END)
    
    graph_builder.add_edge("end_interview", END)

    return graph_builder.compile()

__all__ = ["build_graph"]
