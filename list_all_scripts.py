import os
import glob

py_files = sorted(glob.glob("*.py"))

info_list = []
for p in py_files:
    size = os.path.getsize(p)
    info_list.append(f"{p} ({size} bytes)")

with open("all_py_files.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(info_list))

print("Total Python files:", len(py_files))
