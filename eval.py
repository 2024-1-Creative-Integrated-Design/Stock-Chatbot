import json
from deepeval.metrics import GEval
from deepeval.test_case import LLMTestCaseParams, LLMTestCase
import deepeval
import matplotlib.pyplot as plt
from uuid import uuid4
from api.chat import ask_question

# Load example dataset
with open('eval.json', 'r') as f:
    data = json.load(f)

# Initialize G-Eval metrics
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

# Variables to store evaluation results for visualization
scores_correctness = []
scores_relevance = []
scores_fluency = []
scores_coherence = []
labels = []

# Process each example
for example in data:
    question = example['question']
    expected_answer = example['expected_answer']
    
    # Get RAG response
    session_id = str(uuid4())
    response_generator = ask_question(question, session_id)
    
    # Collect the complete response from the generator
    actual_response = ""
    for chunk in response_generator:
        # Here we filter out any metadata tags
        if SESSION_ID_TAG in chunk or SOURCE_TAG in chunk or DONE_TAG in chunk:
            continue
        actual_response += chunk.replace("data: ", "").strip()
    
    # Track the event using deepeval
    event_id = deepeval.track(
        event_name="Chatbot",
        model="gpt-4",
        input=question,
        response=actual_response,
        hyperparameters={
            "prompt template": "Prompt template used",
            "temperature": 1.0,
            "chunk size": 500
        },
        additional_data={
            "Example Text": "Additional context or metadata",
            "Example Link": deepeval.events.api.Link(value="https://example.com"),
            "Example JSON": {"key": "value"}
        }
    )

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
