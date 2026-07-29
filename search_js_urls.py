import re

with open("main.30476152531ff721.js", "r", encoding="utf-8") as f:
    text = f.read()

# 搜尋所有字串 (Strings between quotes or backticks)
urls = re.findall(r'["`\'](https?://[^\s"`\']+|(?:/api/|/layout/|/baselist|/Declara|/Query|/Search)[^\s"`\']*)["`\']', text, re.IGNORECASE)
print("Found URLs:", list(set(urls))[:20])

# 搜尋 POST/GET/HttpClient 關鍵字周圍的字串
http_calls = re.findall(r'\.(?:get|post|put|delete)\s*\(\s*["`\']([^"`\']+)["`\']', text, re.IGNORECASE)
print("Found HTTP call paths:", list(set(http_calls)))
