# Morning Alpha 使用手冊

本手冊只描述目前 repository 已實作的功能。Morning Alpha 已完成四個階段的程式開發，目前適合在本機或 Docker 中學習、展示及測試；尚未達到可公開營運的投資產品等級。

## 1. 專案概覽

Morning Alpha 解決的問題是：科技與財經資訊分散在不同來源，而且新聞、公司、股票資料和市場變化不容易一起閱讀。

使用者執行一個 Pipeline 後，可以在 Dashboard 完成以下任務：

1. 集中閱讀 TechNews、中央社財經、自由時報財經與 TWSE 官方重大訊息。
2. 搜尋、排序、分頁，並依來源、分類、公司及同事件篩選。
3. 查看來源、分類、中文關鍵字、來源健康與 Pipeline 歷史。
4. 閱讀每日 07:00（Asia/Taipei）固定時間窗的規則式晨報。
5. 查看新聞標題辨識出的 TWSE 公司、產業與股票代號。
6. 查看 TWSE 每日盤後價格及季度財務摘要。
7. 觀察新聞前後交易日價格變化，但不把時間關聯說成因果。
8. 建立本機公司追蹤清單，閱讀個人化追蹤晨報。

預期使用者是正在學習 Python、資料處理、MySQL 與前端整合的初學者，或需要快速整理繁體中文科技／財經資訊的本機使用者。

## 2. 目前功能

| 功能 | 實際內容 | 主要技術 |
| --- | --- | --- |
| 多來源資訊 | TechNews HTML 最多 5 篇；中央社與自由時報財經 RSS；TWSE 上市公司每日重大訊息 | Requests、BeautifulSoup、XML／JSON parser |
| 共同資料格式 | adapter 轉成相同 News Record，再交給 Pandas | Python、Pandas |
| 新聞身分與去重 | 分開保存取得來源、原始發布媒體與來源文章 ID；canonical URL 與來源文章 ID 使用 UNIQUE index | Python、MySQL |
| 分類與事件分組 | 標題規則分類；72 小時內用共同關鍵字與 Jaccard similarity 分組 | Python |
| 中文關鍵字 | `jieba-py` 斷詞、Pandas 統計 Top 20 | jieba、Pandas |
| 公司資料 | TWSE 上市公司、產業、股票代號及別名 | TWSE OpenAPI、MySQL |
| 公司辨識 | 以公司名、簡稱、ticker 與 alias 比對新聞標題 | Python 規則式 matching |
| 市場價格 | TWSE 上市個股每日盤後價格 | TWSE OpenAPI、PyMySQL |
| 財務摘要 | TWSE 上市公司季度 EPS、營收、利益與淨利 | TWSE OpenAPI、PyMySQL |
| 每日晨報 | 固定時間窗內的來源、分類、關鍵字與最多 5 篇 highlights | Python、MySQL JSON |
| 事件市場觀察 | 找新聞前後可用交易日收盤價並計算變化 | Python、MySQL；標示非因果 |
| 追蹤清單 | 本機單一使用者加入／移除公司 | Flask POST/DELETE、MySQL |
| 個人化晨報 | 只計入追蹤公司且公司比對成功的新聞 | Flask、Python |
| Dashboard | 新聞、圖表、晨報、公司資料、追蹤清單與狀態 | HTML、CSS、JavaScript、Chart.js |
| 自動化與測試 | Docker scheduler、GitHub Actions、unit／integration／Playwright tests | Docker、GitHub Actions |

Dashboard 沒有使用 DataTables。搜尋、篩選、排序及分頁都是原生 JavaScript。

## 3. 系統工作流程

