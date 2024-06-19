import requests
import os
from dotenv import load_dotenv
from datetime import datetime
from langchain_community.document_loaders import WebBaseLoader
import re
import json

load_dotenv(override=True)
API_KEY = os.getenv("ALPHA_VANTAGE_API_KEY")

def fetch_all(start_date, end_date):
    result = get_alpha_vantage_data("NVDA",start_date,end_date) + get_alpha_vantage_data("AMD",start_date,end_date)
    json_result = transform_data(result)
    start_date_str = convert_date_format(start_date)
    end_date_str = convert_date_format(end_date)
    file_name = f'news_{start_date_str}_to_{end_date_str}.json'
    save_path = os.path.join(os.path.dirname(__file__), 'news', 'alphavantage', file_name)
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    with open(save_path, 'w') as json_file:
        json.dump(json_result, json_file, ensure_ascii=False, indent=4)
    return result
    
def get_alpha_vantage_data(ticker,start_date, end_date):
    start_date = convert_to_datetime_format(start_date)
    end_date = convert_to_datetime_format(end_date, end=True)
    url = f'https://www.alphavantage.co/query?function=NEWS_SENTIMENT&tickers={ticker}&apikey={API_KEY}&time_from={start_date}&time_to={end_date}&sort=RELEVANCE'
    resp = requests.get(url)
    data = resp.json()
    data = data['feed']
    docs = []

    for item in data:
        loader = WebBaseLoader(item['url'])
        result = loader.load()
        result[0].metadata['updated_at'] = format_date(item['time_published'])
        result[0].metadata['category'] = "news"
        rename_key(result[0].metadata, 'source', 'url')
        rename_key(result[0].metadata, 'title', 'name')
        result[0].metadata['name'] = format_title(result[0].metadata['name'])
        if ticker == "NVDA":
            company = "NVIDIA"
        elif ticker == "AMD":
            company = "AMD"
        else:
            company = "unknown"
        result[0].metadata['company'] = company
        result[0].page_content = normalize_newlines(result[0].page_content)
        docs.append(result[0])
    
    return docs

def convert_to_datetime_format(date_str, end=False):
    date_obj = datetime.strptime(date_str, "%Y%m%d")
    # end가 True이면 시간을 23:59로 설정, 아니면 00:00으로 설정
    if end:
        return date_obj.strftime("%Y%m%dT2359")
    else:
        return date_obj.strftime("%Y%m%dT0000")
    
def format_date(date_str):
    dt = datetime.strptime(date_str, '%Y%m%dT%H%M%S')
    return dt.strftime('%Y-%m-%d')

def rename_key(dictionary, old_key, new_key):
    if old_key in dictionary:
        dictionary[new_key] = dictionary.pop(old_key)

def format_title(text):
    clean = re.sub(r'<[^>]+>', '', text)
    clean = clean.replace('&quot;', '')
    clean = clean.replace(',', '')
    return clean

def normalize_newlines(text):
    text = re.sub(r'\n+', ' ', text)
    text = re.sub(r'\t+', ' ', text)
    text = re.sub(r' +', ' ', text)
    return text

def transform_data(documents):
    transformed = []
    for doc in documents:
        metadata = doc.metadata
        transformed.append({
            "company": metadata['company'],
            "name": metadata['name'],
            "url": metadata['url'],
            "content": doc.page_content,
            "updated_at": metadata['updated_at'],
            "category": metadata['category']
        })
    return transformed


def convert_date_format(date_str):
    date_obj = datetime.strptime(date_str, "%Y%m%d")
    formatted_date_str = date_obj.strftime("%Y-%m-%d")
    return formatted_date_str

if __name__ == "__main__":
    fetch_all("20240101", "20240531")