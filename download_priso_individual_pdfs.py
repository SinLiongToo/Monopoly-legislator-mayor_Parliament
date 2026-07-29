import os
import sys
import json
import time
import random
import asyncio
from playwright.async_api import async_playwright

if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

TARGET_OFFICERS_FILE = "target_officers.json"
PRISO_DOWNLOAD_DIR = "./downloads_priso"
PRISO_BASE_URL = "https://priso.cy.gov.tw/layout/baselist"

# 要過濾掉的非真實姓名（股票代號、公司名稱等）
SKIP_KEYWORDS = ["2330", "2882", "2317", "股", "公司", "3006"]


def build_officer_index(officers: list) -> dict:
    """
    回傳 {name: 全局編號(1-based)} 字典，依 target_officers.json 順序，
    只計算真實官員（跳過股票/公司名稱）。
    """
    index = {}
    counter = 1
    for o in officers:
        name = o.get("name", "").strip()
        if name and not any(k in name for k in SKIP_KEYWORDS):
            if name not in index:
                index[name] = counter
            counter += 1
    return index

async def main():
    os.makedirs(PRISO_DOWNLOAD_DIR, exist_ok=True)

    if not os.path.exists(TARGET_OFFICERS_FILE):
        print(f"❌ 找不到目標官員名冊：{TARGET_OFFICERS_FILE}")
        return

    with open(TARGET_OFFICERS_FILE, "r", encoding="utf-8") as f:
        officers = json.load(f)

    # 建立全局編號對照表（以所有真實官員計算，不受 start_idx 影響）
    officer_index = build_officer_index(officers)
    total_real_officers = len(officer_index)
    pad_width = len(str(total_real_officers))  # 補位寬度，例如 4 → "0007"

    start_idx = 1
    target_officers = []

    if len(sys.argv) > 1:
        arg1 = sys.argv[1].strip()
        if arg1.isdigit():
            start_idx = int(arg1)
            # 以真實官員的全局編號為基準，找到第 start_idx 位之後的官員
            real_officers = [o for o in officers if o.get("name") and not any(k in o["name"] for k in SKIP_KEYWORDS)]
            target_officers = real_officers[start_idx - 1:]
            print(f"📍 [斷線續傳模式] 已指定從第 {start_idx} 位官員開始執行 (跳過前 {start_idx - 1} 位)")
        else:
            specified_names = [a.strip() for a in sys.argv[1:] if not a.startswith("-")]
            matched = [o for o in officers if any(name in o.get("name", "") for name in specified_names)]
            if matched:
                target_officers = matched
            else:
                target_officers = [{"name": name, "county": "全台", "position": "公職人員"} for name in specified_names]
            print(f"🎯 [指定姓名模式] 已鎖定下載 {len(target_officers)} 位官員：{', '.join(specified_names)}")
    else:
        target_officers = officers

    print("==========================================================")
    print(" 🚀 監察院 PRISO 系統 (https://priso.cy.gov.tw/layout/baselist)")
    print(" 🤖 全自動真人行為模擬：「輸入姓名 ➔ 按下送出 ➔ 點擊結果列 PDF 下載」")
    print(f" 👥 目標人數：{len(target_officers)} 位（全局真實官員共 {total_real_officers} 位，編號補位 {pad_width} 碼）")
    print("==========================================================")

    success_count = 0

    async with async_playwright() as p:
        # 啟動 Chromium 瀏覽器
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(accept_downloads=True)
        page = await context.new_page()

        print(f"\n🌐 [啟動瀏覽器] 連線至 {PRISO_BASE_URL}...")
        try:
            await page.goto(PRISO_BASE_URL, wait_until="networkidle", timeout=30000)
        except Exception as e:
            print(f"⚠️ 初次載入警告: {e}")

        for idx, o in enumerate(target_officers, start_idx):
            name = o.get("name", "")
            county = o.get("county", "全台")
            position = o.get("position", "公職人員")

            if not name or any(k in name for k in SKIP_KEYWORDS):
                continue

            # 取得該官員的全局編號（補位字串）
            global_num = officer_index.get(name, 0)
            num_str = str(global_num).zfill(pad_width) if global_num else "????"

            print(f"\n(#{num_str} | {idx}/{len(officers)}) [真人模擬] 處理 [{county} {position}] 【{name}】...")

            try:
                # 1. 尋找輸入框並填入【name】
                input_el = await page.wait_for_selector("input[placeholder*='請輸入'], input[placeholder*='查詢'], input", timeout=10000)
                await input_el.fill("")
                await input_el.fill(name)
                await asyncio.sleep(0.3)

                # 2. 點擊 [送出] 按鈕
                send_btn = await page.wait_for_selector("button:has-text('送出'), input[value*='送出']", timeout=5000)
                print(f"  ├─ 🖱️ 模擬人工輸入【{name}】並按下 [送出]...")
                await send_btn.click()

                # 3. 等待 Angular / 動態表格渲染結果
                await page.wait_for_timeout(2500)

                # 4. 取得結果表格中對應名稱/申報列的可點擊連結
                links = await page.query_selector_all("a, tr td a, .mat-cell a")
                target_links = []
                for l in links:
                    t = (await l.inner_text()).strip()
                    if name in t or "廉政專刊" in t or "申報" in t:
                        target_links.append((l, t))

                if target_links:
                    print(f"  ├─ 🎯 在 PRISO 結果表格發現 {len(target_links)} 個可點擊申報 PDF 下載列，準備全量下載...")
                    for p_idx, (link_el, title_text) in enumerate(target_links, 1):
                        # 新格式：{編號}_{姓名}_財產申報_{申報期次}.pdf
                        pdf_filename = f"{num_str}_{name}_財產申報_{p_idx}.pdf"
                        save_path = os.path.join(PRISO_DOWNLOAD_DIR, pdf_filename)

                        # 同時檢查舊格式（無編號）是否已存在，若有則跳過
                        old_filename = f"{name}_財產申報_{p_idx}.pdf"
                        old_path = os.path.join(PRISO_DOWNLOAD_DIR, old_filename)

                        # 已存在（新格式）跳過
                        if os.path.exists(save_path) and os.path.getsize(save_path) > 1000:
                            print(f"  │  ⚡ 【{pdf_filename}】 本機已存在，跳過重複下載。")
                            success_count += 1
                            continue
                        # 舊格式已存在 → 改名為新格式後跳過
                        if os.path.exists(old_path) and os.path.getsize(old_path) > 1000:
                            os.rename(old_path, save_path)
                            print(f"  │  🔄 舊格式已存在，已改名 → 【{pdf_filename}】")
                            success_count += 1
                            continue

                        print(f"  │  🖱️ 模擬人工點擊第 {p_idx} 筆申報列... 觸發瀏覽器下載")
                        try:
                            async with page.expect_download(timeout=15000) as download_info:
                                await link_el.click()
                            
                            download = await download_info.value
                            await download.save_as(save_path)
                            f_size = os.path.getsize(save_path)
                            print(f"  │  🎉 [成功點擊下載] ➔ 【{pdf_filename}】 ({f_size:,} bytes)")
                            success_count += 1
                            await asyncio.sleep(random.uniform(0.5, 1.2))
                        except Exception as e_dl:
                            print(f"  │  ❌ 點擊下載觸發失敗 ({pdf_filename}): {e_dl}")
                else:
                    print(f"  └─ ⚡ 搜尋完成：【{name}】 已登記 PRISO 官方索引標記。")

            except Exception as e:
                print(f"  └─ ❌ 模擬操作 【{name}】 時發生例外: {e}")

        await browser.close()

    print("\n==========================================================")
    print(f" 🎉 [處理完成！] 共成功下載與對齊 {success_count} 個官員/議員個人專屬申報 PDF 檔案！")
    print(f" 📂 PDF 儲存目錄：{os.path.abspath(PRISO_DOWNLOAD_DIR)}")
    print("==========================================================")

if __name__ == "__main__":
    asyncio.run(main())
