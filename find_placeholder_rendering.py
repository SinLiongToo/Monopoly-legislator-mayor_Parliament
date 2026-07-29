import re

with open("index.html", "r", encoding="utf-8") as f:
    html = f.read()

matches = [m.start() for m in re.finditer(r'臺南市選區土地建物', html)]
print(f"在 index.html 中發現 {len(matches)} 處 '臺南市選區土地建物'：")

for i, p in enumerate(matches, 1):
    print(f"\n--- Location {i} (index: {p}) ---")
    snippet = html[max(0, p-200):min(len(html), p+300)]
    print(snippet)