```mermaid
flowchart TD
    A["TechNews HTML"] --> C["新聞 adapters"]
    B["中央社財經 RSS"] --> C
    V["自由時報財經 RSS"] --> C
    U["TWSE 每日重大訊息 OpenAPI"] --> C
    C --> D["BeautifulSoup / XML 解析"]
    D --> E["共同 News Record"]
    E --> F["Pandas 清理、分類與 URL 正規化"]
    F --> G[("MySQL news_records")]

    H["TWSE 公司 OpenAPI"] --> I[("companies / securities / industries")]
    G --> J["標題公司比對"]
    I --> J
    J --> K[("news_company_links")]

    L["TWSE 每日價格 OpenAPI"] --> M[("market_prices")]
    N["TWSE 財務 OpenAPI"] --> O[("financial_metrics")]

    G --> P["每日晨報與資料分析"]
    G --> Q["四個 JSON 備援輸出"]
    G --> R["Flask API"]
    I --> R
    K --> R
    M --> R
    O --> R
    S[("watchlist_items")] --> R
    R --> T["HTML / JavaScript Dashboard"]
```

關鍵觀念：MySQL 是目前 Dashboard 的正式資料來源；`news.json`、`chart_data.json`、`keyword.json`、`metadata.json` 仍由 Pipeline 產生，但主要用於學習、檢查與備援。

新聞的 `source` 是 Morning Alpha 取得資料的 adapter／管道，`publisher` 是原始發布媒體。直接 RSS 或網站來源通常兩者相同；未來若透過聚合服務取得中央社文章，則可保存成 `source=聚合服務`、`publisher=cna`。Dashboard 優先顯示 `publisher`。

## 4. 專案結構

```text
Morning-Alpha/
├── .github/workflows/ci.yml
├── .env.example
├── Dockerfile
├── compose.yaml
├── requirements.txt
├── package.json
├── playwright.config.js
├── dashboard/
│   ├── index.html
│   ├── styles.css
│   └── app.js
├── data/
│   ├── raw/
│   └── processed/
├── docs/
│   ├── DATA_SOURCES.md
│   └── USER_GUIDE.md
├── sql/
│   └── 001 ... 013 migrations
├── src/
│   ├── run_pipeline.py
│   ├── pipeline_process.py
│   ├── api.py
│   ├── scheduler.py
│   ├── run_migrations.py
│   ├── *_adapter.py
│   ├── *_store.py
│   ├── daily_brief.py
│   ├── personalized_brief.py
│   ├── company_matching.py
│   ├── news_company_links.py
│   ├── event_market_analysis.py
│   └── watchlist.py
└── tests/
    ├── fixtures/
    ├── dashboard.spec.js
    └── test_*.py
```

重要檔案：

| 檔案 | 何時執行 | 互動對象 |
| --- | --- | --- |
| `src/run_pipeline.py` | 日常更新 | 所有 adapters、Pandas、MySQL stores、JSON exporters |
| `src/pipeline_process.py` | Dashboard 按下更新時 | 使用 API 當下的 Python 環境啟動並追蹤 Pipeline |
| `src/api.py` | 使用 Dashboard 前 | MySQL 與 `dashboard/` |
| `src/scheduler.py` | 選用 Docker 排程 | 定期呼叫 `run_pipeline.py` |
| `src/run_migrations.py` | 既有 database 升級前 | `sql/001`～`013` |
| `src/news_sources.py` | Pipeline 第 1 步 | TechNews、中央社、自由時報、TWSE 重大訊息 adapters |
| `src/twse_*_adapter.py` | Pipeline 第 2、4、5 步 | TWSE 官方 OpenAPI |
| `src/company_matching.py` | Pipeline 第 3 步 | 公司候選資料與新聞標題 |
| `src/daily_brief.py` | Pipeline 第 6 步 | 新聞 records、固定時間窗 |
| `src/watchlist.py` | API 讀寫追蹤清單 | `watchlist_items`、公司資料 |
| `src/personalized_brief.py` | `/api/personalized-brief` | 追蹤清單、公司新聞關聯 |
| `dashboard/app.js` | 瀏覽器載入首頁 | Flask APIs、DOM、Chart.js |
| `docs/DATA_SOURCES.md` | 閱讀來源設計時 | TWSE 欄位契約與限制 |

## 5. 系統需求

