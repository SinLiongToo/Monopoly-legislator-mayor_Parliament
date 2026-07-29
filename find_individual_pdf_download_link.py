import urllib.request
import urllib.parse
import ssl
import re
import sys

if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

url = "https://sunshine.cy.gov.tw/PAQuery.aspx?n=21&sms=0"

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Content-Type": "application/x-www-form-urlencoded"
}
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

# 1. 抓取 GET 頁面
req_get = urllib.request.Request(url, headers=headers)
with urllib.request.urlopen(req_get, context=ctx, timeout=15) as resp:
    html_get = resp.read().decode('utf-8', errors='ignore')

viewstate = re.search(r'id="__VIEWSTATE"\s+value="([^"]+)"', html_get).group(1)
viewgen = re.search(r'id="__VIEWSTATEGENERATOR"\s+value="([^"]+)"', html_get).group(1)
eventval = re.search(r'id="__EVENTVALIDATION"\s+value="([^"]+)"', html_get).group(1)

# 2. 帶入正確的 hdDoQuery = "2", hdButtonType = "1" (財產申報資料), txtCategory = "李宗霖"
form_data = {
    "__VIEWSTATE": viewstate,
    "__VIEWSTATEGENERATOR": viewgen,
    "__EVENTVALIDATION": eventval,
    "ctl00$ContentPlaceHolder_PageContent_title$QType": "rbCategory",
    "ctl00$ContentPlaceHolder_PageContent_title$txtCategory": "李宗霖",
    "ctl00$ContentPlaceHolder_PageContent_title$hdDoQuery": "2",
    "ctl00$ContentPlaceHolder_PageContent_title$hdButtonType": "1",
    "ctl00$ContentPlaceHolder_PageContent_title$btnSend": "送出"
}

encoded_data = urllib.parse.urlencode(form_data).encode('utf-8')

print("發送正確帶 hdButtonType=1 (財產申報資料) 的 POST 搜尋請求（姓名：李宗霖）...")
req_post = urllib.request.Request(url, data=encoded_data, headers=headers, method='POST')
try:
    with urllib.request.urlopen(req_post, context=ctx, timeout=15) as resp:
        html_post = resp.read().decode('utf-8', errors='ignore')
        print(f"🎉 搜尋成功！回傳 HTML 長度: {len(html_post):,} bytes")
        
        # 抓取表格內文與結果
        rows = re.findall(r'<tr[^>]*>([\s\S]*?)</tr>', html_post)
        print(f"表格發現 {len(rows)} 列數據！")
        for idx, r in enumerate(rows, 1):
            clean_r = re.sub(r'<[^>]+>', ' ', r).strip()
            clean_r = re.sub(r'\s+', ' ', clean_r)
            print(f"  Row {idx}: {clean_r}")
            # 抓出 href 或 onclick 或 __doPostBack 連結
            a_tags = re.findall(r'<a[^>]+>([\s\S]*?)</a>', r)
            links = re.findall(r'href=["\']([^"\']+)["\']', r)
            print(f"     Links: {links}")

        with open("paquery_property_result.html", "w", encoding="utf-8") as f:
            f.write(html_post)
except Exception as e:
    print("❌ POST Error:", e)
