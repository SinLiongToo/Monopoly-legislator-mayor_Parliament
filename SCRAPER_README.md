# 🎲 台灣官員財產申報 - 全自動下載、解析、網頁整合與 GitHub Pages 發布全流程指南

本專案提供完全自動化的雙管道資料處理管線（Dual Data Pipeline），遵循以下作業步驟：

```mermaid
flowchart TD
    subgraph 管道A [管道 A：監察院廉政專刊 (最高權威)]
        A1["1. download_gazettes.py 4<br/>自動下載 PDF 與第1頁貼標"] --> A2["2. polite_scraper_parser.py<br/>解析正文與存款並更新 HTML"]
    end
    
    subgraph 管道B [管道 B：中選會競選專區 (補充來源)]
        B1["1. fetch_cec_declarations.py<br/>下載議員候選人申報 PDF"] --> B2["2. parse_cec_declarations.py<br/>解析中選會表格並更新 HTML"]
    end

    A2 --> C["3. Git Commit & Push<br/>發布至 GitHub Pages"]
    B2 --> C
```

---

## 🛠️ 雙管道詳細使用手冊與指令集

### 🔹 管道 A：監察院《廉政專刊》全自動下載與解析手冊

適用對象：**全台 22 縣市長、113 位立法委員、直轄市（六都）議員與正副議長**

1. **下載專刊 PDF（自動帶期數標籤與去重）**：
   ```bash
   # 預設抓取前 4 頁（包含約 80 本廉政專刊 PDF，自動帶期數標籤與去重）
   python download_gazettes.py

   # 自訂抓取頁數（例如抓取前 5 頁共 100 本 PDF，舊檔自動跳過）
   python download_gazettes.py 5
   ```

2. **解析 PDF 並全自動寫入網頁**：
   ```bash
   # 全量解析 ./downloads/ 目錄內所有 PDF，並將最新存款數據寫入 index.html
   python polite_scraper_parser.py

   # 指定特定 1~2 位官員解析（例如：侯友宜、蔣萬安）
   python polite_scraper_parser.py 侯友宜 蔣萬安

   # ⚡ 免讀 PDF 秒級獨立更新 HTML（直接讀取 JSON 於 0.2 秒完成網頁同步）
   python polite_scraper_parser.py --html-only
   ```

---

### 🔹 管道 B：中選會 (CEC) 全自動下載與解析手冊

適用對象：**全台 22 縣市所有公職人員選舉候選人與縣市議員**

1. **下載中選會申報 PDF**：
   ```bash
   # 從中選會競選公開專區下載議員申報 PDF 存至 ./downloads_cec/
   python fetch_cec_declarations.py
   ```

2. **解析中選會 PDF 並全自動寫入網頁**：
   ```bash
   # 解析 ./downloads_cec/ 內所有中選會 PDF，並寫入網頁且標註來源為【中選會】
   python parse_cec_declarations.py
   ```

---

### 👑 雙管道資料衝突與權威優先序法則 (Data Priority Hierarchy)

當同一位官員/民代在《監察院廉政專刊》與《中選會候選人申報》兩邊均有申報紀錄時，系統遵循以下權威優先法則：

1. **第一優先（最高權威）：監察院廉政專刊原始 PDF 申報**
   * 監察院專刊為公職人員就職後每年例行定期申報之最高法律權威記錄。
   * 若兩者均有資料，JSON 檔與網頁資料一律以 **《監察院廉政專刊》** 之數據與期數標籤為主。
2. **第二優先（補強與非直轄市議員）：中選會候選人財產申報**
   * 中選會資料為參選競選期間之公開申報。僅在監察院專刊無其 PDF 紀錄（如非直轄市縣市議員）時作為主要數據填入。
3. **防止 0 元覆蓋與聰明數據合併機制 (Smart Merge)**：
   * 腳本內建 `Smart Merge` 機制，絕不允許備用來源將監察院已核對之真實存款與資產金額覆蓋成 0 元。

---

### 🚀 步驟 3：Git 一鍵發布至 GitHub Pages

完成資料更新後，執行以下指令完成全網公開發布：
```bash
git add .
git commit -m "Update property declarations with exact gazette issue tags and non-zero deposit figures"
git push origin main
```

---

## 📌 資料來源說明與引用出處 (Data Sources & Legal Foundations)

本專案所有官員與民代之財產申報資料均來自以下三大官方與權威公開管道：

1. **監察院廉政專刊電子書（權威來源 1）**
   * **官方網址**：[監察院廉政專刊電子書查詢專區 (https://sunshine.cy.gov.tw/News.aspx?n=17&sms=8861)](https://sunshine.cy.gov.tw/News.aspx?n=17&sms=8861)
   * **涵蓋對象**：全台 22 縣市長、113 位立法委員、直轄市議員（雙北、桃園、台中、台南、高雄六都議員）與正副議長。

2. **中央選舉委員會 (CEC) 候選人財產申報公開專區（權威來源 2）**
   * **官方網址**：[中央選舉委員會選務資料庫 (https://db.cec.gov.tw/)](https://db.cec.gov.tw/)
   * **涵蓋對象**：全台 22 縣市所有公職人員選舉候選人（包含全台 22 縣市所有議員候選人）。

3. **各縣市議會政風室「現場查閱專區」（權威來源 3）**
   * **涵蓋對象**：非直轄市之 16 縣市議員（如苗栗、彰化、南投、屏東、宜蘭、基隆等）。
   * **法規與實務說明**：依《公職人員財產申報法》第六條第二項規定，非直轄市縣市議員之例行申報由各縣市議會政風室現場查閱，依法不提供網路 PDF 下載。
