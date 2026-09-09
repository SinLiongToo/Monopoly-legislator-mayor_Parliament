import asyncio
import sys
import os
import json
from playwright.async_api import async_playwright

if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

DOWNLOAD_DIR = "./downloads_priso"

# 需補齊之中央立法委員與縣市長名冊（共 82 位）
TARGET_OFFICIALS = [
    # 縣市長
    "楊文科", "王惠美", "張麗善", "黃敏惠", "翁章梁", "林姿妙", "徐榛蔚", "饒慶鈴", "陳光復", "陳福海", "王忠銘", "黃偉哲",
    # 區域與不分區立法委員
    "黃國昌", "王鴻薇", "林沛祥", "李彥秀", "羅智強", "賴士葆", "鄭正鈐", "羅明才", "柯志恩", "江啟臣", 
    "張智倫", "葉元之", "洪孟楷", "牛煦庭", "陳玉珍", "涂權吉", "魯明哲", "呂玉玲", "邱若華", "廖先翔", 
    "林德福", "林思銘", "徐欣瑩", "楊瓊瓔", "廖偉翔", "黃健豪", "羅廷瑋", "游顥", "丁學忠", "黃建賓", 
    "鄭天財", "黃仁", "盧縣一", "葛如鈞", "吳宗憲", "林倩綺", "陳永康", "許宇甄", "王育敏", "高金素梅", 
    "孔文吉", "蔡其昌", "林俊憲", "賴瑞隆", "沈伯洋", "洪申翰", "王世堅", "黃捷", "吳思瑤", "吳沛憶", 
    "林淑芬", "李坤城", "吳秉叡", "蘇巧慧", "張宏陸", "吳琪銘", "陳俊宇", "陳秀寳", "黃秀芳", "陳素月", 
    "何欣純", "郭國文", "陳亭妃", "林宜瑾", "賴惠員", "王定宇", "邱議瑩", "邱志偉", "李柏毅", "張啓楷", 
    "林國成", "麥玉珍", "林憶君", "吳春城", "劉書彬", "游錫堃", "張嘉郡", "蘇清泉", "陳菁徽", "范雲"
]

async def download_officials(officials_list):
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)
    print("=" * 65)
    print(f"🚀 開始監察院 PRISO 自動化下載：共 {len(officials_list)} 位中央立委與首長")
    print(f"📁 儲存目錄: {DOWNLOAD_DIR}")
    print("=" * 65)

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(accept_downloads=True)
        page = await context.new_page()

        success_count = 0
        skip_or_fail = []

        for idx, name in enumerate(officials_list, 1):
            print(f"\n[{idx}/{len(officials_list)}] 正在查詢與下載: 【{name}】...")
            
            existing = [f for f in os.listdir(DOWNLOAD_DIR) if f.startswith(f"{name}_財產申報_")]
            if len(existing) >= 1:
                print(f"  ⏩ 【{name}】本地已有 {len(existing)} 份申報 PDF，跳過下載。")
                success_count += 1
                continue

            try:
                await page.goto("https://priso.cy.gov.tw/layout/baselist", wait_until="networkidle", timeout=30000)
                
                input_el = await page.wait_for_selector("input[placeholder*='請輸入'], input[placeholder*='查詢'], input", timeout=10000)
                await input_el.fill(name)
                await asyncio.sleep(0.4)

                send_btn = await page.wait_for_selector("button:has-text('送出'), input[value*='送出']", timeout=5000)
                await send_btn.click()

                await page.wait_for_timeout(2500)

                links = await page.query_selector_all("a, tr td a, .mat-cell a")
                target_links = []
                for l in links:
                    t = (await l.inner_text()).strip()
                    if name in t or "廉政專刊" in t or "申報" in t:
                        target_links.append((l, t))

                if not target_links:
                    print(f"  ⚠️ 【{name}】在 PRISO 未檢索到可下載申報連結。")
                    skip_or_fail.append(name)
                    continue

                downloaded_for_this = 0
                for file_idx, (link, text) in enumerate(target_links[:2], 1):
                    try:
                        async with page.expect_download(timeout=15000) as download_info:
                            await link.click()
                        download = await download_info.value
                        save_name = f"{name}_財產申報_{file_idx}.pdf"
                        save_path = os.path.join(DOWNLOAD_DIR, save_name)
                        await download.save_as(save_path)
                        print(f"  🎉 成功儲存: {save_name} ({os.path.getsize(save_path):,} bytes)")
                        downloaded_for_this += 1
                    except Exception as de:
                        print(f"  ❌ 第 {file_idx} 筆點擊下載失敗: {de}")

                if downloaded_for_this > 0:
                    success_count += 1
                else:
                    skip_or_fail.append(name)

                await asyncio.sleep(1)

            except Exception as e:
                print(f"  ❌ 處理 {name} 時發生異常: {e}")
                skip_or_fail.append(name)

        await browser.close()

    print("\n" + "=" * 65)
    print(f"🏁 下載任務完成！")
    print(f"✅ 成功官員數: {success_count} / {len(officials_list)}")
    if skip_or_fail:
        print(f"⚠️ 未完成或需手動確認者 ({len(skip_or_fail)}): {', '.join(skip_or_fail)}")
    print("=" * 65)

if __name__ == "__main__":
    asyncio.run(download_officials(TARGET_OFFICIALS))