### Docker 方式

- Git
- Docker Desktop
- 現代瀏覽器

Docker image 使用 Python 3.13 slim 與 MySQL 8.4。

### 原生方式

- Python 3.13
- MySQL 8.4
- Git
- 現代瀏覽器
- Node.js 22：只有執行 Playwright tests 需要

`requirements.txt` 已鎖定：Requests 2.34.2、BeautifulSoup 4.15.0、Pandas 3.0.5、PyMySQL 1.2.0、jieba-py 0.46.12、python-dotenv 1.2.2、Flask 3.1.3。Chart.js 是 4.5.1；Playwright 是 1.62.1。

## 6. 安裝

### 方式 A：Docker

1. Clone 並建立 `.env`：

```bash
git clone https://github.com/OllieHu12304/Morning-Alpha.git
cd Morning-Alpha
cp .env.example .env
```

2. 編輯 `.env`，為這份 Docker MySQL 建立一組新密碼：

```text
MYSQL_USER=morning_alpha_app
MYSQL_PASSWORD=請換成安全的新密碼
MYSQL_DATABASE=morning_alpha
```

這組密碼不是 Mac 密碼，也不需要與其他 MySQL 相同。`.env` 不可 commit。

3. Build 並啟動 database：

```bash
docker compose build api
docker compose up -d db
docker compose ps
```

4. 第一次更新及啟動 API：

```bash
docker compose run --rm api python src/run_pipeline.py
docker compose up -d api
```

### 方式 B：原生 Python 與 MySQL

1. Clone、建立 venv、安裝 packages：

```bash
git clone https://github.com/OllieHu12304/Morning-Alpha.git
cd Morning-Alpha
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

2. 以 MySQL 管理員建立 database 與 app user：

```sql
CREATE DATABASE morning_alpha
CHARACTER SET utf8mb4
COLLATE utf8mb4_unicode_ci;

CREATE USER 'morning_alpha_app'@'localhost'
IDENTIFIED BY '請換成安全密碼';

