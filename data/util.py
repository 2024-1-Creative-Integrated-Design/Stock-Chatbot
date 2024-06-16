from datetime import datetime, timedelta

def get_day_before(date_str: str) -> str:
    date_obj = datetime.strptime(date_str, "%Y%m%d")
    day_before = date_obj - timedelta(days=1)
    day_before_str = day_before.strftime("%Y%m%d")
    return day_before_str

def convert_date_format(date_str):
    date_obj = datetime.strptime(date_str, "%Y%m%d")
    formatted_date_str = date_obj.strftime("%Y-%m-%d")
    return formatted_date_str