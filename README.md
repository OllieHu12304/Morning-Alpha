# Morning Alpha v0.1

Morning Alpha 是一個以繁體中文為主要介面的科技新聞儀表板學習專案。

專案定位是「科技新聞事件分析與投資晨報」，目標是自動蒐集科技新聞，整理成晨間投資摘要，幫助投資人快速掌握市場重點。

專案將逐步完成以下流程：

1. 收集科技新聞。
2. 將新聞資料儲存到 MySQL。
3. 使用 Pandas 進行統計分析。
4. 產生提供投資人閱讀的 HTML 儀表板。

目前已經可以收集 TechNews 首頁最新五篇文章，並使用 Pandas 整理資料。尚未包含 MySQL 或 HTML 功能。

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
│   └── analyze_news.py
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

## 目前限制

- 只收集 TechNews 首頁最新五篇文章。
- 尚未將資料儲存到 MySQL。
- 尚未產生 HTML 儀表板。
- 網站 HTML 結構改變時，爬蟲 selector 可能需要更新。

## 目前進度

- [x] 初始化專案結構
- [x] 收集 TechNews 首頁最新五篇文章
- [x] 使用 Pandas 建立並整理 DataFrame
- [ ] 儲存新聞到 MySQL
- [ ] 使用 Pandas 進行統計分析
- [ ] 產生 HTML 儀表板
