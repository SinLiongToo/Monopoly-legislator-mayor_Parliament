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

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
}
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

urls = [
    "https://sunshine.cy.gov.tw/News.aspx?n=17&sms=8861",
    "https://sunshine.cy.gov.tw/News_Content.aspx?n=17&sms=8861",
    "https://sunshine.cy.gov.tw/Default.aspx"
]

for url in urls:
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, context=ctx, timeout=10) as resp:
            html = resp.read().decode('utf-8', errors='ignore')
            # 尋找頁面內所有連結或 Form 操作
            links = re.findall(r'href=["\']([^"\']+)["\']', html)
            forms = re.findall(r'<form[^>]+action=["\']([^"\']+)["\']', html)
            title = re.findall(r'<title>(.*?)</title>', html)
            print(f"URL: {url} | Title: {title} | Form actions: {forms[:5]}")
            search_links = [l for l in links if any(k in l.lower() for k in ['search', 'query', 'baselist', 'priq', 'sunshine', '17'])]
            print(f"   Candidate Search Links found: {search_links[:10]}")
    except Exception as e:
        print(f"Error {url}: {e}")
