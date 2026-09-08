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
- **Legal Categorization (Act on Property Declaration Article 6)**:
  - Central officials, legislators, and mayors: published nationally in Control Yuan Gazette (廉政專刊).
  - City & county councilors: kept at local council ethics offices for in-person on-site inspection.
  - When no digital PDF exists: set assets to 0 and record the truthful legal inspection pathway.
- **Triple Sync**: Always synchronize `index.html`, `legislator-assets-compare.html`, and `updated_declarations.json` concurrently.

---

## 2. Standard Workflow

### Step 1: Discover & Index PRISO PDFs
Scan `./downloads_priso/*.pdf`. File naming standard:
`NNNN_姓名_財產申報_N.pdf` or `姓名_財產申報_N.pdf`.
Group all PDFs belonging to the same official.

### Step 2: Batch Extract Full Fields
Run extraction using `parse_priso_individual_pdfs.py` or multi-threaded batch parser:
- **Deposits**: `depositsTotal` (latest / highest official filing)
- **Securities/Stocks**: `stocksTotal` and detailed `stockList` (`name`, `shares`, `amount`)
- **Real Estate**: `realEstate` (`loc`, `area`, `share`, `owner`, `date`, `reason`)
- **Debts**: `debtTotal`
- **Insurance**: `insurance` count and `insuranceList`

### Step 3: Purge Synthetic Templates
Filter out any remaining legacy mock records:
```javascript
const isMock = [4100000, 4500000, 6800000].includes(f.depositsTotal) ||
               [950000, 1200000, 2500000].includes(f.securitiesTotal) ||
               (f.realEstate || []).some(r => r.reason === '買買');
```
Reset mock entries to `0` assets and inject legal notice.

### Step 4: Synchronize Targets
Update the `const DATA = { ... }` object in:
- `index.html`
- `legislator-assets-compare.html`
- `updated_declarations.json`

### Step 5: Verification & Integrity Test
1. **Counter Audit**: Run frequency distribution check on `depositsTotal`. Ensure no synthetic constants appear repeatedly.
2. **Syntax Check**: Run `node -e "new Function(...)"` across all `<script>` tags to ensure 0 JavaScript parse errors.
