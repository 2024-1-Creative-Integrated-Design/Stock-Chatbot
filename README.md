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

#### Ingest data


```sh
flask create-index
```


#### Run API and frontend

```sh
# Launch API app
flask run

# In a separate terminal launch frontend app
cd frontend && yarn start
```

You can now access the frontend at http://localhost:5000.
