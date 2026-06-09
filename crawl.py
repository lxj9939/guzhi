import requests
import pandas as pd
from datetime import datetime
import os

# 配置
# 东方财富最新的行业/概念板块数据中心接口
API_URL = "https://11.push2.eastmoney.com/api/qt/clist/get?pn=1&pz=500&po=1&np=1&fltt=2&invt=2&fid=f3&fs=m:90+t:2+f:!62,m:90+t:3+f:!62&fields=f12,f14,f2,f3,f9,f22,f23"

# 升级后的 HEADERS，加入了更完整的浏览器伪装，防止被服务器断开连接
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json, text/javascript, */*; q=0.01",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    "Referer": "https://quote.eastmoney.com/center/grid_list.html",
    "Connection": "keep-alive"
}
DATA_DIR = "data"
HISTORY_FILE = os.path.join(DATA_DIR, "pe_history.csv")

# 创建数据文件夹
if not os.path.exists(DATA_DIR):
    os.mkdir(DATA_DIR)

def fetch_valuation_data():
    """抓取东方财富板块估值数据"""
    try:
        # 增加 timeout 防止网络卡死
        res = requests.get(API_URL, headers=HEADERS, timeout=15)
        res.raise_for_status()
        json_data = res.json()
    except requests.exceptions.RequestException as e:
        print(f"❌ 网络请求失败，原因: {e}")
        return pd.DataFrame()

    # 检查返回的数据结构是否正确
    data_list = json_data.get("data", {}).get("diff", [])
    if not data_list:
        print("⚠️ 未能获取到有效的 API 数据，请检查接口。")
        return pd.DataFrame()

    rows = []
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    for item in data_list:
        # 排除无效或空数据
        if item.get("f12") == "-":
            continue
            
        rows.append({
            "采集时间": now,
            "板块代码": item.get("f12", ""),
            "板块名称": item.get("f14", ""),
            "最新点位": item.get("f2", "-"),
            "涨跌幅%": item.get("f3", "-"),
            "PE(TTM)": item.get("f9", "-"),   # 动态/TTM 估值
            "PB": item.get("f23", "-"),        # 市净率 PB
            "五分钟涨跌%": item.get("f22", "-") 
        })
        
    return pd.DataFrame(rows)

def save_history(df_new):
    """追加保存历史数据"""
    if df_new.empty:
        print("⚠️ 数据为空，跳过保存以保护历史文件")
        return
        
    if os.path.exists(HISTORY_FILE):
        try:
            df_old = pd.read_csv(HISTORY_FILE, encoding="utf-8-sig")
            df_all = pd.concat([df_old, df_new], ignore_index=True)
        except Exception as e:
            print(f"⚠️ 读取历史 CSV 失败（可能文件损坏），将重新创建。错误: {e}")
            df_all = df_new
    else:
        df_all = df_new
        
    df_all.to_csv(HISTORY_FILE, index=False, encoding="utf-8-sig")

if __name__ == "__main__":
    df = fetch_valuation_data()
    save_history(df)
    print("✅ 数据抓取并保存完成")
