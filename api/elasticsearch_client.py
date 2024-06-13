from elasticsearch import Elasticsearch
from langchain_elasticsearch import ElasticsearchChatMessageHistory
import os
from dotenv import load_dotenv

load_dotenv(override=True)

ELASTIC_CLOUD_ID = os.getenv("ELASTIC_CLOUD_ID")
ELASTIC_API_KEY = os.getenv("ELASTIC_API_KEY")


if ELASTIC_CLOUD_ID:
    elasticsearch_client = Elasticsearch(
        cloud_id=ELASTIC_CLOUD_ID, api_key=ELASTIC_API_KEY
    )
else:
    raise ValueError(
        "Please provide either ELASTICSEARCH_URL or ELASTIC_CLOUD_ID and ELASTIC_API_KEY"
    )


def get_elasticsearch_chat_message_history(index, session_id):
    return ElasticsearchChatMessageHistory(
        es_connection=elasticsearch_client, index=index, session_id=session_id
    )
