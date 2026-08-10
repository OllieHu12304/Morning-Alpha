# Morning Alpha v0.1

Morning Alpha 是一個以繁體中文為主要介面的科技新聞儀表板學習專案。

專案定位是「科技新聞事件分析與投資晨報」，目標是自動蒐集科技新聞，整理成晨間投資摘要，幫助投資人快速掌握市場重點。

專案將逐步完成以下流程：

1. 收集科技新聞。
2. 將新聞資料儲存到 MySQL。
3. 使用 Pandas 進行統計分析。
4. 產生提供投資人閱讀的 HTML 儀表板。

目前已經可以收集 TechNews 首頁最新五篇文章、使用 Pandas 整理資料、寫入及讀取 MySQL，並產生包含統計圖表與可排序新聞列表的 HTML dashboard。

## 技術範圍

- Python
- Requests
- BeautifulSoup
- Pandas
- MySQL
- HTML
- CSS
- JavaScript
- Git

## 專案結構

```text
morning-alpha/
├── src/
│   ├── crawler.py
│   ├── analyze_news.py
│   ├── store_news.py
│   ├── read_news.py
│   ├── export_news_json.py
│   ├── generate_chart_data.py
│   ├── analyze_keywords.py
│   └── run_pipeline.py
├── data/
│   ├── raw/
│   └── processed/
├── sql/
│   └── 001_add_news_quality_fields.sql
├── dashboard/
│   ├── index.html
│   ├── styles.css
│   ├── app.js
│   ├── news.json
│   ├── chart_data.json
│   └── keyword.json
├── tests/
├── requirements.txt
└── README.md
```

## 資料夾責任

- `src/`：存放 Python 原始碼。未來的新聞收集、資料清理和統計分析程式會依功能分開放置。
- `data/raw/`：存放剛收集、尚未整理的原始資料。不應手動修改這些資料。
- `data/processed/`：存放清理或分析後產生的資料。
- `sql/`：存放建立或管理 MySQL 資料庫所需的 SQL 檔案。
- `dashboard/`：存放未來產生的 HTML 儀表板及其 CSS、JavaScript 資源。
- `tests/`：存放各項功能的獨立測試。

## 根目錄檔案責任

- `requirements.txt`：記錄專案需要安裝的 Python 套件。
- `README.md`：說明專案目標、結構、安裝方式與目前進度。

## Python 檔案責任

- `src/crawler.py`：使用 Requests 下載 TechNews 首頁，並使用 BeautifulSoup 解析最新五篇文章。
- `src/analyze_news.py`：將爬蟲結果轉成 Pandas DataFrame，去除重複標題、轉換發布時間並排序。
- `src/store_news.py`：使用 PyMySQL 建立 `news_records` table，並將整理後的新聞寫入 MySQL。
- `src/read_news.py`：讀取 `news_records` 全部資料，轉成 DataFrame，並印出發布時間最新的 20 筆。
- `src/export_news_json.py`：將 MySQL 全部新聞整理並匯出為 dashboard 使用的 JSON。
- `src/generate_chart_data.py`：讀取新聞 JSON，統計來源、推論分類與熱門關鍵字。
- `src/analyze_keywords.py`：使用 Pandas 統計新聞標題中的 Top 20 關鍵字。
- `src/run_pipeline.py`：依序完成新聞儲存、JSON 匯出、圖表統計與 Top 20 關鍵字分析。
- `sql/001_add_news_quality_fields.sql`：將既有 `news_records` 升級為包含來源、分類與 canonical URL 的 schema。
- `dashboard/index.html`：定義 dashboard 的標題、圖表區、狀態區與新聞 table。
- `dashboard/styles.css`：負責 dashboard 排版、顏色、圖表卡片、table 與響應式樣式。
- `dashboard/app.js`：載入新聞及統計 JSON、建立 Chart.js 圖表與 table rows，並處理欄位排序。
- `dashboard/news.json`：保存 Python 從 MySQL 匯出的本機新聞資料。
- `dashboard/chart_data.json`：保存 Python 從新聞資料產生的圖表統計。
- `dashboard/keyword.json`：保存 Pandas 產生的 Top 20 關鍵字與出現次數，供後續 dashboard 功能使用。

