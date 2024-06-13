from elasticsearch import Elasticsearch, NotFoundError
from langchain_elasticsearch import ElasticsearchStore
from langchain.docstore.document import Document
from langchain_openai import OpenAIEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from dotenv import load_dotenv
import json
import os

from data.news.news_naver import get_news_naver

load_dotenv(override=True)

INDEX = os.getenv("ES_INDEX", "workplace-app-docs")
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
embedding = OpenAIEmbeddings(openai_api_key=os.getenv("OPENAI_API_KEY"))


def add_naver_news_data():
    print(f"Loading data from news")
    responses = get_news_naver(length = 50)
    metadata_keys = ["name", "url", "category", "updated_at"]
    workplace_docs = []
    for item in responses:
        workplace_docs.append(
            Document(
                page_content=item["content"],
                metadata={k: item.get(k) for k in metadata_keys},
            )
        )

    print(f"Loaded {len(workplace_docs)} documents")

    text_splitter = RecursiveCharacterTextSplitter.from_tiktoken_encoder(
        chunk_size=512, chunk_overlap=256
    )

    docs = text_splitter.transform_documents(workplace_docs)
    print(f"Split {len(workplace_docs)} documents into {len(docs)} chunks")
    
    ElasticsearchStore.from_documents(
        documents=docs,
        es_connection=elasticsearch_client,
        index_name=INDEX,
        embedding=embedding,
    )
    
