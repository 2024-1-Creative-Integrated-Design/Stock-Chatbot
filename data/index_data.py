from elasticsearch import Elasticsearch, NotFoundError
from langchain_elasticsearch import ElasticsearchStore
from langchain.docstore.document import Document
from langchain_openai import OpenAIEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from dotenv import load_dotenv
import json
import os

from data.naver_news import get_news_naver
from data.korea_investment import fetch_all_company_data
from data.dart import get_filing_list_samsung, get_filing_list_hynix
from data.edgar import get_filing_list_nvda, get_filing_list_amd

load_dotenv(override=True)

NEWS_INDEX = "news"
STOCK_INDEX = "stock"
REPORT_INDEX = "report"
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
embedding = OpenAIEmbeddings(openai_api_key=os.getenv("OPENAI_API_KEY"), model="text-embedding-3-small")


def add_naver_news_data(day_before=1, length=50):
    print(f"Loading data from news")
    responses = get_news_naver(length = length, day_before = day_before)
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
        model_name="text-embedding-3-small", chunk_size=512, chunk_overlap=256
    )

    docs = text_splitter.transform_documents(workplace_docs)
    print(f"Split {len(workplace_docs)} documents into {len(docs)} chunks")
    
    ElasticsearchStore.from_documents(
        documents=docs,
        es_connection=elasticsearch_client,
        index_name=NEWS_INDEX,
        embedding=embedding,
    )

def add_stock_data(start_date, end_date):
    print(f"Loading data from stock")
    df = fetch_all_company_data(start_date, end_date)
    workplace_docs = []
    for index, row in df.iterrows():
        row_str = ', '.join([f"{col} : {row[col]}" for col in df.columns])
        workplace_docs.append(
            Document(
                page_content=row_str,
                metadata={
                    "name": row['날짜']+ " " + row['회사명'] +" 주가 정보",
                    "category": "stock",
                    "updated_at": row['날짜']
                },
            )
        )

    print(f"Loaded {len(workplace_docs)} documents")
    ElasticsearchStore.from_documents(
        documents=workplace_docs,
        es_connection=elasticsearch_client,
        index_name=STOCK_INDEX,
        embedding=embedding,
    )

def add_dart_data(start_date, end_date):
    print(f"Loading data from dart")
    result1 = get_filing_list_samsung(start_date, end_date)
    result2 = get_filing_list_hynix(start_date, end_date)
    result1.extend(result2)
    if len(result1)==0:
        print("No data found")
        return None
    else:
        metadata_keys = ["name", "url", "category", "updated_at"]
        workplace_docs = []
        for item in result1:
            workplace_docs.append(
                Document(
                    page_content=item["content"],
                    metadata={k: item.get(k) for k in metadata_keys},
                )
            )
        print(f"Loaded {len(workplace_docs)} documents")
        ElasticsearchStore.from_documents(
            documents=workplace_docs,
            es_connection=elasticsearch_client,
            index_name=REPORT_INDEX,
            embedding=embedding,
        )


def add_edgar_data(start_date, end_date):
    print(f"Loading data from edgar")
    result1 = get_filing_list_nvda(start_date, end_date)
    result2 = get_filing_list_amd(start_date, end_date)
    result1.extend(result2)
    if len(result1)==0:
        print("No data found")
        return None
    else:
        metadata_keys = ["name", "url", "category", "updated_at"]
        workplace_docs = []
        for item in result1:
            workplace_docs.append(
                Document(
                    page_content=item["content"],
                    metadata={k: item.get(k) for k in metadata_keys},
                )
            )
        print(f"Loaded {len(workplace_docs)} documents")
        ElasticsearchStore.from_documents(
            documents=workplace_docs,
            es_connection=elasticsearch_client,
            index_name=REPORT_INDEX,
            embedding=embedding,
        )
