import json
import numpy as np
import pandas as pd
import requests
import os

current_dir = os.path.dirname(os.path.abspath(__file__))
amd_folder = os.path.join(current_dir, "amd")
nvda_folder = os.path.join(current_dir, "nvda")

amd_cik = "2488"
nvda_cik = "1045810"

amd_url = f"https://data.sec.gov/submissions/CIK{amd_cik.zfill(10)}.json"
nvda_url = f"https://data.sec.gov/submissions/CIK{nvda_cik.zfill(10)}.json"
header = { "User-Agent": "Mozilla"}
amd_filings = requests.get(amd_url, headers=header).json()
nvda_filings = requests.get(nvda_url, headers=header).json()

amd_filings_df = pd.DataFrame(amd_filings["filings"]["recent"])
nvda_filings_df = pd.DataFrame(nvda_filings["filings"]["recent"])
amd_3years = amd_filings_df[amd_filings_df["filingDate"] > "2021-01-01"]
nvda_3years = nvda_filings_df[nvda_filings_df["filingDate"] > "2021-01-01"]

def main():
    if not os.path.exists(amd_folder):
        os.makedirs(amd_folder)
    if not os.path.exists(nvda_folder):
        os.makedirs(nvda_folder)


    for index, row in amd_3years[amd_3years["form"].isin(["10-K", "8-K", "10-Q"])].iterrows():
        access_number = row["accessionNumber"].replace("-", "")
        file_name = row["primaryDocument"]
        report_url = f"https://www.sec.gov/Archives/edgar/data/{amd_cik}/{access_number}/{file_name}"
        req_content = requests.get(report_url, headers=header).content.decode("utf-8")
        file_path = os.path.join(amd_folder, file_name)
        with open(file_path, "w") as f:
            f.write(req_content)

    for index, row in nvda_3years[nvda_3years["form"].isin(["10-K", "8-K", "10-Q"])].iterrows():
        access_number = row["accessionNumber"].replace("-", "")
        file_name = row["primaryDocument"]
        report_url = f"https://www.sec.gov/Archives/edgar/data/{nvda_cik}/{access_number}/{file_name}"
        req_content = requests.get(report_url, headers=header).content.decode("utf-8")
        file_path = os.path.join(nvda_folder, file_name)
        with open(file_path, "w") as f:
            f.write(req_content)

if __name__ == "__main__":
    main()