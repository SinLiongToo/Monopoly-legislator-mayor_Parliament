import urllib.request
import urllib.parse
import ssl
import re

url = "https://sunshine.cy.gov.tw/PAQuery.aspx?n=20&sms=0"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
}
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

req = urllib.request.Request("https://sunshine.cy.gov.tw/PAQuery.aspx?n=20&sms=0", headers=headers)
with urllib.request.urlopen(req, context=ctx, timeout=12) as resp:
    html = resp.read().decode('utf-8', errors='ignore')

# 找出所有的 input, select, radio, button
inputs = re.findall(r'<input[^>]+>', html)
print("Found inputs in PAQuery n=20 page:")
for i in inputs:
    if any(k in i for k in ['type="radio"', 'type="submit"', 'type="text"', 'name=']):
        print("  ", i)

# 搜尋選單或頁籤選項 (如 財產申報, 廉政專刊, 政治獻金, 簡易查詢)
radios_and_options = re.findall(r'(<input[^>]+type=["\']radio["\'][^>]*>[\s\S]*?</label>|<option[^>]*>[\s\S]*?</option>)', html)
print("\nRadio/Option Elements:")
for ro in radios_and_options[:20]:
    clean_ro = re.sub(r'\s+', ' ', ro).strip()
    print("  ", clean_ro)
