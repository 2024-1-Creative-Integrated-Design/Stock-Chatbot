from deepeval.metrics import GEval
from deepeval.test_case import LLMTestCaseParams, LLMTestCase
from langchain_elasticsearch import ElasticsearchStore
from llm_integrations import get_llm
from elasticsearch_client import (
    elasticsearch_client
)
from langchain_openai import OpenAIEmbeddings
import json
import os
from dotenv import load_dotenv

load_dotenv(override=True)

NEWS_INDEX = "news"
STOCK_INDEX = "stock"
REPORT_INDEX = "report"
INDEX_CHAT_HISTORY = "chat-history"
SESSION_ID_TAG = "[SESSION_ID]"
SOURCE_TAG = "[SOURCE]"
DONE_TAG = "[DONE]"

embedding = OpenAIEmbeddings(openai_api_key=os.getenv("OPENAI_API_KEY"), model="text-embedding-3-small")
news_store = ElasticsearchStore(
    es_connection=elasticsearch_client,
    index_name=NEWS_INDEX,
    embedding=embedding,
)
stock_store = ElasticsearchStore(
    es_connection=elasticsearch_client,
    index_name=STOCK_INDEX,
    embedding=embedding,
)
report_store = ElasticsearchStore(
    es_connection=elasticsearch_client,
    index_name=REPORT_INDEX,
    embedding=embedding,
)

# G-Eval 메트릭 초기화
correctness_metric = GEval(
    name="Correctness",
    criteria="Determine whether the actual output is factually correct based on the expected output.",
    evaluation_steps=[
        "Check whether the facts in 'actual output' contradict any facts in 'expected output'",
        "Heavily penalize omission of detail",
        "Vague language, or contradicting opinions, are OK"
    ],
    evaluation_params=[LLMTestCaseParams.INPUT, LLMTestCaseParams.ACTUAL_OUTPUT],
)

relevance_metric = GEval(
    name="Relevance",
    criteria="Determine whether the actual output is relevant to the input question.",
    evaluation_steps=[
        "Check whether the response directly addresses the question",
        "Evaluate the presence of irrelevant information"
    ],
    evaluation_params=[LLMTestCaseParams.INPUT, LLMTestCaseParams.ACTUAL_OUTPUT],
)

fluency_metric = GEval(
    name="Fluency",
    criteria="Determine whether the actual output is fluent and well-formed.",
    evaluation_steps=[
        "Evaluate the grammatical correctness of the response",
        "Assess the naturalness of the language used"
    ],
    evaluation_params=[LLMTestCaseParams.ACTUAL_OUTPUT],
)

coherence_metric = GEval(
    name="Coherence",
    criteria="Determine whether the actual output is coherent and logically structured.",
    evaluation_steps=[
        "Check the logical flow of the response",
        "Ensure the response is easy to understand and follow"
    ],
    evaluation_params=[LLMTestCaseParams.ACTUAL_OUTPUT],
)


def ask_question_with_geval(question, expected_answer):
    condensed_question = question
    news = news_store.as_retriever().invoke(condensed_question)
    stock = stock_store.as_retriever(search_kwargs={'k': 2}).invoke(condensed_question)
    reports = report_store.as_retriever().invoke(condensed_question)
    docs = news + stock + reports
    source = ""
    for doc in docs:
         doc_source = {**doc.metadata, "page_content": doc.page_content}
         source += json.dumps(doc_source, indent=4, ensure_ascii=False) + "\n"
    context = ""
    for doc in docs:
        context += "NAME: " + doc.metadata['name'] + "\n" + "PASSAGE: " + doc.page_content + "\n"


    qa_prompt = f"""
    You are a stock analyst analyzing Samsung Electronics, SK Hynix, NVIDIA, and AMD.
    Use the following passages and chat history to answer the user's question about the companies. 
    Each passage has a NAME which is the TITLE of the document. After your answer, leave a blank line and then give the source name of the passages you answered from. Put them in a comma separated list, prefixed with SOURCES:.
    You must answer in korean.

    Example:

    Question: SK 하이닉스의 요즘 주가가 우상향하는 이유가 뭐야?
    Response:
    하이닉스의 주가가 상승하는 이유는 올해 영업이익이 역대 최대를 기록할 것이라는 전망 때문입니다.

    SOURCES: SK하이닉스 역대 최대 실적 예상


    If you don't know the answer, just say that you don't know, don't try to make up an answer.

    ----
    {context}
    ---

    Question: {question}
    Response:
    
    """

    answer = ""
    for chunk in get_llm().stream(qa_prompt):
        content = chunk.content.replace(
            "\n", " "
        ) 
        answer += chunk.content

    index = answer.find("SOURCES:")

    if index != -1:
        answer = answer[:index]

    test_case = LLMTestCase(
        input=question,
        actual_output=answer,
        expected_output=expected_answer
    )

    # Perform the evaluation for each metric
    correctness_metric.measure(test_case)
    relevance_metric.measure(test_case)
    fluency_metric.measure(test_case)
    coherence_metric.measure(test_case)

    # Print the scores and reasons
    print(f"Correctness Score for '{question}': {correctness_metric.score} - Reason: {correctness_metric.reason}")
    print(f"Relevance Score for '{question}': {relevance_metric.score} - Reason: {relevance_metric.reason}")
    print(f"Fluency Score for '{question}': {fluency_metric.score} - Reason: {fluency_metric.reason}")
    print(f"Coherence Score for '{question}': {coherence_metric.score} - Reason: {coherence_metric.reason}")


if __name__ == "__main__":
    ask_question_with_geval(
        question="엔비디아의 요즘 주가가 우상향하는 이유가 뭐야?", 
        expected_answer="엔비디아의 주가가 상승하는 이유는 올해 영업이익이 역대 최대를 기록할 것이라는 전망 때문입니다."
        )