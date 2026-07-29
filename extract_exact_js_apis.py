import re

with open("main.30476152531ff721.js", "r", encoding="utf-8") as f:
    text = f.read()

# 找出所有的 HTTP 請求路徑 (e.g., this.http.post, this.http.get)
http_posts = re.findall(r'this\.http\.post(?:<[^>]+>)?\s*\(\s*["`\']([^"`\']+)["`\']', text)
http_gets = re.findall(r'this\.http\.get(?:<[^>]+>)?\s*\(\s*["`\']([^"`\']+)["`\']', text)

print("HTTP POST Endpoints:", http_posts)
print("HTTP GET Endpoints:", http_gets)

# 搜尋所有字串字面值
str_literals = re.findall(r'["\'](/[^"\'\s]{3,50})["\']', text)
api_str = [s for s in set(str_literals) if any(w in s.lower() for w in ['base', 'list', 'decl', 'query', 'search', 'officer', 'sys'])]
print("API String Literals:", api_str)
