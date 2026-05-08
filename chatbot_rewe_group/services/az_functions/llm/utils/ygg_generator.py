from utils.file_loader import load_prompt
from models.pydantic.PydanticModels import InterviewSummaryYggs
from langchain_core.messages import HumanMessage

def generate_interview_yggs(chat_history, llm):
    ygg_prompt = load_prompt(directory="yggs", name="generate_ygg")
    prompt_message = HumanMessage(content=ygg_prompt)
    chat_history.append(prompt_message)

    structured_llm = llm.with_structured_output(
        schema=InterviewSummaryYggs, include_raw=True
    )
    response = structured_llm.invoke(chat_history)
    parsed_response = response["parsed"]
    yggs = {
        "function_yggs": {},
        "general_yggs": []
    }
    for item in parsed_response.ygg_list:
        details = item.dict()
        function = details.pop("function")
        yggs["function_yggs"][function] = details
    for item in parsed_response.ygg_list_all:
        yggs["general_yggs"].append(item.dict())

    return yggs
