import mojito
import pandas as pd
from datetime import datetime, timedelta
import time
import os
import requests
from dotenv import load_dotenv

load_dotenv()
key = os.getenv("KOREA_INVESTMENT_API_KEY")
secret = os.getenv("KOREA_INVESTMENT_API_SECRET")
acc_no = os.getenv("KOREA_INVESTMENT_ACC_NO")



class UnvalidCompanyError(Exception):
    def __init__(self) -> None:
        super().__init__("Please use valid company name.")

kr_analyzer = mojito.KoreaInvestment(
    api_key=key,
    api_secret=secret,
    acc_no=acc_no
)
kr_company_list = {"samsung" : "005930", "skhynix" : "000660" }

us_analyzer = mojito.KoreaInvestment(
    api_key=key,
    api_secret=secret,
    acc_no=acc_no,
    exchange='나스닥'
)
us_company_list = {"nvidia" : "NVDA" , "amd" : "AMD"}


def fetch_real_time(company_name: str) -> dict:

    """
    실시간 주식 정보 조회 (거래일이 아닌 경우 가장 최근 거래일 정보 조회)

    Args:
        company_name: 회사 이름(kr_company_list, us_company_lest의 keys)
    
    Returns: 
        kr_real_time_resp의 value가 key인 dict 
        us_real_time_resp의 value가 key인 dict
    """

    if company_name in kr_company_list:
        response = kr_analyzer.fetch_price(kr_company_list[company_name])['output']
        result = {kr_real_time_resp.get(k,k): v for k,v in response.items() if k in kr_real_time_resp}
        return result
    elif company_name in us_company_list:
        response = us_analyzer.fetch_price(us_company_list[company_name])['output']
        result = {us_real_time_resp.get(k,k): v for k,v in response.items() if k in us_real_time_resp}
        return result
    else:
        raise UnvalidCompanyError

def fetch_today_data(company_name: str) -> pd.DataFrame:
    
    """
    당일 분봉 데이터 조회

    Args:
        company_name: 회사 이름(kr_company_list, us_company_lest의 keys)
    
    """
    if company_name in kr_company_list:
        result = kr_analyzer.fetch_today_1m_ohlcv(kr_company_list[company_name])
        df = pd.DataFrame(result['output2'])
        dt = pd.to_datetime(df['stck_bsop_date'] + ' ' + df['stck_cntg_hour'], format="%Y%m%d %H%M%S")
        df.set_index(dt, inplace=True)
        df = df[['stck_oprc', 'stck_hgpr', 'stck_lwpr', 'stck_prpr', 'cntg_vol']]
        df.columns = ['시가(₩)', '최고가(₩)', '최저가(₩)', '종가(₩)','거래량']
        df.index.name = "datetime"
        df = df[::-1]
        return df
    elif company_name in us_company_list:
        url = "https://openapi.koreainvestment.com:9443//uapi/overseas-price/v1/quotations/inquire-time-itemchartprice"
        headers = {
            "content-type": "application/json; charset=utf-8",
            "authorization": us_analyzer.access_token,
            "appKey": us_analyzer.api_key,
            "appSecret" : us_analyzer.api_secret,
            "tr_id": "HHDFS76950200",
            "tr_cont": ""
        }
        paramss = {
            "AUTH":"",
            "EXCD":"NAS",
            "SYMB":us_company_list[company_name],
            "NMIN":"1",
            "PINC":"1",
            "NEXT":"",
            "NREC":"120",
            "FILL":"",
            "KEYB":""
        }
        result = requests.get(url, headers=headers, params=paramss)
        result = result.json()
        df = pd.DataFrame(result['output2'])
        dt = pd.to_datetime(df['kymd'] + ' ' + df['khms'], format="%Y%m%d %H%M%S")
        df.set_index(dt, inplace=True)
        df = df[['open', 'high', 'low', 'last', 'evol']]
        df.columns = ['시가($)', '최고가($)', '최저가($)', '종가($)','거래량']
        df.index.name = "datetime"
        df = df[::-1]
        return df
    else:
        raise UnvalidCompanyError

def fetch_previous_data(company_name: str, start_day: str, end_day: str, timeframe: str ='D', is_adjusted: bool = True) -> pd.DataFrame:
    
    """
    특정 기간 동안의 주식 정보 조회

    Args:
        company_name: 회사 이름(kr_company_list, us_company_lest의 keys)
        start_day, end_day: 검색 시작/종료 날짜 ("YYYYMMDD" 형식 ex."20240101")
        timeframe: "D" (일), "W" (주), "M" (월)
        is_adjusted: 수정 주가 반영 여부
    
    returns:
        DataFrame (column : 날짜, 회사명, 시가, 최고가, 최저가, 종가, 거래량)
    """
    if company_name in kr_company_list:
        data_lst = []
        while True:
            data = kr_get_previous(company_name, start_day, end_day, timeframe, is_adjusted)
            try:
                day = data[-1]['stck_bsop_date']
            except KeyError:
                break
            data_lst.extend(data)
            if start_day < day:
                end_day = get_day_before(day)
            else: break
        return kr_set_df(data_lst, company_name)
    elif company_name in us_company_list:
        data_lst = []
        while True:
             data = us_get_previous(company_name, end_day, timeframe, is_adjusted)
             try:
                 day = data[-1]['xymd']
             except KeyError:
                 break
             data_lst.extend(data)
             if start_day < day:
                 end_day = get_day_before(day)
             else: break
        return us_set_df(data_lst, company_name, start_day)
    else:
        raise UnvalidCompanyError
        
