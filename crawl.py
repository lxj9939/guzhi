import requests
import pandas as pd
from datetime import datetime
import os
import time

# 配置
# 核心过滤：fs=m:90+t:2 彻底锁定了东财的“行业板块”（去除了所有概念板块），pz=100 一页直接封顶抓完
API_URL = "https://11.push2.eastmoney.com/api/qt/clist/get?pn=1&pz=100&po=1&np=1&fltt=2&invt=2&fid=f3&fs=m:90+t:2+f:!62&fields=f12,f14,f9"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Referer": "https://quote.eastmoney.com/center/grid_list.html",
    "Connection": "keep-alive"
}
DATA_DIR = "data"
HISTORY_FILE = os.path.join(DATA_DIR, "pe_history.csv")

if not os.path.exists(DATA_DIR):
    os.mkdir(DATA_DIR)

def fetch_industry_pe():
    """只抓取行业板块的核心 PE 数据"""
    print("🚀 开始抓取东方财富核心行业板块 PE 估值...")
    try:
        res = requests.get(API_URL, headers=HEADERS, timeout=15)
        res.raise_for_status()
        json_data = res.json()
    except Exception as e:
        print(f"❌ 请求接口失败: {e}")
        return pd.DataFrame()
        
    data_list = json_data.get("data", {}).get("diff", [])
    if not data_list:
        print("⚠️ 未能获取到有效的行业数据。")
        return pd.DataFrame()
        
    rows = []
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    for item in data_list:
        pe_val = item.get("f9", "-")
        
        # 严格过滤：如果 PE 字段为空、为 "-" (通常是亏损行业) 则直接跳过
        if pe_val == "-" or pe_val == "" or pe_val is None:
            continue
            
        rows.append({
            "采集时间": now,
            "行业代码": item.get("f12", ""),
            "行业名称": item.get("f14", ""),
            "PE(TTM)": pe_val
        })
        
    return pd.DataFrame(rows)

def save_history(df_new):
    """追加保存到历史 CSV"""
    if df_new.empty:
        print("⚠️ 本次没有抓取到有效的 PE 数据，跳过保存。")
        return
        
    if os.path.exists(HISTORY_FILE):
        try:
            df_old = pd.read_csv(HISTORY_FILE, encoding="utf-8-sig")
            df_all = pd.concat([df_old, df_new], ignore_index=True)
        except Exception as e:
            print(f"⚠️ 读取历史文件失败，将重新创建。错误: {e}")
            df_all = df_new
    else:
        df_all = df_new
        
    df_all.to_csv(HISTORY_FILE, index=False, encoding="utf-8-sig")
    print(f"💾 成功追加 {len(df_new)} 条行业 PE 数据至 {HISTORY_FILE}")

if __name__ == "__main__":
    df = fetch_industry_pe()
    save_history(df)
    print("✅ 任务结束")
