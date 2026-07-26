# 🎲 台灣官員財產申報 - 全自動下載、解析、網頁整合與 GitHub Pages 發布全流程指南

本專案提供完全自動化的三管道資料處理管線（Triple Data Pipeline），遵循以下作業步驟：

```mermaid
flowchart TD
    subgraph 管道A [管道 A：監察院 PRISO 申報名冊索引 (最高全覆蓋)]
        A1["1. fetch_priso_declarations.py<br/>自動讀取 1024 位官員產出 PRISO 索引"] --> A2["2. parse_priso_declarations.py<br/>解析 PRISO 名冊並全量寫入網頁"]
    end

    subgraph 管道B [管道 B：監察院廉政專刊 PDF (最高權威)]
        B1["1. download_gazettes.py 1 2<br/>高速抓取全站 204 本專刊 PDF"] --> B2["2. polite_scraper_parser.py<br/>解析正文存款並更新 HTML"]
    end
    
    subgraph 管道C [管道 C：中選會競選專區 (補充來源)]
        C1["1. fetch_cec_declarations.py<br/>下載議員候選人申報 PDF"] --> C2["2. parse_cec_declarations.py<br/>解析中選會表格並更新 HTML"]
    end

    subgraph 盤點 [盤點報告產出]
        D1["python audit_actual_html_data.py<br/>全自動掃描 index.html 產生 actual_report.md"]
    end

    A2 --> E["Git Commit & Push<br/>發布至 GitHub Pages"]
    B2 --> E
    C2 --> E
    D1 --> E
```

---

## 🐍 Python 全套工具腳本完整分類對照表 (Complete Python Tools Registry)

| 腳本名稱 | 核心用途與功能說明 | 預設輸入與輸出 | 常用執行指令範例 |
| :--- | :--- | :--- | :--- |
| **`fetch_priso_declarations.py`** | **監察院 PRISO 申報名冊索引下載器**<br/>讀取 1,024 位官員名冊，自動產出監察院 PRISO (priso.cy.gov.tw) 官方檢索索引。 | **輸入**：`target_officers.json`<br/>**輸出**：`priso_declarations_index.json` | `python fetch_priso_declarations.py` |
| **`parse_priso_declarations.py`** | **監察院 PRISO 名冊解析與網頁同步工具**<br/>解析 PRISO 檢索索引，遵循最高權威優先原則，全量補齊與寫入 `index.html`。 | **輸入**：`priso_declarations_index.json`<br/>**輸出**：`updated_declarations.json` & `index.html` | `python parse_priso_declarations.py` |
| **`download_gazettes.py`** | **監察院專刊 PDF 自動下載器**<br/>連線監察院官方網頁下載專刊 PDF，並自動開啟 PDF 第 1 頁識別期數貼標與去重。<br/>**支援 PageSize=200 高速抓取與任意頁數區間！** | **輸入**：監察院電子書網頁<br/>**輸出**：`./downloads/廉政專刊_第XXX期.pdf` | `python download_gazettes.py 1 2`<br/>*(專小大容量一次抓取全站 204 本專刊)* |
| **`polite_scraper_parser.py`** | **監察院 PDF 解析與網頁同步主引擎**<br/>萃取 1,030 位官員/立委之真實存款、不動產筆數、股票明細與債務，並自動同步寫入網頁。 | **輸入**：`./downloads/*.pdf`<br/>**輸出**：`updated_declarations.json` & `index.html` | `python polite_scraper_parser.py`<br/>`python polite_scraper_parser.py --html-only` |
| **`fetch_cec_declarations.py`** | **中選會競選申報 PDF 自動下載器**<br/>連線至中選會選務資料庫，搜尋全台議員/候選人競選財產申報 PDF。 | **輸入**：中選會選務資料庫<br/>**輸出**：`./downloads_cec/中選會_縣市_姓名.pdf` | `python fetch_cec_declarations.py` |
| **`parse_cec_declarations.py`** | **中選會 PDF 解析與網頁同步工具**<br/>解析中選會表格，遵循「監察院最高權威優先原則」與 `Smart Merge` 防 0 元覆蓋合併數據。 | **輸入**：`./downloads_cec/*.pdf`<br/>**輸出**：`index.html` | `python parse_cec_declarations.py` |

---

## 🛠️ 三大管道使用手冊與實戰範例

### 🔹 管道 A：監察院 PRISO 系統名冊對齊與補齊手冊
```bash
python fetch_priso_declarations.py
python parse_priso_declarations.py
```

### 🔹 管道 B：監察院《廉政專刊》全自動下載與解析手冊
```bash
python download_gazettes.py 1 2
python polite_scraper_parser.py
```

### 🔹 管道 C：中選會 (CEC) 全自動下載與解析手冊
```bash
python fetch_cec_declarations.py
python parse_cec_declarations.py
```

---

### 🚀 Git 一鍵發布至 GitHub Pages

完成資料更新後，執行以下指令完成全網公開發布：
```bash
git add .
git commit -m "Complete all 1,024 officials declarations with PRISO official index and Control Yuan Gazettes"
git push origin main
```
