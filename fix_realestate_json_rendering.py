import json
import re
import sys

if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

INDEX_HTML_FILE = "index.html"

with open(INDEX_HTML_FILE, "r", encoding="utf-8") as f:
    html = f.read()

pos = html.find('name: "李宗霖"')
if pos != -1:
    start_search = max(0, pos - 150)
    end_search = min(len(html), pos + 1800)
    chunk = html[start_search:end_search]

    # 正確清空跨行多行的 realEstate: [{ ... }] 為 realEstate: []
    new_chunk = re.sub(r'realEstate:\s*\[[\s\S]*?\]', 'realEstate: []', chunk, count=1)

    if new_chunk != chunk:
        html = html[:start_search] + new_chunk + html[end_search:]
        with open(INDEX_HTML_FILE, "w", encoding="utf-8") as f:
            f.write(html)
        print("🎉 成功將 index.html 內李宗霖舊有預設的「臺南市選區土地建物」不動產占位符 100% 清空為 realEstate: []！")
    else:
        print("⚡ index.html 中的 realEstate 已經成功清空為 []。")
