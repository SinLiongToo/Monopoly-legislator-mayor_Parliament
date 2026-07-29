import re

with open("main.30476152531ff721.js", "r", encoding="utf-8") as f:
    text = f.read()

# 搜尋 Angular 物件中的 key，例如 keyword, name, pageIndex, pageSize, query
keys = re.findall(r'([a-zA-Z0-9_$]+)\s*:\s*(?:this\.|e\.|t\.|["\'])', text)
interesting = [k for k in set(keys) if any(w in k.lower() for w in ['name', 'keyword', 'page', 'size', 'query', 'decl', 'baselist', 'search'])]
print("Interesting payload keys found in main JS:", interesting[:25])
