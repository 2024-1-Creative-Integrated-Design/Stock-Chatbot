import json
import numpy as np
import pandas as pd
import requests
import os
import warnings
from datetime import datetime
import re
from io import StringIO
import bs4
import pandas as pd
import sec_parser as sp
import tiktoken

current_dir = os.path.dirname(os.path.abspath(__file__))
amd_folder = os.path.join(current_dir,"disclosure", "amd")
nvda_folder = os.path.join(current_dir, "disclosure", "nvda")

amd_cik = "2488"
nvda_cik = "1045810"

amd_url = f"https://data.sec.gov/submissions/CIK{amd_cik.zfill(10)}.json"
nvda_url = f"https://data.sec.gov/submissions/CIK{nvda_cik.zfill(10)}.json"
header = { "User-Agent": "Mozilla"}

def get_filing_list_nvda(start_date, end_date):
    start_date = pd.to_datetime(start_date, format='%Y%m%d')
    end_date = pd.to_datetime(end_date, format='%Y%m%d')
    nvda_filings = requests.get(nvda_url, headers=header).json()
    nvda_filings_df = pd.DataFrame(nvda_filings["filings"]["recent"])
    nvda_filings_df['filingDate'] = pd.to_datetime(nvda_filings_df['filingDate'])
    nvda_selected = nvda_filings_df[
        (nvda_filings_df['filingDate'] >= start_date) &
        (nvda_filings_df['filingDate'] <= end_date)
    ]
    if nvda_selected.empty:
        print("No NVIDIA reports found")
        return []
    else:
        return process_report(nvda_folder, nvda_selected, "NVIDIA", nvda_cik)

def get_filing_list_amd(start_date, end_date):
    start_date = pd.to_datetime(start_date, format='%Y%m%d')
    end_date = pd.to_datetime(end_date, format='%Y%m%d')
    amd_filings = requests.get(amd_url, headers=header).json()
    amd_filings_df = pd.DataFrame(amd_filings["filings"]["recent"])
    amd_filings_df['filingDate'] = pd.to_datetime(amd_filings_df['filingDate'])
    amd_selected = amd_filings_df[
        (amd_filings_df['filingDate'] >= start_date) &
        (amd_filings_df['filingDate'] <= end_date)
    ]
    if amd_selected.empty:
        print("No AMD reports found")
        return []
    else:
        return process_report(amd_folder, amd_selected, "AMD", amd_cik)


def process_report(folder_path, df, company_name, cik):
    final_result = []
    os.makedirs(folder_path, exist_ok=True)
    for index, row in df[df["form"].isin(["10-K", "8-K", "10-Q"])].iterrows():
        result = []
        access_number = row["accessionNumber"].replace("-", "")
        file_name = row["primaryDocument"]
        report_date = convert_date_format(row["filingDate"])
        report_name = "["+company_name+"]" + row["form"] + "("+report_date+")"
        report_url = f"https://www.sec.gov/Archives/edgar/data/{cik}/{access_number}/{file_name}"
        req_content = requests.get(report_url, headers=header).content.decode("utf-8", errors="ignore")
        file_path = os.path.join(folder_path, report_name+".html")
        with open(file_path, "w") as f:
            f.write(req_content)
        report_content = parse_report(req_content)
        for content in report_content:
            result.append({
                "company": company_name,
                "name": report_name,
                "url": report_url,
                "content": content,
                "updated_at": report_date,
                "category": "edgar"
            })
            parsed_file_name = f'{report_name}.json'
            save_path = os.path.join(folder_path, parsed_file_name)
            with open(save_path, 'w') as json_file:
                json.dump(result, json_file, ensure_ascii=False, indent=4)
        final_result.extend(result)
    return final_result
    
def parse_report(report):
    parser = sp.Edgar10QParser()

    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", message="Invalid section type for")
        elements: list = parser.parse(report)
        return _parse(elements)

def _parse(elements):
    enc = tiktoken.encoding_for_model("text-embedding-3-small")
    output = []
    i = 0
    while i < len(elements):
        element = elements[i]
        tokens = enc.encode(element.text)
        if isinstance(element, sp.TextElement):
            if (i + 1 < len(elements)) and isinstance(elements[i + 1], sp.TableElement):
                combined_text = f"{element.text}\n{_pandas_to_markdown(_html_to_pandas(_unmerge_cells(elements[i + 1].get_source_code())))}"
                output.append(combined_text)
                i += 1  
            else:
                if len(tokens) > 512:
                    text_chunks = chunk_string(element.text)
                    output.extend(text_chunks)
                else:
                    output.append(f"{element.text}")
        elif isinstance(element, sp.TableElement):
            unmerged_html: str = _unmerge_cells(element.get_source_code())
            output.append(_pandas_to_markdown(_html_to_pandas(unmerged_html)))
        i += 1

    return output


def _unmerge_cells(html: str) -> str:
    soup = bs4.BeautifulSoup(html, "lxml")
    assert soup is not None, "No table found."
    assert isinstance(soup, bs4.Tag), "Expected a bs4.Tag."
    for td in soup.find_all("td"):
        if td.has_attr("colspan"):
            for _ in range(int(td["colspan"]) - 1):
                new_td = soup.new_tag("td")
                new_td.string = "NaN"
                td.insert_before(new_td)
            td["colspan"] = 1
    return str(soup)

def _pandas_to_markdown(df):
    df = df.fillna("")
    markdown_table = "\n".join(df.to_markdown(index=False).split("\n")[2:])
    markdown_table = re.sub(r" +", " ", markdown_table)
    return markdown_table

def _html_to_pandas(html):
    df = pd.read_html(StringIO(html), flavor="lxml")[0]
    df = df.dropna(how="all")
    df = df.dropna(how="all", axis="columns")
    return df

def convert_date_format(date_str):
    date_str = str(date_str)
    date_obj = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
    formatted_date_str = date_obj.strftime("%Y-%m-%d")
    return formatted_date_str

def chunk_string(string, max_tokens=512, overlap=256):
    enc = tiktoken.encoding_for_model("text-embedding-3-small")
    tokens = enc.encode(string)
    chunks = []
    i = 0
    while i < len(tokens):
        chunk = enc.decode(tokens[i:i + max_tokens])
        chunks.append(chunk)
        i += max_tokens - overlap
    
    return chunks

if __name__ == "__main__":
    get_filing_list_amd("20230101", "20240101")
    get_filing_list_nvda("20230101", "20240101")