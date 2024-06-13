import os
import urllib.request
import requests
import json
import re
from bs4 import BeautifulSoup
from datetime import datetime
from dotenv import load_dotenv

# 환경 변수 로드
load_dotenv(override=True)

client_id = os.getenv("NAVER_CLIENT_ID")
client_secret = os.getenv("NAVER_CLIENT_SECRET")

def get_news_naver(length=100,sort="sim"):
    keywords = {
        "samsung": ["삼성전자", "삼전"],
        "skhynix": ["하이닉스", "하닉"],
        "nvidia": ["엔비디아", "NVIDIA"],
        "amd": ["AMD"]
    }

    responses = []

    display = min(100, length)
    start_from = 1
    current_date = datetime.now().strftime("%a, %d %b %Y")


    for company in keywords.keys():
        for keyword in keywords[company]:
            for start in range(start_from, length, display):
                encText = urllib.parse.quote(keyword)
                url = f"https://openapi.naver.com/v1/search/news.json?query={encText}&display={display}&start={start}&sort={sort}"
                request = urllib.request.Request(url)
                request.add_header("X-Naver-Client-Id", client_id)
                request.add_header("X-Naver-Client-Secret", client_secret)
                response = urllib.request.urlopen(request)
                rescode = response.getcode()
                if rescode == 200:
                    response_body = response.read().decode('utf-8')
                    search_results = json.loads(response_body)
                    today_results = [item for item in search_results['items'] if current_date in item['pubDate']]
                    naver_results = [item for item in today_results if item['link'].startswith("https://n.news.naver.com")]
                    for result in naver_results:
                        responses.append({
                            "company": company,
                            "title": format_title(result['title']),
                            "link": result['link'],
                            "content": get_news_text(result['link']),
                            "date": format_date(result['pubDate']),
                            "category": "news"
                        })
                else:
                        continue
    current_date = datetime.now().strftime('%Y-%m-%d')
    file_name = f'{current_date}_news.json'
    save_path = os.path.join('data', file_name)
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    with open(save_path, 'w') as json_file:
        json.dump(responses, json_file, ensure_ascii=False, indent=4)
    return responses

def get_news_text(url):
    req = requests.get(url, headers={'User-agent': 'Mozilla/5.0'})
    soup = BeautifulSoup(req.text, "lxml")
    text = soup.find('article', class_='go_trans _article_content', id='dic_area')

    for br in text.find_all("br"):
        br.decompose()

    return text.get_text(strip=True)

def format_date(date_str):
    date_obj = datetime.strptime(date_str, '%a, %d %b %Y %H:%M:%S %z')
    formatted_date = date_obj.strftime('%Y-%m-%d')
    return formatted_date

def format_title(text):
    clean = re.sub(r'<[^>]+>', '', text)
    clean = clean.replace('&quot;', '')
    return clean

if __name__ == "__main__":
    get_news_naver()