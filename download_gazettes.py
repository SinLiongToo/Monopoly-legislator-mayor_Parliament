import os
import sys
import re
import time
import random
import urllib.request
import urllib.parse
import ssl
import pypdf
from typing import Dict, Any, List, Optional, Set

if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

BASE_GAZETTE_URL = "https://sunshine.cy.gov.tw/News.aspx?n=17&sms=8861"
DOWNLOAD_DIR = "./downloads"

def fetch_page_html(url: str) -> str:
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

def download_gazette_pdf(file_url: str, suggested_filename: str) -> Optional[str]:
    filepath = os.path.join(DOWNLOAD_DIR, suggested_filename)
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
    }
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    delay = random.uniform(2.0, 4.0)
    print(f"[禮貌下載] 準備下載 {suggested_filename}... (等待 {delay:.2f} 秒)")
    time.sleep(delay)

    try:
        req = urllib.request.Request(file_url, headers=headers)
        with urllib.request.urlopen(req, context=ctx, timeout=60) as resp:
            data = resp.read()
            
            # 先將檔案寫入臨時檔
            temp_path = filepath + ".tmp"
            with open(temp_path, "wb") as f:
                f.write(data)
            
            exact_filename = suggested_filename
            # 【自動辨識 PDF 內文第 1 頁標題與期數】
            try:
                reader = pypdf.PdfReader(temp_path)
                if reader.pages:
                    text_p1 = reader.pages[0].extract_text() or ""
                    m = re.search(r'(廉政專刊第?\s*\d+\s*期|第\s*\d+\s*期)', text_p1)
                    if m:
                        raw_issue = m.group(1).replace(" ", "")
                        if not raw_issue.startswith("廉政專刊"):
                            raw_issue = f"廉政專刊_{raw_issue}"
                        elif not raw_issue.startswith("廉政專刊_"):
                            raw_issue = raw_issue.replace("廉政專刊", "廉政專刊_")

                        exact_filename = f"{raw_issue}.pdf"
            except Exception:
                pass

            exact_filepath = os.path.join(DOWNLOAD_DIR, exact_filename)

            # 若此期數的完整專刊已存在，清理臨時檔並跳過
            if os.path.exists(exact_filepath) and temp_path != exact_filepath:
                os.remove(temp_path)
                print(f"  └─ ⚡ [專刊去重] 【{exact_filename}】已存在，跳過重複下載。")
                return exact_filepath

            # 更名為最終精準標籤檔名
            os.rename(temp_path, exact_filepath)
            print(f"  └─ 🎉 [成功下載與精準期數命名] ➔ 【{exact_filename}】 (大小: {len(data):,} bytes)")
            return exact_filepath
    except Exception as e:
        print(f"  └─ ❌ [下載失敗] {suggested_filename}: {e}")
        return None

def download_multi_pages(start_page: int = 1, end_page: int = 4):
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)
    print("==========================================================")
    print(f" 📚 監察院《廉政專刊》全自動「帶期數標籤」下載器 (第 {start_page} 頁 ～ 第 {end_page} 頁)")
    print("==========================================================")

    download_queue = []
    seen_urls: Set[str] = set()

    for page_num in range(start_page, end_page + 1):
        # 關鍵修復：監察院官方網頁分頁參數必須帶上 &PageSize=20
        page_url = f"{BASE_GAZETTE_URL}&page={page_num}&PageSize=20"
        print(f"\n[步驟 1/2] 解析第 {page_num}/{end_page} 頁目錄: {page_url}")

        try:
            html = fetch_page_html(page_url)
            a_tags = re.findall(r'<a[^>]+href=["\']([^"\']*Download\.ashx[^"\']+)["\'][^>]*>([\s\S]*?)</a>', html)

            print(f"  └─ 第 {page_num} 頁發現 {len(a_tags)} 個專刊檔案連結")

            for link, title_text in a_tags:
                full_url = urllib.parse.urljoin(BASE_GAZETTE_URL, link)
                
                if full_url in seen_urls:
                    continue
                seen_urls.add(full_url)

                parsed = urllib.parse.urlparse(full_url)
                query_params = urllib.parse.parse_qs(parsed.query)
                
                raw_n = query_params.get('n', [''])[0]
                unquoted = urllib.parse.unquote(raw_n)
                clean_title = re.sub(r'<[^>]+>', '', title_text).strip()
                
                m_issue = re.search(r'(第\d+期|\d+期)', unquoted) or re.search(r'(第\d+期|\d+期)', clean_title)
                if m_issue:
                    issue_num = m_issue.group(1)
                    if not issue_num.startswith("第"):
                        issue_num = f"第{issue_num}"
                    suggested_filename = f"廉政專刊_{issue_num}.pdf"
                else:
                    suggested_filename = f"廉政專刊_待辨識_{len(download_queue)+1}.pdf"

                download_queue.append((suggested_filename, full_url))
        except Exception as e:
            print(f"  └─ ❌ 抓取第 {page_num} 頁失敗: {e}")

    print(f"\n[步驟 2/2] 開始下載 {len(download_queue)} 個檔案（將自動分析第1頁並給予精準【廉政專刊_第XXX期.pdf】標籤）...\n")
    success_count = 0

    for idx, (suggested_filename, download_url) in enumerate(download_queue, 1):
        print(f"({idx}/{len(download_queue)}) 下載處理中...")
        saved_file = download_gazette_pdf(download_url, suggested_filename)
        if saved_file:
            success_count += 1

    print("\n==========================================================")
    print(f" 🎉 [完成！] 共成功下載並貼標 {success_count} 本《廉政專刊》PDF 檔案！")
    print(f" 📂 儲存目錄：{os.path.abspath(DOWNLOAD_DIR)}")
    print("==========================================================")

def main():
    start_page = 1
    end_page = 4

    if len(sys.argv) == 2 and sys.argv[1].isdigit():
        end_page = int(sys.argv[1])
    elif len(sys.argv) >= 3 and sys.argv[1].isdigit() and sys.argv[2].isdigit():
        start_page = int(sys.argv[1])
        end_page = int(sys.argv[2])

    download_multi_pages(start_page, end_page)

if __name__ == "__main__":
    main()
