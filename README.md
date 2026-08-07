# Morning Alpha v0.1

Morning Alpha 是一個以繁體中文為主要介面的科技新聞儀表板學習專案。

專案定位是「科技新聞事件分析與投資晨報」，目標是自動蒐集科技新聞，整理成晨間投資摘要，幫助投資人快速掌握市場重點。

專案將逐步完成以下流程：

1. 收集科技新聞。
2. 將新聞資料儲存到 MySQL。
3. 使用 Pandas 進行統計分析。
4. 產生提供投資人閱讀的 HTML 儀表板。

目前已經可以收集 TechNews 首頁最新五篇文章、使用 Pandas 整理資料、寫入 MySQL，並讀取全部新聞後顯示最新 20 筆。尚未包含視覺化或 HTML 功能。

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
│   └── read_news.py
├── data/
│   ├── raw/
│   └── processed/
├── sql/
├── dashboard/
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
- `title`：新聞標題，不允許重複。
- `publish_time`：新聞發布時間。
- `url`：原始文章網址。
- `created_at`：資料寫入 MySQL 的時間。

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

## 目前限制

- 只收集 TechNews 首頁最新五篇文章。
- 目前只讀取全部新聞並顯示最新 20 筆，尚未提供條件查詢。
- 尚未加入資料視覺化。
- 尚未產生 HTML 儀表板。
- 網站 HTML 結構改變時，爬蟲 selector 可能需要更新。

## 目前進度

- [x] 初始化專案結構
- [x] 收集 TechNews 首頁最新五篇文章
- [x] 使用 Pandas 建立並整理 DataFrame
- [x] 儲存新聞到 MySQL
- [x] 讀取全部新聞並顯示最新 20 筆
- [ ] 使用 Pandas 進行統計分析
- [ ] 產生 HTML 儀表板
