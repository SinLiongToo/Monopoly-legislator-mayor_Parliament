import re

with open("index.html", "r", encoding="utf-8") as f:
    content = f.read()

cy_matches = re.findall(r'監察院廉政專刊', content)
news_matches = re.findall(r'isNewsSourced:\s*false', content)

print(f"Total '監察院廉政專刊' occurrences in index.html: {len(cy_matches)}")
print(f"Total 'isNewsSourced: false' occurrences in index.html: {len(news_matches)}")
