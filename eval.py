import json
from deepeval.metrics import GEval
from deepeval.test_case import LLMTestCaseParams, LLMTestCase
import deepeval
import matplotlib.pyplot as plt
from uuid import uuid4
from chat import ask_question
from flask import Response

# Load example dataset
with open('eval.json', 'r') as f:
    data = json.load(f)

# Initialize G-Eval correctness metric
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

    # Perform the evaluation
    correctness_metric.measure(test_case)
    print(f"Score for '{question}': {correctness_metric.score}")
    print(f"Reason: {correctness_metric.reason}")

    # Send feedback to the development team
    deepeval.send_feedback(
        event_id=event_id,
        provider="user",
        rating=4,
        explanation=f"The response was mostly correct, but lacked detail. ({correctness_metric.reason})",
        expected_response=expected_answer
    )

    # Visualize evaluation metrics
    scores = [correctness_metric.score]  # Example score data
    labels = [question]

    plt.bar(labels, scores)
    plt.xlabel('Questions')
    plt.ylabel('Evaluation Score')
    plt.title('Evaluation Metrics')
    plt.show()