GRANT CREATE, ALTER, INDEX, REFERENCES, SELECT, INSERT, UPDATE, DELETE
ON morning_alpha.*
TO 'morning_alpha_app'@'localhost';
```

3. 建立 `.env`：

```bash
cp .env.example .env
```

填入剛才實際建立的 app user 密碼。`MYSQL_USER` 與 `MYSQL_PASSWORD` 沒有預設值；其他預設是 `localhost`、port `3306`、database `morning_alpha`。

4. 若是既有 database，先備份再執行 Migration：

```bash
./.venv/bin/python src/run_migrations.py
./.venv/bin/python src/run_migrations.py --apply
```

目前最新為 Migration 013：為新聞增加 `publisher`、`source_article_id` 與對應 indexes。全新 database 可直接跑 Pipeline；各 store 會建立最新 tables。

## 7. 如何執行 Morning Alpha

請在 repository 根目錄依序執行。

### Step 1：更新全部資料

```bash
./.venv/bin/python src/run_pipeline.py
```

九個步驟依序為：

1. 新聞擷取、Pandas 整理、MySQL 寫入。
2. TWSE 公司目錄同步。
3. 新聞標題與公司關聯重建。
4. TWSE 每日盤後價格同步。
5. TWSE 季度財務摘要同步。
6. 每日晨報產生與保存。
7. 新聞／metadata JSON 匯出。
8. 圖表 JSON 產生。
9. Top 20 關鍵字 JSON 產生。

九步是相依順序：例如先有公司，才能把新聞連到公司；先有股票代號，價格與財務資料才知道要寫到哪家公司。必要步驟失敗時 Pipeline 會停止，後續步驟保持 `pending`，並盡力保存失敗歷史。

### Step 2：啟動 API 與 Dashboard

```bash
./.venv/bin/python src/api.py
```

開啟 [http://127.0.0.1:5050](http://127.0.0.1:5050)。不要直接雙擊 `dashboard/index.html`，因為頁面需要 Flask API。

### Step 3：日後更新

API 可以保持執行。需要更新時，到 Dashboard 的「Pipeline 執行紀錄」區按下「立即更新資料」即可；執行期間按鈕會鎖定，成功後頁面會自動重新載入最新資料。

這個按鈕會使用 API 當下的 Python 與 MySQL 環境，因此本機 API 更新本機 MySQL，Docker API 更新 Docker MySQL，不會再發生兩個環境交叉讀寫。終端指令 `./.venv/bin/python src/run_pipeline.py` 仍保留給除錯與觀察完整 log 使用。

## 8. 預期結果

下列內容是格式範例，筆數依執行時間與來源內容不同：

```text
Step 1/9：爬取、整理並儲存新聞…
...
Step 9/9：產生 Top 20 關鍵字資料…
Morning Alpha 資料更新完成。
MySQL 新增新聞：[實際筆數] 筆
TWSE 公司資料：[實際筆數] 筆
新聞公司關聯：[實際筆數] 筆
```

JSON 格式範例：

```json
[
  {
    "source": "cna",
    "analysis_category": "金融市場",
    "title": "[新聞標題範例]",
    "publish_time": "2026-08-11T09:00:00",
    "url": "https://example.com/news"
  }
]
```

```json
[
  {"keyword": "半導體", "count": 4}
]
```

Dashboard 應顯示晨報、追蹤晨報、來源健康、Pipeline 歷史、新聞統計、公司市場資料、事件觀察及新聞列表。若某區沒有足夠資料，應顯示空狀態，而不是偽造結果。

## 9. Database

Database 名稱預設是 `morning_alpha`。以下是目前實際 tables。

### 新聞與執行狀態

| Table | 欄位與 datatype | 用途 |
| --- | --- | --- |
| `news_records` | `id BIGINT`、`source/publisher VARCHAR(100)`、`source_article_id VARCHAR(255)`、`source_category VARCHAR(100)`、`analysis_category VARCHAR(100)`、`title VARCHAR(500)`、`publish_time DATETIME`、`url/canonical_url VARCHAR(1000)`、`canonical_url_hash CHAR(64)`、`created_at TIMESTAMP` | 正式新聞；canonical hash 與 `source + source_article_id` 是 UNIQUE |
| `source_health_events` | `id BIGINT`、`source VARCHAR(100)`、`status VARCHAR(20)`、`article_count INT`、`error_message VARCHAR(500)`、`attempted_at TIMESTAMP` | 每次來源成功／失敗事件 |
| `pipeline_runs` | `id BIGINT`、`status VARCHAR(20)`、`started_at/finished_at DATETIME(6)`、`duration_ms BIGINT`、`failed_step VARCHAR(100)`、`step_results JSON`、`error_message VARCHAR(500)` | 完整九步執行歷史；也能讀舊四步紀錄 |
| `daily_briefs` | `id BIGINT`、`brief_date DATE`、`window_start/window_end DATETIME`、`article_count INT`、`brief_payload JSON`、`created_at/updated_at TIMESTAMP` | 每日一份結構化晨報 |

### 公司與市場資料

| Table | 欄位與 datatype | 用途 |
| --- | --- | --- |
| `industries` | `id BIGINT`、`name VARCHAR(100)`、`created_at TIMESTAMP` | 官方產業名稱 |
| `companies` | `id BIGINT`、`name VARCHAR(200)`、`short_name VARCHAR(100)`、`industry_id BIGINT`、`market VARCHAR(30)`、timestamps | 公司實體 |
| `securities` | `id BIGINT`、`company_id BIGINT`、`ticker VARCHAR(20)`、`exchange VARCHAR(30)`、`currency CHAR(3)`、`is_active BOOLEAN`、timestamps | 公司與上市股票代號 |
| `company_aliases` | `id BIGINT`、`company_id BIGINT`、`alias VARCHAR(200)`、`created_at TIMESTAMP` | 標題比對用別名 |
| `news_company_links` | `id BIGINT`、`news_id/company_id BIGINT`、`matched_text VARCHAR(200)`、`match_method VARCHAR(30)`、`confidence DECIMAL(4,3)`、timestamps | 新聞與公司的規則式關聯 |
| `market_prices` | `id/security_id BIGINT`、`trade_date DATE`、OHLC `DECIMAL(18,4)`、`price_change DECIMAL(18,4)`、`volume BIGINT`、`trade_value DECIMAL(24,2)`、`transaction_count BIGINT`、`source VARCHAR(100)`、`fetched_at DATETIME`、timestamps | 每證券／交易日一筆盤後價格 |
| `financial_metrics` | `id/security_id BIGINT`、`report_date DATE`、`fiscal_year SMALLINT`、`fiscal_quarter TINYINT`、`industry VARCHAR(100)`、EPS `DECIMAL(20,4)`、營收／利益／淨利 `DECIMAL(30,2)`、`currency CHAR(3)`、`source VARCHAR(100)`、`fetched_at DATETIME`、timestamps | 每證券／季度一筆財務摘要 |
| `watchlist_items` | `id BIGINT`、`company_id BIGINT`、`created_at TIMESTAMP` | 本機單一使用者追蹤公司；company id 是 UNIQUE |

常用 SQL：

```sql
SELECT * FROM news_records ORDER BY publish_time DESC LIMIT 20;

