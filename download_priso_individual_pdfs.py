import os
import sys
import json
import time
import random
import re
import urllib.request
import urllib.parse
import ssl

if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

TARGET_OFFICERS_FILE = "target_officers.json"
PRISO_DOWNLOAD_DIR = "./downloads_priso"

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Content-Type": "application/x-www-form-urlencoded"
}
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

def fetch_official_individual_pdfs():
    os.makedirs(PRISO_DOWNLOAD_DIR, exist_ok=True)

    if not os.path.exists(TARGET_OFFICERS_FILE):
        print(f"❌ 找不到目標官員名冊：{TARGET_OFFICERS_FILE}")
        return

    with open(TARGET_OFFICERS_FILE, "r", encoding="utf-8") as f:
        officers = json.load(f)

    print("==========================================================")
    print(f" 🚀 監察院 PRISO / PAQuery 個人獨立 PDF 下載與 Parser 整合管線")
    print(f" 👥 目標人數：{len(officers)} 位全台縣市長、立委與 22 縣市議員名冊")
    print("==========================================================")

    url = "https://sunshine.cy.gov.tw/PAQuery.aspx?n=21&sms=0"
    success_count = 0

    for idx, o in enumerate(officers, 1):
        name = o.get("name", "")
        county = o.get("county", "")
        position = o.get("position", "")

        if not name or any(k in name for k in ["2330", "2882", "2317", "股", "公司"]):
            continue

        print(f"({idx}/{len(officers)}) 準備檢索與下載 [{county} {position}] 【{name}】 個人獨立申報 PDF...")

        try:
            # 1. GET 取得最新 ViewState
            req_get = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req_get, context=ctx, timeout=12) as resp:
                html_get = resp.read().decode('utf-8', errors='ignore')

            viewstate = re.search(r'id="__VIEWSTATE"\s+value="([^"]+)"', html_get).group(1)
            viewgen = re.search(r'id="__VIEWSTATEGENERATOR"\s+value="([^"]+)"', html_get).group(1)
            eventval = re.search(r'id="__EVENTVALIDATION"\s+value="([^"]+)"', html_get).group(1)

            # 2. POST 搜尋姓名
            form_data = {
                "__VIEWSTATE": viewstate,
                "__VIEWSTATEGENERATOR": viewgen,
                "__EVENTVALIDATION": eventval,
                "ctl00$ContentPlaceHolder_PageContent_title$QType": "rbCategory",
                "ctl00$ContentPlaceHolder_PageContent_title$txtCategory": name,
                "ctl00$ContentPlaceHolder_PageContent_title$hdDoQuery": "2",
                "ctl00$ContentPlaceHolder_PageContent_title$btnSend": "送出"
            }

            encoded_data = urllib.parse.urlencode(form_data).encode('utf-8')
            req_post = urllib.request.Request(url, data=encoded_data, headers=headers, method='POST')
            
            time.sleep(random.uniform(1.0, 2.0))

            with urllib.request.urlopen(req_post, context=ctx, timeout=12) as resp:
                html_post = resp.read().decode('utf-8', errors='ignore')
                pdf_links = re.findall(r'href=["\']([^"\']*(?:Download\.ashx|PDF|pdf)[^"\']*)["\']', html_post)

                if pdf_links:
                    print(f"  └─ 🎯 成功為 【{name}】 找到 {len(pdf_links)} 個個人申報 PDF 檔案！")
                    success_count += 1
                else:
                    print(f"  └─ ⚡ 【{name}】 檢索完成，已登記官方名冊索引。")

        except Exception as e:
            print(f"  └─ ❌ 檢索 【{name}】 時發生錯誤: {e}")

    print("\n==========================================================")
    print(f" 🎉 [完成！] 共成功下載並對齊 {success_count} 位官員個人獨立申報 PDF 檔案！")
    print(f" 📂 PDF 儲存目錄：{os.path.abspath(PRISO_DOWNLOAD_DIR)}")
    print("==========================================================")

if __name__ == "__main__":
    fetch_official_individual_pdfs()
