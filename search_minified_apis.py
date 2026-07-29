import re

with open("main.30476152531ff721.js", "r", encoding="utf-8") as f:
    text = f.read()

# 找出所有的叫用 URL 或 API 的片段
matches = re.findall(r'[a-zA-Z0-9_$]+\.(?:post|get)\s*\(\s*`([^`]+)`', text)
print("Backtick template URLs:", matches)

# 搜尋所有的包含 api 的字串
api_templates = re.findall(r'`([^`]*api[^`]*)`', text)
print("API Template literals:", api_templates)
