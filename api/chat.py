from langchain_elasticsearch import ElasticsearchStore
from llm_integrations import get_llm
from elasticsearch_client import (
    elasticsearch_client,
    get_elasticsearch_chat_message_history,
)
from langchain_openai import OpenAIEmbeddings
from flask import render_template, stream_with_context, current_app
import json
import os
import sys
from trulens_eval.feedback.provider import OpenAI
from langchain_core.tools import tool
from dotenv import load_dotenv

basedir = os.path.abspath(os.path.dirname(__file__))
sys.path.append(f"{basedir}/../")
from data import korea_investment

load_dotenv(override=True)

NEWS_INDEX = "news"
STOCK_INDEX = "stock"
REPORT_INDEX = "report"
INDEX_CHAT_HISTORY = "chat-history"
SESSION_ID_TAG = "[SESSION_ID]"
SOURCE_TAG = "[SOURCE]"
DONE_TAG = "[DONE]"
EVAL_TAG = "[EVAL]"

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


@stream_with_context
def ask_question(question, session_id):
    yield f"data: {SESSION_ID_TAG} {session_id}\n\n"
    current_app.logger.debug("Chat session ID: %s", session_id)

    chat_history = get_elasticsearch_chat_message_history(
        INDEX_CHAT_HISTORY, session_id
    )

    if len(chat_history.messages) > 0:
        # create a condensed question
        condense_question_prompt = render_template(
            "condense_question_prompt.txt",
            question=question,
            chat_history=chat_history.messages,
        )
        condensed_question = get_llm().invoke(condense_question_prompt).content
    else:
        condensed_question = question

    current_app.logger.debug("Condensed question: %s", condensed_question)
    current_app.logger.debug("Question: %s", question)

    news = news_store.as_retriever().invoke(condensed_question)
    stock = stock_store.as_retriever(search_kwargs={'k': 2}).invoke(condensed_question)
    reports = report_store.as_retriever().invoke(condensed_question)
    docs = news + stock + reports
    context=""
    for doc in docs:
        doc_source = {**doc.metadata, "page_content": doc.page_content}
        context += "source_name: " + doc.metadata['name'] + "\n" + "source_content: " + doc.page_content + "\n"
        current_app.logger.debug(
            "Retrieved document passage from: %s", doc.metadata["name"]
        )
        yield f"data: {SOURCE_TAG} {json.dumps(doc_source)}\n\n"
    stock_info = korea_investment.fetch_real_time_all()
    
    qa_prompt = render_template(
        "rag_prompt.txt",
        question=question,
        docs=docs,
        chat_history=chat_history.messages,
        stock_info=stock_info,
    )

    answer = ""
    for chunk in get_llm().stream(qa_prompt):
        content = chunk.content.replace(
            "\n", " "
        ) 
        yield f"data: {content}\n\n"
        answer += chunk.content

    yield f"data: {DONE_TAG}\n\n"
    current_app.logger.debug("Answer: %s", answer)

    index = answer.find("SOURCES:")
    sources = None
    if index != -1:
        sources = answer[index + len("SOURCES:"):].strip()
        answer = answer[:index].strip()

    if sources:
        provider = OpenAI(model_engine="gpt-4o")
        answer_relevance = provider.relevance(prompt=question, response=answer)
        context_relevance, context_relevance_reason = provider.context_relevance_with_cot_reasons(question=question, context=context)
        groundedness, groundedness_reason  = provider.groundedness_measure_with_cot_reasons(source=context, statement=answer)
        yield f"data: {EVAL_TAG} Context Relavance: {context_relevance}, Groundedness: {groundedness}, Answer Relavance: {answer_relevance}\n\n"

    chat_history.add_user_message(question)
    chat_history.add_ai_message(answer)