def fetch_3years_all(timeframe: str='D', is_adjusted: bool = True) -> dict[str, pd.DataFrame]:
    result = dict() 
    for key in kr_company_list.keys():
        result[key] = fetch_previous_data(key, "20210101","20240509", timeframe, is_adjusted)
    for key in us_company_list.keys():
        result[key] = fetch_previous_data(key, "20210101","20240509", timeframe, is_adjusted)
    return result





kr_real_time_resp = {
    'stck_prpr' : '현재 가격(₩)',
    'prdy_vrss' : '전일 대비(₩)',
    'prdy_ctrt' : '전일 대비율',
    'acml_vol'  : '현재 거래량',
    'acml_tr_pbmn' : '현재 거래대금(₩)',
    'prdy_vrss_vol_rate' : '전일 대비 거래량 비율',
    'stck_oprc' : '시가(₩)',
    'stck_hgpr' : '최고가(₩)',
    'stck_lwpr' : '최저가(₩)' ,
    'lstn_stcn' : '상장 주수',
    'cpfn'      : '자본금(억)',
    'per'       : 'PER',
    'pbr'       : 'PBR',
    'eps'       : 'EPS',
    'bps'       : 'BPS',
    'frgn_ntby_qty' : '외국인 순매수 수량',
    'pgtr_ntby_qty' : '프로그램매맴 순매수 수량',
    'frgn_hldn_qty' : '외국인 보유 수량'
}

us_real_time_resp = {
    'last' : '현재 가격($)',
    'diff' : '전일 대비($)',
    'rate' : '전일 대비율',
    'tvol' : '현재 거래량' ,
    'tamt' : '현재 거래대금($)',
    'base' : '전일 종가($)'
}

def kr_get_previous(company_name: str, start_day: str, end_day: str, timeframe: str ='D', is_adjusted: bool = True) -> list[dict]:
    time.sleep(0.1)
    response = kr_analyzer.fetch_ohlcv_domestic (
            symbol = kr_company_list[company_name],
            timeframe = timeframe,
            start_day = start_day,
            end_day = end_day,
            adj_price = is_adjusted
        )
    return response['output2']

def us_get_previous(company_name: str, end_day: str, timeframe: str ='D', is_adjusted: bool = True) -> list[dict]:
    time.sleep(0.1)
    response = us_analyzer.fetch_ohlcv_overesea (
            symbol = us_company_list[company_name],
            timeframe = timeframe,
            end_day = end_day,
            adj_price= is_adjusted
        )
    return response['output2']

def kr_set_df(response: list, company_name: str) -> pd.DataFrame:
    df = pd.DataFrame(response)
    df['stck_bsop_date'] = pd.to_datetime(df['stck_bsop_date'], format='%Y%m%d')
    df['company'] = company_name
    df = df[['stck_bsop_date', 'company', 'stck_oprc', 'stck_hgpr', 'stck_lwpr', 'stck_clpr','acml_vol' ]]
    df.columns = ['날짜','회사명', '시가(₩)', '최고가(₩)', '최저가(₩)', '종가(₩)','거래량']
    return df

def us_set_df(response: list, company_name: str, start_day: str) -> pd.DataFrame:
    df = pd.DataFrame(response)
    df = df[df['xymd'] >= start_day]
    df['xymd'] = pd.to_datetime(df['xymd'], format='%Y%m%d')
    df['company'] = company_name
    df = df[['xymd','company','open', 'high', 'low', 'clos', 'tvol']]
    df.columns = ['날짜','회사명', '시가($)', '최고가($)', '최저가($)', '종가($)','거래량']
    return df

def get_day_before(date_str: str) -> str:
    date_obj = datetime.strptime(date_str, "%Y%m%d")
    day_before = date_obj - timedelta(days=1)
    day_before_str = day_before.strftime("%Y%m%d")
    return day_before_str


if __name__ =="__main__":
    current_dir = os.path.dirname(os.path.abspath(__file__))

    dfs = fetch_3years_all()

    # 현재 디렉토리에 CSV 파일 저장
    dfs["samsung"].to_csv(os.path.join(current_dir, 'samsung.csv'), index=True)
    dfs["skhynix"].to_csv(os.path.join(current_dir, 'hynix.csv'), index=True)
    dfs["nvidia"].to_csv(os.path.join(current_dir, 'nvidia.csv'), index=True)
    dfs["amd"].to_csv(os.path.join(current_dir, 'amd.csv'), index=True)