各空資料夾中的 `.gitkeep` 是空白占位檔，讓 Git 能夠追蹤目前尚未放入程式或資料的資料夾。

## 初始安裝

建議先建立並啟用 Python 虛擬環境，再安裝套件：

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r requirements.txt
```

## 執行新聞爬蟲

從專案根目錄執行：

```bash
python3 src/crawler.py
```

程式會印出 TechNews 首頁最新五篇文章的標題、發布時間與 URL。

## 執行 Pandas 資料整理

從專案根目錄執行：

```bash
python3 src/analyze_news.py
```

程式會依序執行以下轉換：

1. 將文章串列轉成 DataFrame。
2. 根據 `title` 移除重複文章。
3. 將 `publish_time` 從文字轉成 datetime。
4. 依照發布時間由新到舊排序。
5. 在終端機印出整理後的 DataFrame。

## MySQL 首次設定

以下步驟只需要在第一次準備專案時執行。這個專案使用 Homebrew 的 MySQL 8.4。

### 1. 安裝並啟動 MySQL

```bash
brew install mysql@8.4
export PATH="/opt/homebrew/opt/mysql@8.4/bin:$PATH"
brew services start mysql@8.4
mysql --version
```

`mysql@8.4` 是 keg-only，因此新的終端機可能需要重新執行上面的 `export PATH`，才能直接使用 `mysql` 指令。

接著執行安全設定：

```bash
mysql_secure_installation
```

依照提示設定 MySQL root 密碼，並建議移除匿名使用者、禁止遠端 root 登入及移除 test database。root 密碼只用於管理 MySQL，不應提供給 Morning Alpha 程式。

### 2. 建立專案 database 與專用帳號

使用 root 登入。`-p` 會讓 MySQL 在下一步安全地詢問密碼：

```bash
mysql -u root -p
```

進入 `mysql>` 後執行：

```sql
CREATE DATABASE IF NOT EXISTS morning_alpha
CHARACTER SET utf8mb4
COLLATE utf8mb4_unicode_ci;

CREATE USER 'morning_alpha_app'@'localhost'
IDENTIFIED BY RANDOM PASSWORD;

GRANT CREATE, INSERT, SELECT
ON morning_alpha.*
TO 'morning_alpha_app'@'localhost';
```

`IDENTIFIED BY RANDOM PASSWORD` 會顯示一組 MySQL 自動產生的密碼。請立即將它保存到 macOS Passwords、1Password、Bitwarden 或其他密碼管理器，不要寫入專案檔案。

目前只授予以下權限：

- `CREATE`：讓程式建立 `news_records` table。
- `INSERT`：讓程式新增新聞。
- `SELECT`：讓程式讀取新聞。

目前沒有授予 `UPDATE`、`DELETE` 或 `DROP`。

如果已經在 Feature 4 建立過帳號，請使用 root 登入 MySQL，額外執行一次：

```sql
GRANT SELECT
ON morning_alpha.*
TO 'morning_alpha_app'@'localhost';
```

完成後離開 MySQL：

```sql
exit;
```

### 3. 測試專案帳號

```bash
mysql \
  -h localhost \
  -P 3306 \
  -u morning_alpha_app \
  -p \
  morning_alpha
```

輸入 app password 後，如果看到 `mysql>`，代表帳號、密碼、database 和 server 連線正常。測試完成後輸入 `exit;`，目前不需要執行資料查詢。

### 4. 升級既有 Morning Alpha database

如果 `news_records` 是使用舊版程式建立，請先備份：

```bash
mysqldump -u root -p morning_alpha > ../morning_alpha_before_001.sql
```

備份放在 repository 的上一層，避免誤提交到 Git。確認備份檔存在後，使用 root 執行一次 migration：

```bash
mysql -u root -p morning_alpha < sql/001_add_news_quality_fields.sql
```

Migration 會保留既有新聞，將 `source` 回填為 `technews`，並暫時將原始 `url` 複製到 `canonical_url`。不要重複執行同一個 migration。

全新安裝不需要執行這個檔案；第一次執行 `store_news.py` 或 `run_pipeline.py` 時會直接建立新版 table。

## 每次執行專案前的 MySQL 設定

### 1. 確認 MySQL server 已啟動

```bash
brew services list
```

如果 `mysql@8.4` 沒有顯示 `started`：

```bash
brew services start mysql@8.4
```

### 2. 進入專案並啟用虛擬環境

```bash
cd /Users/olliehu/Documents/Codex/2026-08-07/project-constitution
source .venv/bin/activate
```

如果尚未建立 `.venv`：

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r requirements.txt
```

