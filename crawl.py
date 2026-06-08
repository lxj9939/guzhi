import requests
import pandas as pd
from datetime import datetime
import os

# 配置
API_URL = "http://quote.eastmoney.com/center/api/sbk_gs.php?type=1&sort=3&page=1&ps=2000"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36"
}
DATA_DIR = "data"
HISTORY_FILE = os.path.join(DATA_DIR, "pe_history.csv")

# 创建数据文件夹
if not os.path.exists(DATA_DIR):
    os.mkdir(DATA_DIR)

def fetch_valuation_data():
    """抓取东方财富板块估值数据"""
    res = requests.get(API_URL, headers=HEADERS, timeout=15)
    res.raise_for_status()
    json_data = res.json()

    rows = []
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    for item in json_data["data"]:
        rows.append({
            "采集时间": now,
            "板块名称": item.get("name", ""),
            "最新点位": item.get("price", ""),
            "涨跌幅%": item.get("zdf", ""),
            "PE(TTM)": item.get("pe", ""),
            "PB": item.get("pb", ""),
            "估值分位%": item.get("fwd", "")
        })
    return pd.DataFrame(rows)

def save_history(df_new):
    """追加保存历史数据"""
    if os.path.exists(HISTORY_FILE):
        df_old = pd.read_csv(HISTORY_FILE, encoding="utf-8-sig")
        df_all = pd.concat([df_old, df_new], ignore_index=True)
    else:
        df_all = df_new
    df_all.to_csv(HISTORY_FILE, index=False, encoding="utf-8-sig")

if __name__ == "__main__":
    df = fetch_valuation_data()
    save_history(df)
    print("✅ 数据抓取并保存完成")
