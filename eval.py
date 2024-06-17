import sys
import os
import json
from deepeval.metrics import GEval
from deepeval.test_case import LLMTestCaseParams, LLMTestCase
import deepeval
import matplotlib.pyplot as plt
from uuid import uuid4

# 'api' 디렉토리 경로를 sys.path에 추가
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), 'api')))

from elasticsearch_client import elasticsearch_client, get_elasticsearch_chat_message_history  # elasticsearch 클라이언트 import
from llm_integrations import get_llm  # LLM 통합 import
from langchain_elasticsearch import ElasticsearchStore
from langchain_openai import OpenAIEmbeddings
from dotenv import load_dotenv

# 환경 변수 로드
load_dotenv(override=True)

INDEX = os.getenv("ES_INDEX", "workplace-app-docs")
INDEX_CHAT_HISTORY = os.getenv("ES_INDEX_CHAT_HISTORY", "workplace-app-docs-chat-history")
DEEPEVAL_API_KEY = os.getenv("DEEPEVAL_API_KEY")
SESSION_ID_TAG = "[SESSION_ID]"
SOURCE_TAG = "[SOURCE]"
DONE_TAG = "[DONE]"

embedding = OpenAIEmbeddings(openai_api_key=os.getenv("OPENAI_API_KEY"))
store = ElasticsearchStore(
    es_connection=elasticsearch_client,
    index_name=INDEX,
    embedding=embedding,
)

# 예제 데이터셋 로드
with open('eval.json', 'r') as f:
    data = json.load(f)

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

def ask_question_no_flask(question, session_id):
    # 로깅을 위한 출력문 사용
    print("Chat session ID:", session_id)

    chat_history = get_elasticsearch_chat_message_history(INDEX_CHAT_HISTORY, session_id)

    if len(chat_history.messages) > 0:
        # 간결한 질문 생성
        condense_question_prompt = f"Condense this conversation: {chat_history.messages} and answer the question: {question}"
        condensed_question = get_llm().invoke(condense_question_prompt).content
    else:
        condensed_question = question

    print("Condensed question:", condensed_question)
    print("Question:", question)

    docs = store.as_retriever().invoke(condensed_question)
    for doc in docs:
        doc_source = {**doc.metadata, "page_content": doc.page_content}
        print("Retrieved document passage from:", doc.metadata["name"])
        # 필요시 doc_source 처리

    qa_prompt = f"Use the following documents: {docs} and answer the question: {question}"

    answer = ""
    for chunk in get_llm().stream(qa_prompt):
        content = chunk.content.replace("\n", " ")
        answer += content

    print("Answer:", answer)

    chat_history.add_user_message(question)
    chat_history.add_ai_message(answer)

    return answer

# 평가 결과 시각화를 위한 변수
scores_correctness = []
scores_relevance = []
scores_fluency = []
scores_coherence = []
labels = []

# 각 예제 처리
for example in data:
    question = example['question']
    expected_answer = example['expected_answer']

    # RAG 응답 받기
    session_id = str(uuid4())
    actual_response = ask_question_no_flask(question, session_id)

    # deepeval을 사용하여 이벤트 추적
    try:
        print("Event data:")
        print(f"Event Name: Chatbot")
        print(f"Model: gpt-4")
        print(f"Input: {question}")
        print(f"Response: {actual_response}")

        # JSON 데이터 유효성 확인을 위해 출력
        event_data = {
            "event_name": "Chatbot",
            "model": "gpt-4",
            "input": question,
            "response": actual_response,
            "hyperparameters": {
                "prompt template": "Prompt template used",
                "temperature": 1.0,
                "chunk size": 500
            },
            "additional_data": {
                "Example Text": "Additional context or metadata",
                "Example Link": deepeval.event.api.Link(value="https://example.com"),
                "Example JSON": {"key": "value"}
            }
        }
        print("Event data being sent to deepeval.track:", json.dumps(event_data, indent=2))

        event_id = deepeval.track(**event_data)

        # Create a test case for evaluation
        test_case = LLMTestCase(
            input=question,
            actual_output=actual_response,
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

        # Store the results for visualization
        scores_correctness.append(correctness_metric.score)
        scores_relevance.append(relevance_metric.score)
        scores_fluency.append(fluency_metric.score)
        scores_coherence.append(coherence_metric.score)
        labels.append(question)

        # Send feedback to the development team
        deepeval.send_feedback(
            event_id=event_id,
            provider="user",
            rating=4,
            explanation=f"The response was mostly correct, but lacked detail. ({correctness_metric.reason})",
            expected_response=expected_answer
        )

    except Exception as e:
        print(f"Error occurred: {e}")

# Visualize evaluation metrics
plt.figure(figsize=(10, 5))
bar_width = 0.2
index = range(len(labels))

plt.barh([i + bar_width*0 for i in index], scores_correctness, bar_width, label='Correctness')
plt.barh([i + bar_width*1 for i in index], scores_relevance, bar_width, label='Relevance')
plt.barh([i + bar_width*2 for i in index], scores_fluency, bar_width, label='Fluency')
plt.barh([i + bar_width*3 for i in index], scores_coherence, bar_width, label='Coherence')

plt.xlabel('Evaluation Score')
plt.ylabel('Questions')
plt.title('Evaluation Metrics')
plt.yticks([i + bar_width for i in index], labels)
plt.legend()

plt.tight_layout()
plt.show()
