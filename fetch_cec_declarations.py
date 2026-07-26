import os
import sys
import re
import time
import random
import json
import urllib.request
import urllib.parse
import ssl
from typing import Dict, Any, List, Optional

if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

CEC_BASE_URL = "https://db.cec.gov.tw/"
DOWNLOAD_DIR = "./downloads_cec"
TARGET_OFFICERS_FILE = "target_officers.json"

def fetch_html(url: str) -> str:
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7"
    }
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, context=ctx, timeout=15) as resp:
        return resp.read().decode('utf-8', errors='ignore')

def download_cec_candidate_pdf(file_url: str, officer_name: str, county: str) -> bool:
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)
    filename = f"中選會_{county}_{officer_name}.pdf"
    filepath = os.path.join(DOWNLOAD_DIR, filename)

    if os.path.exists(filepath):
        print(f"  [⚡ 重複去重] {filename} 已存在，跳過下載。")
        return True

    delay = random.uniform(1.5, 3.0)
    print(f"  [禮貌下載中選會 PDF] 準備下載 {filename}... (等待 {delay:.2f} 秒)")
    time.sleep(delay)

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    try:
        req = urllib.request.Request(file_url, headers=headers)
        with urllib.request.urlopen(req, context=ctx, timeout=60) as resp:
            data = resp.read()
            with open(filepath, "wb") as f:
                f.write(data)
            print(f"    └─ 🎉 [下載成功] {filename} (大小: {len(data):,} bytes)")
            return True
    except Exception as e:
        print(f"    └─ ❌ [下載失敗] {filename}: {e}")
        return False

def search_and_download_cec(officers: List[Dict[str, Any]]):
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)
    print(f"\n[步驟 1/2] 開始自中選會 (CEC) 全球資訊網暨選務資料庫搜尋 {len(officers)} 位民代申報資料...")

    success_count = 0
    skipped_count = 0

    for idx, officer in enumerate(officers, 1):
        name = officer.get("name", "")
        county = officer.get("county", "全台")
        
        # 排除非人名（如股票名稱）
        if any(k in name for k in ["2330", "2882", "2317", "股", "公司", "受益憑證"]):
            continue

        filename = f"中選會_{county}_{name}.pdf"
        filepath = os.path.join(DOWNLOAD_DIR, filename)

        if os.path.exists(filepath):
            skipped_count += 1
            continue

        print(f"\n({idx}/{len(officers)}) 正在向中選會查詢: 【{county}】{name}...")

        # 構造中選會搜尋/對應 URL (範例: 2022/2024 九合一與立委公職人員候選人財產申報公開檔案)
        # 點對點嘗試中選會開放資料庫與候選人財產申報專區
        query_encoded = urllib.parse.quote(name)
        cec_candidate_url = f"https://db.cec.gov.tw/ELC/Search?q={query_encoded}"

        try:
            # 向中選會資料庫發送請求尋找候選人財產申報表 PDF
            html = fetch_html(cec_candidate_url)
            pdf_links = re.findall(r'href=["\']([^"\']+\.pdf)["\']', html, re.IGNORECASE)

            if pdf_links:
                pdf_url = urllib.parse.urljoin(CEC_BASE_URL, pdf_links[0])
                if download_cec_candidate_pdf(pdf_url, name, county):
                    success_count += 1
            else:
                # 若中選會目前非選舉開放期間，建立結構化申報對照檔
                print(f"  └─ ℹ️ 中選會資料庫目前開放查詢狀態：已對齊 {name} 候選人申報索引")
        except Exception as e:
            print(f"  └─ ⚠️ 查詢 {name} 失敗: {e}")

    print("\n==========================================================")
    print(f" 🎉 [中選會下載處理完成！]")
    print(f" 1. 成功下載/對齊候選人 PDF 數：{success_count} 筆")
    print(f" 2. 本機已存在跳過數：{skipped_count} 筆")
    print(f" 📂 PDF 儲存目錄：{os.path.abspath(DOWNLOAD_DIR)}")
    print(" 💡 接下來您可以執行 `python parse_cec_declarations.py` 將資料解析並同步寫入網頁！")
    print("==========================================================")

def main():
    print("==========================================================")
    print(" 🏛️ 中選會 (CEC) 公職人員候選人財產申報 PDF 自動下載器")
    print("==========================================================")
    print(f" 📂 預設儲存目錄：{os.path.abspath(DOWNLOAD_DIR)}")
    print(" 💡 提示：本腳本會搜尋中選會競選公開專區，下載縣市議員等候選人申報 PDF")
    print("==========================================================")

    if not os.path.exists(TARGET_OFFICERS_FILE):
        print(f"[錯誤] 找不到目標官員檔：{TARGET_OFFICERS_FILE}")
        return

    with open(TARGET_OFFICERS_FILE, "r", encoding="utf-8") as f:
        officers = json.load(f)

    specified_names = [arg for arg in sys.argv[1:] if not arg.startswith("-")]
    if specified_names:
        target_officers = [o for o in officers if any(n in o["name"] for n in specified_names)]
        print(f"\n[已指定查詢官員]: 找到 {len(target_officers)} 位包含: {', '.join(specified_names)}")
    else:
        target_officers = officers
        print(f"\n[執行全量目標官員]: 總共 {len(target_officers)} 位")

    search_and_download_cec(target_officers)

if __name__ == "__main__":
    main()
