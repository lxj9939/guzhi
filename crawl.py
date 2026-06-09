import requests
import pandas as pd
from datetime import datetime
import os
import time

# 配置
# fs=m:90+t:2 锁定东方财富的行业板块；fields=f12,f14,f9 分别代表代码、名称、PE(TTM)
BASE_URL = "https://11.push2.eastmoney.com/api/qt/clist/get?pz=50&po=1&np=1&fltt=2&invt=2&fid=f3&fs=m:90+t:2+f:!62&fields=f12,f14,f9"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Referer": "https://quote.eastmoney.com/center/grid_list.html",
    "Connection": "keep-alive"
}
DATA_DIR = "data"
HISTORY_FILE = os.path.join(DATA_DIR, "pe_history.csv")

if not os.path.exists(DATA_DIR):
    os.mkdir(DATA_DIR)

def fetch_all_industries():
    """抓取全部行业板块数据（包含亏损行业，自动分页）"""
    all_rows = []
    today = datetime.now().strftime("%Y-%m-%d")
    page = 1
    
    print("🚀 开始抓取东方财富全量行业板块数据...")
    
    while True:
        url = f"{BASE_URL}&pn={page}"
        try:
            res = requests.get(url, headers=HEADERS, timeout=15)
            res.raise_for_status()
            json_data = res.json()
        except Exception as e:
            print(f"❌ 第 {page} 页请求失败: {e}")
            break
            
        data_list = json_data.get("data", {}).get("diff", [])
        
        # 如果这一页没有数据了，说明已经全部抓完
        if not data_list:
            break
            
        for item in data_list:
            # 即使 PE 是 "-"（代表亏损或无法计算），也保留下来
            pe_val = item.get("f9", "-")
            
            all_rows.append({
                "采集日期": today,
                "行业代码": item.get("f12", ""),
                "行业名称": item.get("f14", ""),
                "PE(TTM)": pe_val
            })
            
        page += 1
        time.sleep(0.2) # 稍微减缓请求频率
        
    return pd.DataFrame(all_rows)

def save_history(df_new):
    """追加保存到历史 CSV"""
    if df_new.empty:
        print("⚠️ 未能抓取到任何有效的行业数据。")
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
    print(f"💾 成功追加 {len(df_new)} 条全量行业数据至 {HISTORY_FILE}")

if __name__ == "__main__":
    df = fetch_all_industries()
    save_history(df)
    print("✅ 任务结束")