SELECT COUNT(*) AS news_count FROM news_records;

SELECT source, COUNT(*) AS news_count
FROM news_records
GROUP BY source
ORDER BY news_count DESC;

SELECT c.short_name, s.ticker, w.created_at
FROM watchlist_items AS w
JOIN companies AS c ON c.id = w.company_id
LEFT JOIN securities AS s ON s.company_id = c.id;

SELECT s.ticker, p.trade_date, p.close_price
FROM market_prices AS p
JOIN securities AS s ON s.id = p.security_id
ORDER BY p.trade_date DESC
LIMIT 20;
```

## 10. Dashboard 使用方式

- 每日晨報：顯示固定時間窗、摘要、來源／分類／關鍵字及 highlights。
- 我的追蹤晨報：可用股票代號、公司名稱或簡稱搜尋並加入公司；追蹤 chips 可直接移除，晨報顯示本期相關新聞。
- 公司市場資料：選公司後顯示最近收盤價、價差、EPS、價格圖與季度 table；按「加入追蹤」或「移除追蹤」管理清單。
- 新聞事件與市場變化：只讀時間關聯觀察；不能當成買賣訊號。
- 新聞列表：搜尋標題／來源／分類／公司，使用 select 篩選、點欄位排序及前後頁按鈕。
- 同事件：只有分組成功且多篇的事件才會出現「查看同事件」。文章不會因事件相同而刪除。

## 11. 疑難排解

| 問題 | 原因與處理 |
| --- | --- |
| `ModuleNotFoundError` | 用錯 Python；執行 `./.venv/bin/python -m pip install -r requirements.txt` |
| MySQL `Access denied` | `.env` 帳密與實際 MySQL app user 不一致 |
| `Unknown column`／table 不存在 | 備份後執行 `src/run_migrations.py --apply`，再跑 Pipeline |
| 爬蟲結果空白 | 來源改版、白名單排除或網路失敗；查看 `data/processed/morning_alpha.log` |
| timeout／503 | 外部來源暫時拒絕或太慢；程式最多 retry 3 次 |
| Dashboard `Failed to fetch` | `src/api.py` 未啟動，或直接開啟本機 HTML；使用 port 5050 |
| JSON 找不到 | 從 repository 根目錄跑完整 Pipeline；但 Dashboard 本身使用 API，不依賴 JSON |
| 追蹤清單載入失敗 | 確認 Migration 012 已套用，或重新完成九步 Pipeline |
| Pipeline 在 TWSE 步驟停止 | 市場／財務官方 API 是必要步驟；查看 log，來源恢復後重跑 |
| Docker 修改密碼後仍失敗 | 既有 volume 不會因 `.env` 改密碼；需使用原密碼，或明確刪除不需要的 volume 後重建 |

## 12. 目前限制

- 媒體新聞目前只有 TechNews、中央社財經與自由時報財經，且 TechNews 只看首頁最多 5 篇；TWSE 重大訊息是官方公告，不是媒體新聞。
- [自由時報官方 RSS](https://service.ltn.com.tw/RSS) 的免費使用限個人或非營利機構網站之非商業用途，並須標示新聞出處；本專案若改為商業用途，必須重新確認授權。
- TWSE 重大訊息目前只保存主旨、公司與發言時間，沒有把完整「說明」欄位寫入資料庫。
- 沒有文章全文、生成式 AI 摘要、情緒分析或投資評分。
- 只有 TWSE 上市範圍；沒有 TPEx、海外股票、即時行情或完整歷史回補。
- 公司辨識、事件分組及分類是規則式推論。
- 不同平台同事件只分組、不刪除；canonical URL 阻止相同正規化網址，`source + source_article_id` 阻止同一取得管道重複匯入相同文章。
- 事件與價格分析沒有控制大盤、產業、財報或其他同時因素，不能推論因果。
- 追蹤清單沒有帳號與多使用者隔離；個人化晨報沒有 email／推播發送。
- API 無 authentication、rate limiting、HTTPS 與 production server。
- 本機 scheduler 需要電腦和 Docker 持續運作。
- 外部網站或官方 API 改版時，adapter 仍需人工修改。

## 13. 短期 Roadmap

- v0.2：完成本機 end-to-end 驗收、修正阻擋錯誤並建立穩定 tag。
- v0.3：改善資料品質、公司辨識評估與歷史價格回補策略。
- v0.4：加入可選的多使用者 authentication、通知與雲端部署設計。
- v1.0：在資料授權、監控、安全與分析評估完成後，才考慮公開服務。

Roadmap 是建議，不代表已實作。

## 14. 技術學習與面試摘要

| 技術 | 專案中的證明 | 可說明的觀念 |
| --- | --- | --- |
| Python | adapters、Pipeline、資料驗證、錯誤處理 | 模組、函式、例外、可測試設計 |
| Requests | HTML、RSS、TWSE OpenAPI | timeout、retry、headers、HTTP failure |
| BeautifulSoup | TechNews HTML parser | selector 與網站結構異常 |
| Pandas | News Record 清理、統計、JSON 準備 | DataFrame、缺值、排序、聚合 |
| MySQL | 12 組 migrations 與多張關聯 tables | schema、UNIQUE、index、foreign key、transaction |
| PyMySQL | parameterized SQL、commit／rollback | 防止 SQL injection 與資料一致性 |
| HTML／CSS | Dashboard 語意結構與 responsive layout | 可讀性、狀態與版面 |
| JavaScript | API fetch、DOM、搜尋、分頁、追蹤清單 | async、狀態管理、輸入驗證 |
| Chart.js | 統計與價格趨勢圖 | 將資料轉成 labels／datasets |
| Flask | MySQL-backed REST-style API 與 static files | 前後端邊界、HTTP methods、safe errors |
| Git | 每個 Feature 對應一個 commit | 小步提交、Migration 與可追蹤歷史 |
| Tests／CI | fixtures、unit、MySQL integration、Playwright、Actions | 測試金字塔與可重現環境 |

面試時可以這樣簡述：

> Morning Alpha 是我完成的端到端本機資料產品。我用 adapters 收集 HTML、RSS 與 TWSE OpenAPI，以 Pandas 統一新聞資料，再用 MySQL 管理 canonical URL 去重、公司關聯、價格、財務、晨報與追蹤清單。Flask API 把資料提供給原生 JavaScript Dashboard，並用 unit tests、MySQL integration、Playwright、Docker 與 GitHub Actions 驗證整條流程。我也明確標示規則式分析、非即時資料與非因果觀察的限制。
