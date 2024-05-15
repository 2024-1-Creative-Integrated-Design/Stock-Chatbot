from langchain_anthropic import ChatAnthropic
from langchain_openai import ChatOpenAI
import os


LLM_TYPE = os.getenv("LLM_TYPE", "openai")

def init_gpt4_turbo(temperature):
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    return ChatOpenAI(
        model="gpt-4-turbo-preview", openai_api_key=OPENAI_API_KEY, streaming=True, temperature=temperature
    )

def init_claude3(temperature):
    ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
    return ChatAnthropic(
        model="claude-3-opus-20240229", anthropic_api_key=ANTHROPIC_API_KEY, streaming=True, temperature=temperature
    )

MAP_LLM_TYPE_TO_CHAT_MODEL = {
    "openai": init_gpt4_turbo,
    "anthropic": init_claude3
}

def get_llm(temperature=0):
    if not LLM_TYPE in MAP_LLM_TYPE_TO_CHAT_MODEL:
        raise Exception(
            "LLM type not found. Please set LLM_TYPE to one of: "
            + ", ".join(MAP_LLM_TYPE_TO_CHAT_MODEL.keys())
            + "."
        )

    return MAP_LLM_TYPE_TO_CHAT_MODEL[LLM_TYPE](temperature=temperature)
