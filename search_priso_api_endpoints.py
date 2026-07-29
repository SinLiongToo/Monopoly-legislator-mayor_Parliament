import re

with open("main.30476152531ff721.js", "r", encoding="utf-8") as f:
    text = f.read()

# 搜尋 api/ 後面的所有字串或變數
api_matches = re.findall(r'api/([a-zA-Z0-9_/]+)', text)
print("API endpoints found after 'api/':", list(set(api_matches)))

# 搜尋與查閱相關的中文或關鍵字
coun_matches = re.findall(r'["\']([\u4e00-\u9fa5]{2,10})["\']', text)
print("Sample Chinese labels in system:", [c for c in coun_matches if "申報" in c or "查閱" in c or "議員" in c or "查詢" in c or "名冊" in c])
