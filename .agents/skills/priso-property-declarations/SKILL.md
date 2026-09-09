---
name: priso-property-declarations
description: >-
  Audit, parse, and synchronize official public servant property declarations
  from Control Yuan PRISO PDFs and gazettes. Ensures absolute data veracity,
  purges synthetic placeholders, and updates web frontend and JSON databases.
---

# PRISO Property Declarations Processor & Auditor

This skill provides operational procedures for auditing, parsing, and synchronizing Taiwan public officials' property declarations (Control Yuan PRISO PDFs, gazettes, and local council inspection records).

---

## 1. Core Principles

- **Zero Synthetic Placeholders**: Never populate missing entries with synthetic numbers (e.g., 4.1M, 4.5M, 6.8M, TSMC 2,000 shares, "買買").
- **Legal Categorization & Expiration Rules (Act on Property Declaration Article 6)**:
  - Central officials, legislators, and mayors: published nationally in Control Yuan Gazette (廉政專刊).
  - Expiration Rule: Under Article 6 Paragraph 2 and MOJ ruling, digital declarations are taken offline after 1 year of leaving office. For subsequent candidacies (e.g., Ko Wen-je), officially certified Central Election Commission (CEC) declarations may be adopted with clear legal attribution.
  - City & county councilors: kept at local council ethics offices for in-person on-site inspection. When no digital PDF exists, set assets to 0 and record truthful legal inspection pathway.
- **UI Rankings & Badge Standards**:
  - In Wealth & Real Estate rankings, councilors with in-person inspection must display `—` and `議會現場查閱` badge rather than misleading `NT$ 0` or amber `0 筆`.
  - Header timestamp badge (`update-badge`) is the sole system deployment timestamp (e.g., `2026/09/09 11:00`). Footer explicitly lists the gazette filing year scope.
- **Triple Sync**: Always synchronize `index.html`, `legislator-assets-compare.html`, and `updated_declarations.json` concurrently.

---

## 2. Standard Workflow

### Step 1: Automated Download & PDF Discovery
1. Run Playwright automated batch crawler (`download_central_officials.py`) to search and download official PDF declarations from `https://priso.cy.gov.tw/layout/baselist`.
2. Scan `./downloads_priso/*.pdf`. File naming standard: `NNNN_姓名_財產申報_N.pdf` or `姓名_財產申報_N.pdf`.
3. Group all PDFs belonging to the same official.

### Step 2: Batch Extract Full Fields
Run extraction using `parse_priso_individual_pdfs.py`:
- **Deposits**: `depositsTotal` (latest / highest official filing)
- **Securities/Stocks**: `stocksTotal` and detailed `stockList` (`name`, `shares`, `amount`)
- **Real Estate**: `realEstate` (`loc`, `area`, `share`, `owner`, `date`, `reason`)
- **Debts**: `debtTotal`
- **Insurance**: `insurance` count and `insuranceList`

### Step 3: Purge Synthetic Templates & Placeholders
Filter out any remaining legacy mock records:
```javascript
const isMock = [4100000, 4500000, 6800000].includes(f.depositsTotal) ||
               [950000, 1200000, 2500000].includes(f.securitiesTotal) ||
               (f.realEstate || []).some(r => r.reason === '買買');
```
Reset mock entries to `0` assets and inject legal notice.

### Step 4: Synchronize Targets & UI Renders
Update the `const DATA = { ... }` object in:
- `index.html`
- `legislator-assets-compare.html`
- `updated_declarations.json`

Ensure duplicate `renderRankings` function blocks in both HTML files are kept synchronized with offline councilor badge handling.

### Step 5: Verification & Integrity Test
1. **Counter Audit**: Run frequency distribution check on `depositsTotal`. Ensure no synthetic constants appear repeatedly.
2. **Keyword Purge**: Verify 0 occurrences of `買買` and 2,000 TSMC share placeholders.
3. **Syntax Check**: Run `node -e "new Function(...)"` across all `<script>` tags to ensure 0 JavaScript parse errors.
4. **Git Version Control**: Verify clean git status and commit descriptive log.
