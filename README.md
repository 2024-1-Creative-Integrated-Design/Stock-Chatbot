# Stock-Chatbot RAG App

This is a app that combines Elasticsearch, Langchain and llms(openai, anthropic) to create a stock analyzing chatbot.


#### Pre-requisites

- Python 3.8+
- Node 14+

#### Install the dependencies

```sh
# Create a virtual environment
python -m venv .venv

# Activate the virtual environment
source .venv/bin/activate

# Install Python dependencies
pip install -r requirements.txt

# Install Node dependencies
cd frontend && yarn && cd ..
```



#### Run API and frontend

```sh
# buil frontend
cd frontend
yarn build

# Launch API app
flask run
```
Before you run the program, you should set your .env file based on env_example_file
After that, you can access the frontend at http://localhost:5000.
