import re

with open("main.30476152531ff721.js", "r", encoding="utf-8") as f:
    text = f.read()

# 搜尋包含 api 或 BASE 或 http 的變數賦值
assigns = re.findall(r'([a-zA-Z0-9_$]+Url|[a-zA-Z0-9_$]+API|baseUrl|apiUrl)\s*[:=]\s*["\']([^"\']+)["\']', text, re.IGNORECASE)
print("URL Assignments found:", assigns)

# 搜尋包含 baselist 的周圍文字 (500 字元)
idx = text.find("baselist")
if idx != -1:
    print("\nText around 'baselist':")
    print(text[max(0, idx-300):min(len(text), idx+300)])
else:
    print("'baselist' not found in main.js")

# 搜尋包含 Search 或 Query 或 Officer 的周圍文字
for kw in ["Officer", "Declara", "Query", "BaseList", "申报", "申報"]:
    pos = text.find(kw)
    if pos != -1:
        print(f"\nText around '{kw}':")
        print(text[max(0, pos-150):min(len(text), pos+150)])
        break