不要將 `.venv/` 提交到 Git。

### 3. 設定連線環境變數

非機密資訊可以直接設定：

```bash
export MYSQL_HOST="localhost"
export MYSQL_PORT="3306"
export MYSQL_USER="morning_alpha_app"
export MYSQL_DATABASE="morning_alpha"
```

使用隱藏輸入設定密碼：

```bash
read -s "MYSQL_PASSWORD?MySQL app password: "
echo
export MYSQL_PASSWORD
```

輸入或貼上密碼時，終端機不會顯示字元，這是正常行為。不要使用 `export MYSQL_PASSWORD="真實密碼"`，因為完整指令可能進入 shell history。

### 4. 執行完成後清除密碼

```bash
unset MYSQL_PASSWORD
```

## MySQL 密碼儲存位置

- MySQL server 保存帳號驗證資訊，不會讓應用程式讀回原始密碼。
- 原始 app password 應保存在個人密碼管理器。
- Morning Alpha 不會將密碼寫入 Python、README、`.env` 或 MySQL 新聞 table。
- `MYSQL_PASSWORD` 只暫存在目前 shell process 的 environment，關閉終端機或執行 `unset MYSQL_PASSWORD` 後即移除。
- 不要將 root password 或 app password 提交到 Git。

## MySQL 常見錯誤

`command not found: mysql`

```bash
export PATH="/opt/homebrew/opt/mysql@8.4/bin:$PATH"
```

`Can't connect to MySQL server`

```bash
brew services start mysql@8.4
```

`Access denied for user`

- 確認 `MYSQL_USER` 是 `morning_alpha_app`。
- 重新從密碼管理器輸入 app password。
- 確認帳號的 host 是 `localhost`。

`Unknown database 'morning_alpha'`

- 使用 root 登入 MySQL，重新執行建立 `morning_alpha` database 的 SQL。

`ModuleNotFoundError: No module named 'pymysql'`

```bash
source .venv/bin/activate
python3 -m pip install -r requirements.txt
```

官方參考資料：

