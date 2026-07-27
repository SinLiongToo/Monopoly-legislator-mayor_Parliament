# 🎲 台灣官員財產申報資料大富翁 (Taiwan Officials Property Declaration Monopoly)

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![GitHub Pages](https://img.shields.io/badge/Deployment-GitHub%20Pages-blue.svg)](https://pages.github.com/)
[![Data Verification](https://img.shields.io/badge/Data%20Verification-100%25%20Real%20Names-success.svg)](#資料來源說明與引用出處)

本專案為一套專門整理、分析與比較台灣政府公職人員（包含全台 **22 縣市長**、**第 11 屆 113 位立法委員全員**、以及 **全台 22 縣市議會 900+ 席全體真實議員名錄**）依法向監察院及相關機關申報財產資料的開源網頁應用程式。

已完整涵蓋 **全台 22 縣市長（含前台北市長柯文哲）**、**全體 113 位立法委員** 與 **全台 22 縣市議會 900+ 席真實民代姓名** 之財產申報紀錄與查核索引（總計 1,024 位真實官員），所有官員均使用 **100% 當選人真實姓名**，完全消除通用席次占位符。

---

## 🐍 Python 全套工具腳本完整分類對照表 (Complete Python Tools Registry)

專案內包含三大類 Python 腳本工具，分別適用於主流程執行、資料盤點清理與分析測試：

### 🌟 1. 主資料管線與抓取解析腳本 (Core Pipeline Scripts)

| 腳本名稱 | 核心用途與功能說明 | 預設輸入與輸出 | 常用執行指令範例 |
| :--- | :--- | :--- | :--- |
| **`download_priso_individual_pdfs.py`** | **監察院 PRISO 個人獨立申報 PDF 下載器**<br/>讀取 1,024 位官員名冊，自動連線 PRISO 系統檢索並下載個人專屬申報 PDF。 | **輸入**：`target_officers.json`<br/>**輸出**：`./downloads_priso/姓名_個人申報.pdf` | `python download_priso_individual_pdfs.py` |
| **`parse_priso_individual_pdfs.py`** | **監察院 PRISO 個人獨立 PDF 專用解析引擎**<br/>專門解析 PRISO 個人 PDF 內文格式，萃取真實存款金額與不動產筆數，並自動寫入 `index.html`。 | **輸入**：`./downloads_priso/*.pdf`<br/>**輸出**：`updated_declarations.json` & `index.html` | `python parse_priso_individual_pdfs.py` |
| **`fetch_priso_declarations.py`** | **監察院 PRISO 申報名冊索引下載器**<br/>讀取 1,024 位官員名冊，自動產出監察院 PRISO (priso.cy.gov.tw) 官方檢索索引。 | **輸入**：`target_officers.json`<br/>**輸出**：`priso_declarations_index.json` | `python fetch_priso_declarations.py` |
| **`parse_priso_declarations.py`** | **監察院 PRISO 名冊解析與網頁同步工具**<br/>解析 PRISO 檢索索引，遵循最高權威優先原則，全量補齊與寫入 `index.html`。 | **輸入**：`priso_declarations_index.json`<br/>**輸出**：`updated_declarations.json` & `index.html` | `python parse_priso_declarations.py` |
| **`download_gazettes.py`** | **監察院專刊 PDF 自動下載器**<br/>連線監察院官方網頁下載專刊 PDF，並自動開啟 PDF 第 1 頁識別期數貼標與去重。<br/>**支援 PageSize=200 高速抓取與任意頁數區間！** | **輸入**：監察院電子書網頁<br/>**輸出**：`./downloads/廉政專刊_第XXX期.pdf` | `python download_gazettes.py 1 2`<br/>*(專小大容量一次抓取全站 204 本專刊)* |
| **`polite_scraper_parser.py`** | **監察院 PDF 解析與網頁同步主引擎**<br/>萃取 1,030 位官員/立委之真實存款、不動產筆數、股票明細與債務，並自動同步寫入網頁。 | **輸入**：`./downloads/*.pdf`<br/>**輸出**：`updated_declarations.json` & `index.html` | `python polite_scraper_parser.py`<br/>`python polite_scraper_parser.py --html-only` |
| **`fetch_cec_declarations.py`** | **中選會競選申報 PDF 自動下載器**<br/>連線至中選會選務資料庫，搜尋全台議員/候選人競選財產申報 PDF。 | **輸入**：中選會選務資料庫<br/>**輸出**：`./downloads_cec/中選會_縣市_姓名.pdf` | `python fetch_cec_declarations.py` |
| **`parse_cec_declarations.py`** | **中選會 PDF 解析與網頁同步工具**<br/>解析中選會表格，遵循「監察院最高權威優先原則」與 `Smart Merge` 防 0 元覆蓋合併數據。 | **輸入**：`./downloads_cec/*.pdf`<br/>**輸出**：`index.html` | `python parse_cec_declarations.py` |

---

### 📊 2. 資料盤點與維護清理工具腳本 (Data Audit & Maintenance Tools)

| 腳本名稱 | 核心用途與功能說明 | 預設輸入與輸出 | 常用執行指令範例 |
| :--- | :--- | :--- | :--- |
| **`audit_actual_html_data.py`** | **全台官員資料「實際核對 vs 預設樣板」盤點工具**<br/>點對點掃描 `index.html` 實體文字，按四大獨立職類（縣市長、立委、正副議長、議員）與 22 縣市產出盤點報告。 | **輸入**：`index.html`<br/>**輸出**：[actual_report.md](actual_report.md) | `python audit_actual_html_data.py` |
| **`clean_duplicate_pdfs.py`** | **PDF 檔案去重與清理腳本**<br/>自動辨識並刪除臨時或重複下載的 PDF 檔。 | **輸入**：`./downloads/`<br/>**輸出**：乾淨去重後的目錄 | `python clean_duplicate_pdfs.py` |
| **`rename_gazettes_by_content.py`** | **依 PDF 第 1 頁標題批次重命名工具**<br/>開啟 PDF 內文自動抓取期數並補齊檔名。 | **輸入**：未貼標 PDF<br/>**輸出**：`廉政專刊_第XXX期.pdf` | `python rename_gazettes_by_content.py` |

---

## 🛠️ 三大來源全自動資料更新與實戰應用指南 (Operations Guide)

```
【管道 1：PRISO 個人獨立 PDF 下載與專用解析】 ➔ python download_priso_individual_pdfs.py && python parse_priso_individual_pdfs.py
【管道 2：監察院專刊 PDF 下載與解析】       ➔ python download_gazettes.py 1 2 && python polite_scraper_parser.py
【管道 3：中選會競選申報下載與解析】       ➔ python fetch_cec_declarations.py && python parse_cec_declarations.py
【產出盤點報告查看進度】                    ➔ python audit_actual_html_data.py
【一鍵 Git 推送公開發布】                  ➔ git add . && git commit -m "..." && git push origin main
```

---

### 🚀 Git 發布至 GitHub Pages

完成資料更新後，執行以下指令完成全網公開發布：
```bash
git add .
git commit -m "Add parse_priso_individual_pdfs.py dedicated parser for PRISO individual PDFs"
git push origin main
```

---

## 📌 資料來源說明與引用出處 (Data Sources & Legal Foundations)

本專案所有官員與民代之財產申報資料均來自以下三大官方與權威公開管道：

1. **監察院公職人員財產申報線上查閱專區 (PRISO 權威來源 1)**
   * **官方網址**：[監察院 PRISO 系統 (https://priso.cy.gov.tw/layout/baselist)](https://priso.cy.gov.tw/layout/baselist)
   * **涵蓋對象**：全台 22 縣市長、113 位立法委員、全台 22 縣市議會 900+ 席全體議員名冊索引與個人獨立申報文件。

2. **監察院廉政專刊電子書（權威來源 2）**
   * **官方網址**：[監察院廉政專刊電子書查詢專區 (https://sunshine.cy.gov.tw/News.aspx?n=17&sms=8861)](https://sunshine.cy.gov.tw/News.aspx?n=17&sms=8861)
   * **涵蓋對象**：全台 22 縣市長、113 位立法委員、直轄市議員（雙北、桃園、台中、台南、高雄六都議員）與正副議長。

3. **中央選舉委員會 (CEC) 候選人財產申報公開專區（權威來源 3）**
   * **官方網址**：[中央選舉委員會選務資料庫 (https://db.cec.gov.tw/)](https://db.cec.gov.tw/)
   * **涵蓋對象**：全台 22 縣市所有公職人員選舉候選人（包含全台 22 縣市所有議員候選人）。

4. **各縣市議會政風室「現場查閱專區」（權威來源 4）**
   * **涵蓋對象**：非直轄市之 16 縣市議員（如苗栗、彰化、南投、屏東、宜蘭、基隆等）。
   * **法規與實務說明**：依《公職人員財產申報法》第六條第二項規定，非直轄市縣市議員之例行申報由各縣市議會政風室現場查閱，依法不提供網路 PDF 下載。

---

## 🌟 主要功能 (Core Features)

### 1. 🗂️ 全台官員資料庫與 22 縣市議會 900+ 席真實議員總覽
* **全涵蓋全台 22 縣市真實議員**：完整載入全台 22 縣市議會第 4 屆（2022-2026）真實議員姓名名錄（包含臺北市、新北市、桃園市、臺中市、臺南市、高雄市、基隆市、新竹市、新竹縣、苗栗縣、彰化縣、南投縣、雲林縣、嘉義市、嘉義縣、屏東縣、宜蘭縣、花蓮縣、臺東縣、澎湖縣、金門縣、連江縣）。
* **22 縣市選區即時篩選**：可按 22 縣市選區、政黨、職位（縣市長/立法委員/縣市議員）及姓名即時過濾與統計。

### 2. 📜 歷年申報資料查閱 (Filing History & Details)
* **完整欄位結構化呈現**：條列土地、建物、車輛、存款總額、有價證券（股票、債券、基金）、保單件數、債權、債務細項及事業投資。
* **法源與資料來源說明**：依《公職人員財產申報法》第六條規定，明確標註資料係來自「監察院 PRISO 官方檢索索引」、「監察院廉政專刊原始 PDF 核對（精準帶期數檔名與時間戳記）」、「中選會公職人員候選人申報」或「各縣市議會政風室現場查閱專區」。

---

## 📄 開源授權 (License)

本專案採用 [MIT License](LICENSE) 宣告開源。
