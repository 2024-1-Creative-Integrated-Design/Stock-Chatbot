import dart_fss as dart
import os
import sys
import openparse
import json
from dotenv import load_dotenv

basedir = os.path.abspath(os.path.dirname(__file__))
sys.path.append(os.path.join(basedir, '../'))
from data.util import convert_date_format

load_dotenv(override=True)
api_key = os.getenv("DART_API_KEY")
dart.set_api_key(api_key)

current_dir = os.path.dirname(os.path.abspath(__file__))
samsung_folder = os.path.join(current_dir,"disclosure", "samsung")
hynix_folder = os.path.join(current_dir, "disclosure", "hynix")

def get_filing_list_samsung(start_date, end_date):
    samsung = dart.corp.Corp('00126380')
    try:
        result = []
        samsung_reports = samsung.search_filings(bgn_de=start_date, end_de=end_date, sort='date', pblntf_ty=["A","B"], page_count=100)
        pages = samsung_reports.total_page
        for page in range(1, pages+1):
            samsung_reports = samsung.search_filings(bgn_de=start_date, end_de=end_date, sort='date', pblntf_ty=["A","B"], page_no=page, page_count=100).report_list
            for report in samsung_reports:
                result.extend(process_report(samsung_folder, report))
        return result
    except:
        print("Samsung reports not found")
        return []

def get_filing_list_hynix(start_date, end_date):
    hynix = dart.corp.Corp('00164779')
    try: 
        result = []
        hynix_reports = hynix.search_filings(bgn_de=start_date, end_de=end_date, sort='date', pblntf_ty=["A","B"], page_count=100)
        page_hynix =  hynix_reports.total_page
        for page in range(1, page_hynix+1):
            hynix_reports = hynix.search_filings(bgn_de=start_date, end_de=end_date, sort='date', pblntf_ty=["A","B"], page_no=page, page_count=100).report_list
            for report in hynix_reports:
                result.extend(process_report(hynix_folder, report))
        return result
    except:
        print("Hynix reports not found")
        return []


def process_report(folder_path, report):
    result = []
    os.makedirs(os.path.dirname(folder_path), exist_ok=True)
    report.attached_files[0].download(folder_path)
    file_name = report.attached_files[0].filename
    report_path = os.path.join(folder_path, file_name)
    report_name = os.path.splitext(file_name)[0]
    report_date = convert_date_format(report.rcept_dt)
    report_url = "https://dart.fss.or.kr/dsaf001/main.do?rcpNo="+str(report.rcp_no)
    company_name = report.corp_name
    report_content = parse_report(report_path)
    for content in report_content:
        result.append({
            "company": company_name,
            "name": report_name,
            "url": report_url,
            "content": content,
            "updated_at": report_date,
            "category": "dart"
        })
    file_name = f'{report_name}.json'
    save_path = os.path.join(folder_path, file_name)
    with open(save_path, 'w') as json_file:
        json.dump(result, json_file, ensure_ascii=False, indent=4)
    return result
    

def parse_report(report_path):
    result = []
    parser = openparse.DocumentParser(
        table_args={
            "parsing_algorithm": "pymupdf",
            "table_output_format": "markdown"
        }
    )
    parsed_report = parser.parse(report_path)
    for node in parsed_report.nodes:
        elem = node.text.replace("<br>", "")
        result.append(elem)
    return result

if __name__ == "__main__":
    start_date = '20240501'
    end_date = '20240616'
    get_filing_list_samsung(start_date, end_date)
    get_filing_list_hynix(start_date, end_date)