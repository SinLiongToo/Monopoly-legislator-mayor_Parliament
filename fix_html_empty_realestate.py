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

# 尋找李宗霖在 index.html 裡面的物件位置
pos = html.find('name: "李宗霖"')
if pos != -1:
    start_search = max(0, pos - 150)
    end_search = min(len(html), pos + 1800)
    chunk = html[start_search:end_search]

    # 正確將預設舊資料 "臺南市選區土地建物" 的 realEstate 清空為 []
    new_chunk = re.sub(r'(realEstate:\s*\[)[^\]]+(\])', r'\1\2', chunk, count=1)
    
    if new_chunk != chunk:
        html = html[:start_search] + new_chunk + html[end_search:]
        with open(INDEX_HTML_FILE, "w", encoding="utf-8") as f:
            f.write(html)
        print("🎉 [成功] 已將 index.html 內李宗霖舊有預設的「臺南市選區土地建物」不動產舊資料清空為 []（符合實體 5 份 PDF 本欄空白）！")
    else:
        print("⚡ index.html 中的 realEstate 已經是空陣列 []。")
else:
    print("❌ 在 index.html 中找不到李宗霖")
