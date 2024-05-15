import dart_fss as dart
import os
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("DART_API_KEY")
dart.set_api_key(api_key)

current_dir = os.path.dirname(os.path.abspath(__file__))
samsung_folder = os.path.join(current_dir, "samsung")
hynix_folder = os.path.join(current_dir, "hynix")

samsung = '00126380'
hynix = '00164779'

samsung_reports = dart.api.filings.search_filings(
    corp_code=samsung,
    bgn_de="20210101",
    pblntf_ty=["A","B"],
    sort="date",
    page_count=100
)

hynix_reports = dart.api.filings.search_filings(
    corp_code=hynix,
    bgn_de="20210101",
    pblntf_ty=["A","B"],
    sort="date",
    page_count=100
)

def main():
    if not os.path.exists(samsung_folder):
        os.makedirs(samsung_folder)
    if not os.path.exists(hynix_folder):
        os.makedirs(hynix_folder)

    for report in samsung_reports['list']:
        access_number = report['rcept_no']
        file_name = report['report_nm'] +"_"+ report['rcept_dt'] + "htm"
        file_path = os.path.join(samsung_folder, file_name)
        try:
            dart.api.filings.download_document(file_path, access_number)
        except:
            continue
        

    for report in hynix_reports['list']:
        access_number = report['rcept_no']
        file_name = report['report_nm'] +"_"+ report['rcept_dt'] + "htm"
        file_path = os.path.join(hynix_folder, file_name)
        try:
            dart.api.filings.download_document(file_path, access_number)
        except:
            continue

if __name__ == "__main__":
    main()