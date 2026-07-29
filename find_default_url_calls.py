import re

with open("main.30476152531ff721.js", "r", encoding="utf-8") as f:
    text = f.read()

# 尋找所有像 "BaseList", "Declaration", "Public", "Query", "Officer", "Search" 等字樣
words = re.findall(r'["\']([a-zA-Z0-9_/]{3,40})["\']', text)
apis = [w for w in set(words) if any(k in w.lower() for k in ['base', 'decl', 'query', 'search', 'list', 'officer', 'person', 'report'])]
print("Found candidate endpoint paths:", sorted(apis)[:40])