- [Homebrew mysql@8.4](https://formulae.brew.sh/formula/mysql%408.4)
- [MySQL CREATE USER](https://dev.mysql.com/doc/refman/8.4/en/create-user.html)
- [MySQL GRANT](https://dev.mysql.com/doc/refman/8.4/en/grant.html)
- [PyMySQL Connection](https://pymysql.readthedocs.io/en/latest/modules/connections.html)

## 寫入 MySQL

從專案根目錄執行：

```bash
python3 src/store_news.py
```

程式會建立 `news_records` table，並插入最新五篇整理完成的新聞。相同標題已存在時，`INSERT IGNORE` 會略過該筆資料。

`news_records` 包含以下欄位：

- `id`：自動增加的識別碼。
- `source`：穩定的來源識別；目前為 `technews`。
- `source_category`：來源網站提供的分類；目前可以是 `NULL`。
- `analysis_category`：Morning Alpha 分析出的分類；目前可以是 `NULL`。
- `title`：新聞標題，不允許重複。
- `publish_time`：新聞發布時間。
- `url`：原始文章網址。
- `canonical_url`：供後續 URL 去重使用；目前與 `url` 相同。
- `created_at`：資料寫入 MySQL 的時間。

目前仍使用 title UNIQUE constraint 去重。Canonical URL normalization、canonical URL UNIQUE constraint 與移除 title UNIQUE 會在後續 feature 分階段完成。

## 執行完整資料 Pipeline

設定好 MySQL environment variables 後，從專案根目錄執行：

```bash
python3 src/run_pipeline.py
```

Pipeline 會依序執行：

1. 爬取、整理並寫入 MySQL。
2. 從 MySQL 匯出 `dashboard/news.json`。
3. 產生 `dashboard/chart_data.json`。
4. 使用 Pandas 產生 `dashboard/keyword.json`。

任一步驟失敗時，Pipeline 會停止，不繼續執行後面的步驟。

## 讀取 MySQL

先依照「每次執行專案前的 MySQL 設定」準備環境變數，再從專案根目錄執行：

```bash
python3 src/read_news.py
```

程式會執行以下步驟：

1. 從 `news_records` 讀取所有新聞，不在 SQL 使用 `LIMIT`。
2. 使用查詢結果與欄位名稱建立完整 DataFrame。
3. 將 `publish_time` 確認為 Pandas datetime。
4. 依 `publish_time` 由新到舊排序。
5. 使用 `.head(20)` 取得並印出最新 20 筆。

如果 table 少於 20 筆，程式會印出所有現有資料；如果沒有資料，會顯示空資料提示。

## 產生並開啟 HTML Dashboard

先依照「每次執行專案前的 MySQL 設定」準備環境變數，再依序匯出新聞與圖表 JSON：

```bash
python3 src/export_news_json.py
python3 src/generate_chart_data.py
```

接著使用 Python 內建 HTTP server：

```bash
python3 -m http.server 8000 --directory dashboard
```

在瀏覽器開啟：

```text
http://localhost:8000
```

不要直接雙擊 `dashboard/index.html`。Dashboard 使用 JavaScript `fetch()` 載入 `news.json`，瀏覽器通常會限制網頁直接讀取本機檔案。

Dashboard 會顯示新聞來源、主題分類與熱門關鍵字圖表，以及全部匯出的新聞。新聞列表預設依 `publish_time` 由新到舊排列；點擊 Title、Publish Time 或 URL 欄位標題，可以切換排序欄位與方向。

主題分類與熱門關鍵字使用新聞標題中的預設關鍵字規則統計，規則集中定義在 `src/generate_chart_data.py`，未命中分類規則的新聞會歸入「其他」。

## 使用 Pandas 分析 Top 20 關鍵字

先產生最新的 `dashboard/news.json`，再執行：

```bash
python3 src/analyze_keywords.py
```

程式會執行以下步驟：

1. 將 `news.json` 讀取成只包含新聞標題的 DataFrame。
2. 使用 Pandas 字串操作統計候選關鍵字的總出現次數。
3. 依次數由高到低排序；同次數時依關鍵字排序。
4. 最多保留 20 個有出現的關鍵字。
5. 將結果匯出到 `dashboard/keyword.json`。

輸出格式為 JSON array：

```json
[
  {
    "keyword": "AI",
    "count": 12
  }
]
```

Feature 8 只負責產生關鍵字資料，dashboard 將在後續功能讀取 `keyword.json`。

## 目前限制

- 只收集 TechNews 首頁最新五篇文章。
- 目前只讀取全部新聞並顯示最新 20 筆，尚未提供條件查詢。
- 主題分類是關鍵字規則推論結果，不代表新聞來源提供的正式分類。
- Chart.js 從 CDN 載入，第一次開啟 Dashboard 時需要網路連線。
- Dashboard 使用本機 JSON，不會直接連接 MySQL。
- 網站 HTML 結構改變時，爬蟲 selector 可能需要更新。

## 目前進度

- [x] 初始化專案結構
- [x] 收集 TechNews 首頁最新五篇文章
- [x] 使用 Pandas 建立並整理 DataFrame
- [x] 儲存新聞到 MySQL
- [x] 讀取全部新聞並顯示最新 20 筆
- [x] 產生本機 JSON 與可排序 HTML dashboard
- [x] 統計新聞來源、主題分類與熱門關鍵字
- [x] 加入 dashboard 資料視覺化
- [x] 使用 Pandas 匯出 Top 20 關鍵字
