import sys

if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

with open("paquery_search_result.html", "r", encoding="utf-8") as f:
    lines = f.readlines()

for idx, line in enumerate(lines, 1):
    if "李宗霖" in line:
        print(f"Line {idx}: {line.strip()[:200]}")
        # 印出前後 5 行
        start = max(0, idx - 6)
        end = min(len(lines), idx + 6)
        print("\nContext Around Line:")
        for c_idx in range(start, end):
            print(f"  {c_idx+1}: {lines[c_idx].strip()[:150]}")
        break
