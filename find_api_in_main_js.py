import re

with open("main.30476152531ff721.js", "r", encoding="utf-8") as f:
    text = f.read()

# 搜尋抓取所有 API 路徑、HttpClient、post/get 請求
matches = re.findall(r'["\'](/[^"\']*api[^"\']*|/[^"\']*BaseList[^"\']*|/[^"\']*Query[^"\']*|/[^"\']*Declara[^"\']*)["\']', text, re.IGNORECASE)
print("API Matches found in Angular bundle:", list(set(matches)))

# 尋找與公職人員申報有關的欄位/路由
routes = re.findall(r'path:["\']([^"\']+)["\']', text)
print("Angular Route paths found:", list(set(routes)))
