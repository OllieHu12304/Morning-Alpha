# Morning Alpha 期中報告理解講義與演講草稿

> 適用版本：Morning Alpha v0.3.2 之後的目前版本
>
> 文件定位：先協助自己讀懂專案，再從中裁切成 15 分鐘內的口頭報告
>
> 建議分配：簡報約 10 分鐘、實機操作約 3 分 30 秒、切換與緩衝約 1 分 30 秒

## 這份文件怎麼使用

這份文件刻意比實際講稿完整，**不需要逐字全部念完**。每一頁分成四種內容：

- **理解重點**：報告前要真正弄懂的概念。
- **程式對照**：目前 repository 中負責這件事的檔案與精簡程式碼。
- **設計原因**：說明為什麼採用這種方式，以及它解決什麼問題。
- **上台建議講法**：可直接再濃縮成口頭報告的版本。

程式碼只節錄與簡報概念最有關的片段，目的是理解資料如何流動，不是逐行介紹整個專案。

---

## 報告前準備

1. 在 repository 根目錄啟動 Morning Alpha：

   ```bash
   python3 start.py
   ```

2. 確認瀏覽器可以開啟 `http://127.0.0.1:5050`。
3. 預先完成一次 Pipeline，避免把外部網站下載時間算進現場 demo。
4. 在 My Watchlist 加入一間確實有相關新聞的公司。
5. 在 Company Market Data 選好一間具有價格與財務資料的公司。
6. 另開 Terminal，保留最近一次成功 Pipeline 的輸出當作備案。
7. 關閉 `.env`、MySQL 密碼或其他敏感資訊視窗。

---

# 第 1 頁｜Morning Alpha

## 理解重點

Morning Alpha 不是單一爬蟲，也不是單純的新聞網頁。它是一個小型的「資料產品」，將以下工作串成完整流程：

1. 從外部網站取得科技、財經新聞與市場資料。
2. 把不同來源整理成共同格式。
3. 將資料永久保存到 MySQL。
4. 建立新聞、公司與市場價格之間的關聯。
5. 透過 Flask API 把資料轉成前端可以使用的 JSON。
6. 由 JavaScript 將資料呈現在 Dashboard。

專案目前的使用者是希望集中閱讀台灣科技、財經與上市公司消息的個人使用者。它提供的是「資料蒐集、整理與觀察工具」，不是自動投資決策系統。

## 專案定位

```text
Morning Alpha
＝ 新聞收集器
＋ 資料整理流程
＋ MySQL 資料庫
＋ Flask API
＋ 互動式 Dashboard
```

## 設計原因

如果只有爬蟲，資料只能印在 Terminal 或留在記憶體中；如果只有網頁，網頁本身也沒有可靠的資料來源。Morning Alpha 的重點是讓資料從取得、保存、查詢到顯示形成完整閉環。

## 上台建議講法（約 30 秒）

> 大家好，我今天要介紹的專案是 Morning Alpha。它是一套台灣科技與財經新聞整合系統，會自動收集不同來源的新聞、上市公司和市場資料，整理後保存到 MySQL，再透過 Flask API 顯示在 Dashboard。它的目的不是預測股票，而是降低使用者在多個網站之間搜尋、整理和比對資訊的成本。

---

# 第 2 頁｜我想解決什麼問題？

## 理解重點

原始資料分散在新聞網站、RSS、證交所 API 等不同位置，而且資料格式不同。使用者實際遇到的不只是「新聞太多」，還包括：

- 同一家公司消息散落在不同網站。
- 一篇文章可能同時與多家公司有關。
- 同一事件可能被不同媒體重複報導。
- 新聞發布時間、來源名稱與分類格式不一致。
- 新聞和股價資料分開，難以放在相同畫面觀察。
- 每次更新若要手動執行多支程式，操作容易出錯。

因此，這個專案處理的是四層問題：

| 問題層次 | Morning Alpha 的處理方式 |
|---|---|
| 資料取得 | Requests、BeautifulSoup、RSS/XML、JSON |
| 資料品質 | 共同格式、欄位驗證、URL 去重、來源健康狀態 |
| 資料關聯 | 公司別名比對、事件分組、價格與財務資料 |
| 使用介面 | Flask API、JavaScript、Chart.js、搜尋與篩選 |

## 設計原因

將問題拆成不同層次後，每個模組可以獨立測試。例如網站解析錯誤時，可以只測 Adapter；Dashboard 顯示錯誤時，可以直接測 API 回傳，不必重新爬新聞。

## 上台建議講法（約 45 秒）

> 我一開始想解決的是資訊分散問題。科技新聞、財經新聞、公司公告與股價資料來自不同網站，格式也不一樣。使用者不但要切換頁面，還要自行判斷新聞和公司之間的關係。因此我把問題拆成資料取得、資料品質、資料關聯和使用介面四層，讓系統先整理資料，再提供一個可以搜尋和觀察的統一入口。

---

# 第 3 頁｜Morning Alpha 可以完成什麼？

## 理解重點

目前實際完成的功能與負責技術如下：

| 使用者任務 | 系統功能 | 主要技術 |
|---|---|---|
| 集中閱讀新聞 | Latest News、來源與分類篩選、分頁 | Flask API、JavaScript、MySQL |
| 確認資料來源狀態 | 顯示最近嘗試、成功與文章數 | Logging、MySQL、Flask |
| 觀察熱門主題 | Top 20 中文關鍵字與圖表 | jieba、Pandas、Chart.js |
| 找公司相關新聞 | 建立新聞與公司關聯 | 公司名稱／別名規則、MySQL |
| 追蹤特定公司 | 搜尋並加入 My Watchlist | JavaScript、Flask REST API |
| 查看市場資料 | 收盤價、成交資訊與季度摘要 | TWSE JSON、MySQL、Chart.js |
| 閱讀個人化消息 | 依追蹤公司整理近期新聞 | Watchlist、公司關聯、規則式晨報 |
| 更新全部資料 | Dashboard 按鈕或 Terminal 執行 Pipeline | Python orchestration、subprocess |

## 一個重要區分

- Dashboard 的**搜尋與篩選**只處理已經載入的新聞，不會每搜尋一次就重新爬網站。
- Pipeline 的**更新資料**才會連接外部網站、整理並寫入 MySQL。

這個區分能避免使用者每次輸入關鍵字都必須等待外部網路請求。

## 上台建議講法（約 50 秒）

> Morning Alpha 目前可以集中閱讀五個取得來源的新聞與公告，依來源、分類、公司和關鍵字搜尋，也會顯示關鍵字統計、公司價格與部分財務資料。使用者可以搜尋公司加入自選清單，再閱讀相關的近期消息。資料更新則可以直接從 Dashboard 啟動完整 Pipeline。需要注意的是，畫面搜尋只篩選現有資料，真正連接外部來源是在 Pipeline 更新時發生。

---

# 第 4 頁｜資料從哪裡來？為什麼有 HTML、RSS 與 JSON？

## 理解重點

目前五個新聞／公告取得來源如下：

| 來源 | 主要格式 | 解析方式 | 為什麼這樣做 |
|---|---|---|---|
| TechNews 科技新報 | HTML | Requests + BeautifulSoup | 首頁內容直接存在 HTML 標籤中 |
| 中央社財經 | RSS/XML | XML parser | RSS 已提供標題、連結與時間等結構化欄位 |
| 自由時報財經 | RSS/XML | XML parser | 使用官方提供的新聞 feed 比解析版面穩定 |
| Yahoo 股市台股動態 | RSS/XML | XML parser | 聚合來源可保留 publisher 與來源文章身分 |
| TWSE 上市公司重大訊息 | JSON API | `response.json()`／dict | 官方 API 原本就是欄位化資料，不需解析 HTML |

HTML、RSS 和 JSON 並不是專案自行任意拆成三種做法，而是外部來源本身提供不同介面：

- **HTML** 是給人看的網頁，解析時要找標籤、class 或 DOM 結構。
- **RSS/XML** 是給程式訂閱內容的 feed，欄位較固定，但仍要處理命名空間與缺漏值。
- **JSON API** 是給程式交換資料的格式，可直接轉成 Python `dict` 和 `list`。

## 程式對照

`src/news_sources.py` 把五個取得函式集中管理：

```python
source_fetchers = [
    ("technews", "TechNews", fetch_technews),
    ("cna", "中央社財經 RSS", fetch_cna_finance),
    ("ltn", "自由時報財經 RSS", fetch_ltn_business),
    ("yahoo_tw_finance", "Yahoo股市台股動態 RSS", fetch_yahoo_finance),
    ("twse_disclosure", "TWSE 上市公司每日重大訊息", fetch_twse_disclosures),
]
```

單一來源發生錯誤時，系統會記錄結果並繼續下一個來源：

```python
for source, source_name, fetch_articles in source_fetchers:
    try:
        source_articles = fetch_articles()
    except (requests.RequestException, ValueError) as error:
        logger.error("%s 來源失敗：%s", source_name, error)
        continue

    articles.extend(source_articles)
```

## 設計原因與取捨

- 優先使用 RSS 或官方 JSON，因為它們比 HTML 版面穩定。
- 只有來源未提供合適 feed/API 時，才解析 HTML。
- 外部網站仍可能改版、逾時或限制存取，因此每個來源都要獨立處理錯誤。
- Yahoo 是聚合來源，`source` 代表取得管道，`publisher` 才代表原始發布媒體，兩者不能混為一談。

## 上台建議講法（約 70 秒）

> 目前系統有五個新聞與公告取得來源。TechNews 首頁是一般 HTML，因此用 BeautifulSoup 找出文章標籤；中央社、自由時報和 Yahoo 提供 RSS，所以解析 XML；證交所提供官方 JSON API，可以直接轉成 Python 字典。三種方法的差異來自來源本身，而不是為了刻意增加複雜度。每個來源都包在獨立 Adapter 中，單一來源失敗時會留下錯誤紀錄，但不會讓其他來源一起停止。

---

# 第 5 頁｜一則新聞如何進入 Dashboard？

## 理解重點：完整資料流

```text
外部網站
  ↓ HTTP response（HTML／XML／JSON）
來源 Adapter
  ↓ list[dict]，共同 News Record
Pandas
  ↓ DataFrame，轉時間、排序與清理
PyMySQL
  ↓ SQL INSERT，永久保存在 MySQL
Flask API
  ↓ JSON response
JavaScript
  ↓ 儲存前端狀態、篩選、建立 DOM
Dashboard
```

不同階段的資料型態也會跟著改變：

| 階段 | 常見資料型態 | 作用 |
|---|---|---|
| Requests 下載 | `str`、`Response` | 接收外部資料 |
| Adapter 解析 | `list[dict]` | 一篇文章是一個 dictionary |
| Pandas 整理 | `DataFrame` | 批次轉換、排序、統計 |
| PyMySQL 寫入 | `tuple`、SQL row | 對應 Database columns |
| Flask 回傳 | Python `dict` → JSON | 前後端交換資料 |
| JavaScript | Array／Object | 搜尋、篩選、繪圖與渲染 |

## 程式對照 1：Pandas 整理

`src/analyze_news.py` 會把共同格式資料轉成 DataFrame，再處理時間與排序：

```python
dataframe["publish_time"] = pd.to_datetime(
    dataframe["publish_time"],
    errors="coerce",
)

dataframe = dataframe.sort_values(
    by="publish_time",
    ascending=False,
).reset_index(drop=True)
```

`errors="coerce"` 的意思是無法解析的日期會變成 Pandas 的缺失時間 `NaT`，後續可以明確驗證，而不是把錯誤字串直接寫進 Database。

## 程式對照 2：Flask 查詢與回傳 JSON

`src/api.py` 的 `/api/news` 不直接產生 HTML，而是回傳資料：

```python
@app.get("/api/news")
def news():
    dataframe = load_all_news()
    company_links = load_news_company_links()
    return jsonify(build_news_payload(dataframe, company_links))
```

## 程式對照 3：JavaScript 載入資料

`dashboard/app.js` 再用 `fetch()` 呼叫 API：

```javascript
async function loadNews() {
    const payload = await fetchJson(NEWS_API);
    newsRecords = payload.news;
    populateFilters();
    renderTable();
}
```

## 設計原因

瀏覽器不應直接拿到 MySQL 帳密，也不適合直接執行 SQL。Flask 位在中間，負責資料查詢、格式轉換與錯誤處理；JavaScript 只處理使用者互動與畫面呈現。這就是前端、後端與 Database 的基本分工。

## 上台建議講法（約 80 秒）

> 一則新聞會經過多個資料型態。Requests 先下載 HTML、XML 或 JSON，Adapter 把它轉成相同欄位的 Python dictionary，Pandas 再將多筆資料組成 DataFrame，處理時間、排序和缺失值。整理後由 PyMySQL 寫入 MySQL。使用者打開 Dashboard 時，瀏覽器不是直接連資料庫，而是呼叫 Flask API；Flask 查詢 MySQL 並回傳 JSON，最後 JavaScript 把資料渲染成表格和圖表。這幾項技術其實是在同一條資料管線上接力。

---

# 第 6 頁｜不同網站如何共用同一條流程？

## 理解重點：Adapter 與資料契約

每個來源的原始欄位不同，例如可能叫 `pubDate`、`date` 或 `發布日期`。如果後續程式逐一判斷來源，程式會充滿 `if source == ...`。因此專案使用 Adapter，把來源差異隔離在各自模組中。

所有 Adapter 最後都要產生相同 News Record：

| 欄位 | 意義 |
|---|---|
| `source` | Morning Alpha 從哪個管道取得資料 |
| `publisher` | 實際發布文章的媒體或單位 |
| `source_article_id` | 來源提供的文章識別碼 |
| `source_category` | 來源原本提供的分類 |
| `title` | 新聞標題 |
| `publish_time` | 轉成 Python `datetime` 的發布時間 |
| `url` | 原始文章網址 |

## 程式對照

`src/news_record.py` 同時定義格式與基本驗證：

```python
NEWS_RECORD_FIELDS = (
    "source",
    "publisher",
    "source_article_id",
    "source_category",
    "title",
    "publish_time",
    "url",
)
```

```python
return {
    "source": source.strip(),
    "publisher": publisher.strip(),
    "source_article_id": source_article_id,
    "source_category": source_category,
    "title": title.strip(),
    "publish_time": publish_time,
    "url": url.strip(),
}
```

必要文字不能是空白，`publish_time` 必須先轉成 `datetime`。這個共同格式可以視為模組之間的「資料契約」：只要 Adapter 遵守契約，Pandas、MySQL 和 API 就不用知道文章來自哪種網站。

## 設計原因與取捨

- 優點：新增來源時主要新增 Adapter，不需重寫整條 Pipeline。
- 優點：每個 Adapter 可以使用 fixture 獨立測試。
- 代價：每個來源仍要維護自己的解析規則。
- 注意：共同格式只統一欄位，不代表不同來源的資料品質完全相同。

## 上台建議講法（約 60 秒）

> 不同網站的欄位名稱和結構不一樣，所以我建立 Adapter。它可以想成翻譯員，把來源自己的 HTML、RSS 或 JSON 翻成統一 News Record。共同欄位包含取得來源、原始 publisher、文章 ID、分類、標題、發布時間和網址。後面的 Pandas 和 MySQL 只認這份共同格式，因此新增來源時不必重新改寫所有後續程式。這也是專案從單一爬蟲擴充成多來源系統的關鍵。

---

# 第 7 頁｜資料如何避免重複？

## 理解重點：相同文章與相同事件不同

去重必須先區分兩件事：

1. **完全相同的文章**：同一來源、同一網址或同一文章 ID 被重複取得，應阻止重複寫入。
2. **不同媒體報導同一事件**：文章本身不同，應保留每篇報導，只建立跨來源事件分組。

只用標題去重會出現兩種錯誤：

- 兩家媒體使用相同標題，卻被誤刪成只剩一篇。
- 同一篇文章改了一點標題，反而沒有被辨識成重複。

## 程式對照 1：Canonical URL

系統先正規化 URL，例如統一網域大小寫、移除 fragment 與常見追蹤參數，再計算固定長度 SHA-256 hash。MySQL 使用 hash 建立 UNIQUE constraint：

```sql
UNIQUE KEY unique_canonical_url_hash (canonical_url_hash),
UNIQUE KEY unique_source_article (source, source_article_id)
```

`src/store_news.py` 使用：

```sql
INSERT IGNORE INTO news_records (...)
VALUES (...);
```

若 UNIQUE constraint 已存在，MySQL 會忽略這次重複插入；資料規則由 Database 最後把關，而不是只依賴 Python 在記憶體檢查。

## 程式對照 2：事件分組

在輸出 Dashboard 資料時，`src/run_pipeline.py` 會另外呼叫：

```python
records = prepare_dashboard_records(dataframe)
records = group_similar_events(records)
```

因此「文章去重」發生在儲存層，「同事件分組」發生在分析／顯示層。兩者目的不同。

## 設計原因與限制

- URL 與來源文章 ID 對完全重複文章較可靠。
- Database UNIQUE constraint 可防止不同執行批次重複寫入。
- 事件分組目前仍是規則式相似度，可能漏掉標題差異很大的同事件。
- 保留原文能追溯不同媒體觀點，比分組後直接刪除更安全。

## 上台建議講法（約 65 秒）

> 去重時我把相同文章和相同事件分開處理。完全相同的文章會先正規化網址，再用 URL hash，以及來源加文章 ID 的 UNIQUE constraint 阻止重複寫入。不同媒體報導同一事件則不刪除，因為 publisher 和內容仍然不同；系統只在分析層把它們分成同一事件群組。這比只用標題去重更能保留資料來源，也比較不容易誤刪。

---

# 第 8 頁｜一次 Pipeline 更新完成哪些工作？

## 理解重點：Pipeline 是協調者

`src/run_pipeline.py` 不負責所有細節，而是依照資料相依順序呼叫不同模組。完整九個步驟是：

| 步驟 | 工作 | 為何要放在這個順序 |
|---|---|---|
| 1 | 爬取、整理並儲存新聞 | 後面關聯與晨報需要新聞資料 |
| 2 | 同步 TWSE 公司資料 | 公司關聯需要公司與別名目錄 |
| 3 | 建立新聞公司關聯 | 晨報、自選股與事件觀察都會使用 |
| 4 | 同步 TWSE 每日價格 | 事件觀察需要交易日價格 |
| 5 | 同步 TWSE 財務摘要 | 提供公司市場資料區使用 |
| 6 | 產生並保存每日晨報 | 使用已完成的新聞與公司關聯 |
| 7 | 匯出 Dashboard 新聞資料 | 保留靜態 JSON 相容輸出 |
| 8 | 產生圖表資料 | 使用已整理的新聞樣本 |
| 9 | 產生 Top 20 關鍵字 | 使用 jieba 與 Pandas 統計 |

## 程式對照 1：步驟計時與失敗紀錄

```python
def execute_pipeline_step(step_results, step, function):
    step_start_time = time.perf_counter()

    try:
        result = function()
    except Exception:
        update_step_result(step_results, step, "failure", ...)
        raise

    return result, get_duration_ms(step_start_time)
```

每一步都記錄狀態、耗時與摘要，所以 Dashboard 可以顯示最近 Pipeline 歷史，也能知道是哪一步失敗。

## 程式對照 2：從 Dashboard 啟動

Dashboard 按鈕會送出：

```text
POST /api/pipeline/run
```

Flask 再使用 `src/pipeline_process.py` 啟動同一支程式：

```python
_pipeline_process = subprocess.Popen(
    [sys.executable, str(PIPELINE_SCRIPT)],
    cwd=PROJECT_DIRECTORY,
)
```

`sys.executable` 代表沿用目前執行 Flask 的 Python，因此會使用相同 virtual environment 與已安裝套件。Lock 和 process status 則用來阻止重複啟動。

## 設計原因與取捨

- Pipeline 適合長時間、批次且有固定順序的工作。
- 使用 subprocess 可讓 HTTP request 先回應，不必讓瀏覽器連線等待九個步驟完成。
- 目前狀態只存在單一 Flask process 記憶體中，適合本機使用；若要多使用者正式部署，應改成工作佇列，例如 Celery/RQ。

## 上台建議講法（約 80 秒）

> Pipeline 是整個更新流程的協調者。它依序處理新聞、公司目錄、公司關聯、每日價格、財務摘要、晨報和 Dashboard 分析資料。順序不能任意交換，例如建立公司關聯之前必須先有新聞和公司目錄。每一步都記錄成功、失敗和耗時。從網頁按下更新時，Flask 會用目前相同的 Python 環境在背景啟動 `run_pipeline.py`，並阻止使用者重複執行，所以前端可以持續查詢進度，而不必讓一次 HTTP request 等完整流程結束。

---

# 第 9 頁｜實際操作 Morning Alpha

## Demo 前要理解的技術邏輯

實際操作不是只展示畫面，而是驗證前面介紹的資料流：

```text
使用者操作
→ JavaScript event listener
→ fetch Flask API
→ Flask 查詢／修改 MySQL
→ JSON response
→ JavaScript 更新畫面
```

例如 JavaScript 共用的 API 請求函式會關閉瀏覽器快取並檢查 HTTP status：

```javascript
async function fetchJson(url, options = {}) {
    const response = await fetch(url, {
        cache: "no-store",
        ...options,
    });

    if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
    }

    return response.json();
}
```

`cache: "no-store"` 可避免 Pipeline 完成後瀏覽器仍顯示舊 API response。

## 上台銜接講法（約 15 秒）

> 接下來我會切換到實際 Dashboard，依序示範新聞搜尋、自選公司、市場資料，以及完整 Pipeline 的更新入口。這些操作都會經過剛才介紹的 JavaScript、Flask API 和 MySQL。

---

# 實機操作流程（約 3 分 30 秒）

## Demo 1：Latest News（約 50 秒）

### 操作

1. 捲動到 Latest News。
2. 在搜尋框輸入一間公司名稱。
3. 示範來源或公司篩選。
4. 指出標題、取得來源、publisher、分析分類、公司標籤和發布時間。

### 背後邏輯

- Flask `/api/news` 從 MySQL 讀取資料並加入公司關聯。
- JavaScript 把 JSON 保存到 `newsRecords` array。
- 搜尋、排序與分頁主要在瀏覽器內處理，不會重新查外部新聞網站。
- Dashboard 每個取得來源顯示最新 60 篇平衡樣本；MySQL 仍保存完整歷史資料。

### 建議講法

> 新聞由 Flask API 從 MySQL 載入後，JavaScript 負責目前畫面的搜尋、篩選、排序和分頁，因此操作時不需要重新爬取網站。畫面每個來源保留最新 60 篇，避免大量 TWSE 公告完全壓過媒體新聞，但這個限制只影響 Dashboard 樣本，不會刪除 Database 原始資料。

## Demo 2：My Watchlist（約 50 秒）

### 操作

1. 使用搜尋欄輸入股票代號或公司名稱。
2. 加入或展示已加入的公司。
3. 指出追蹤晨報內與該公司相關的新聞。

### 背後邏輯

- 公司搜尋使用已載入的市場公司清單。
- 加入公司會呼叫 `POST /api/watchlist/<company_id>`。
- 移除公司會呼叫 `DELETE /api/watchlist/<company_id>`。
- Database 保存的是穩定的 `company_id`，不是畫面上的公司名稱文字。
- 個人化晨報使用新聞公司關聯表，找出追蹤公司的近期相關新聞。

### 建議講法

> 追蹤清單保存的是公司 ID，而不是只有畫面文字。這樣即使顯示名稱調整，關聯仍然能維持。系統再利用新聞與公司的中介關聯，找出自選公司的近期文章。這裡的公司辨識是規則式方法，不是 AI 閱讀全文，因此仍可能漏判。

## Demo 3：Company Market Data（約 55 秒）

### 操作

1. 選擇一間有資料的公司。
2. 指出最新交易日、收盤價與價格圖。
3. 指出季度財務摘要。
4. 若畫面有 stale warning，說明預期日期與來源實際日期的差異。

### 背後邏輯

- 公司價格 endpoint 回傳最近 90 筆每日價格。
- 財務摘要 endpoint 回傳最近 8 季資料。
- Chart.js 把 JSON 數列轉成折線圖。
- Pipeline 會比較「預期最近交易日」和「Database 實際最新日期」，並回補近期缺漏平日。

### 建議講法

> 這裡的資料來自 TWSE 盤後與財務資料，不是即時報價。後端會保存每日交易資料並檢查最新交易日；若官方快照尚未更新，畫面會提示資料延遲，而不是把 API 成功誤稱為行情已經最新。價格圖只提供歷史觀察，不構成投資建議。

## Demo 4：Pipeline（約 55 秒）

### 操作

1. 捲動到 Pipeline 執行區。
2. 指出「立即更新資料」按鈕。
3. 展示最近一次成功紀錄、總耗時與九個步驟。
4. 現場可按下更新，但不必等待所有外部來源完成。

### 背後邏輯

- 按鈕呼叫 `POST /api/pipeline/run`。
- API 成功啟動時回傳 HTTP `202 Accepted`。
- 已有 Pipeline 執行時回傳 `409 Conflict`，避免重複工作。
- 前端輪詢 `/api/pipeline/status`；完成後重新載入 Dashboard API。
- Pipeline 的詳細歷史另外保存在 MySQL，重新啟動 Flask 後仍可查詢。

### 建議講法

> 這個按鈕啟動的就是和 Terminal 相同的九步 Pipeline。API 會先回應已接受工作，JavaScript 再定期查詢狀態。若已經有一個 Pipeline 在執行，後端會拒絕第二次啟動。現場外部網站可能需要時間，所以我主要用最近一次成功紀錄展示每一步的結果與耗時。

## Demo 失敗備案

### Dashboard 無法開啟

> 目前本機服務沒有成功連線，因此我改用簡報中的流程與歷史畫面說明。這也反映本專案仍是本機開發版本，需要 Flask 和 MySQL 同時運作。

### 單一新聞來源 timeout

> 外部網站可能暫時逾時。共用 HTTP client 最多嘗試三次，每次失敗會寫入 log；若最後仍失敗，該來源會標記異常，但其他成功來源仍可繼續進入 Pipeline。

共用 retry 的核心在 `src/http_client.py`：

```python
for attempt in range(1, max_attempts + 1):
    try:
        response = requests.get(url, timeout=timeout)
        response.raise_for_status()
        return response.text
    except requests.RequestException:
        if attempt == max_attempts:
            raise
        time.sleep(retry_delay)
```

### 市場資料日期不是今天

> 股市只有交易日才有資料，而且官方盤後資料也可能延遲。系統會顯示來源實際最新交易日、警告延遲並嘗試回補近期缺漏，但不會自行捏造不存在的日期。

---

# 第 10 頁｜從單一爬蟲發展成完整系統

## 理解重點

專案不是一次完成，而是透過 Git commits 把不同責任逐步拆開。幾個關鍵演進如下：

| 演進階段 | 代表性修改 | 架構上的意義 |
|---|---|---|
| 單一來源 | 第一個 TechNews crawler | 驗證 Requests + BeautifulSoup 能取得資料 |
| 共同格式 | 多來源 News Record | 將來源差異與後續流程分離 |
| 資料品質 | canonical URL、正式欄位、Migration | 讓 Database 可追溯並防止重複 |
| 統一更新 | `run_pipeline.py` | 用固定順序串起資料工作 |
| 動態 Dashboard | Flask API | 從靜態 JSON 進化為即時查詢 MySQL |
| 公司與市場 | 公司目錄、價格、財務、關聯 | 從新聞閱讀擴充成公司觀察工具 |
| 個人化 | Watchlist、晨報 | 讓使用者聚焦自己關心的公司 |
| 收斂修正 | 來源平衡、價格回補、事件資料 | 針對真實資料問題改善可靠性 |

## 為什麼 Git commit 在這裡重要

每個 feature 對應一個 commit，可以保留：

- 當時要解決的問題。
- 修改了哪些檔案。
- 測試是否通過。
- 如果新版本出錯，可以比較前後差異。

Database Schema 變更則使用 Migration，讓不同電腦可以依序把舊資料庫升級到目前結構，而不是手動猜測要新增哪些欄位。

## 上台建議講法（約 65 秒）

> 這個專案最早只有 TechNews 爬蟲，後來先建立共同新聞格式，才有辦法安全加入其他來源。接著加入 URL 去重、Database Migration 和統一 Pipeline，再由 Flask API 讓 Dashboard 直接讀取 MySQL。最後才加入公司、市場、自選股與晨報。這個過程讓我理解，功能增加之前通常要先整理資料格式和模組責任；Git commit 則保留每一次問題、設計與驗證結果。

---

# 第 11 頁｜幾次關鍵問題與修正

## 案例一：公司短名稱造成誤判

### 問題

「中華電攜手 Nokia」曾同時被判定與「華電」、「中華」和「中華電」相關。原因是這些公司別名存在包含與重疊關係，單純使用 `if alias in title` 會把短字串全部命中。

### 修正

Commit：`8e479b4 fix: prevent overlapping company alias matches`

- 優先接受較完整、較長的公司名稱。
- 已命中的文字範圍不再重複分配給其他公司。
- 股票代號與公司別名先整理成可重用的 matching context。

### 學習重點

字串「有出現」不等於語意「真的相關」。規則式 NLP 必須處理邊界、重疊與優先順序。

## 案例二：Step 3/9 公司關聯過慢

### 問題

每篇新聞都重新整理一次上千間公司的名稱、別名和股票代號，造成大量重複計算。

### 修正

Commit：`ff09d4a perf: reuse prepared company matching context`

將公司規則先準備一次，再重複提供給所有新聞使用。同規模基準由約 **6.031 秒降至 0.134 秒**，約提升 **45 倍**。

### 學習重點

效能問題不一定要靠進階演算法；先找出迴圈內不必要的重複工作，常能得到最大改善。

## 案例三：TWSE 公告壓過其他來源

### 問題

TWSE 一次可能有數百筆重大訊息，若全部直接顯示，來源統計和新聞列表會幾乎只剩 TWSE。

### 修正

Commit：`4d96744 feat: balance latest 60 news per source`

`src/read_news.py` 會針對每個 `source` 依時間排序並取最新 60 篇：

```python
for source in prepared_dataframe["source"].dropna().unique():
    source_dataframe = prepared_dataframe.loc[
        prepared_dataframe["source"] == source
    ]
    source_dataframe = source_dataframe.sort_values(
        by="publish_time",
        ascending=False,
    ).head(per_source_limit)
```

這是顯示層取樣，MySQL 不刪除完整新聞。

### 學習重點

「保存多少資料」和「畫面顯示多少資料」是兩個不同決策。分析樣本需要平衡，但原始資料仍應保留。

## 案例四：官方快照成功，但缺少交易日

### 問題

API request 成功只代表伺服器有回應，不代表資料內容已更新到預期交易日。只保存最新快照會讓延遲當天永久形成缺口。

### 修正

Commit：`48f47af fix: backfill missing TWSE daily market prices`

- 比較 Database 已有日期與預期交易日。
- 檢查近期 14 個日曆日內缺少的平日。
- 嘗試使用指定日期資料回補。
- 週末、休市日或官方尚無資料時安全略過。

### 學習重點

HTTP 成功、資料格式正確與業務資料新鮮，是三種不同層次的成功條件。

## 上台建議講法（約 90 秒，只挑三例）

> 開發後期主要不是一直加功能，而是用真實資料找錯誤。第一個例子是「中華電」曾同時比對到華電和中華，後來改成完整名稱優先並排除重疊範圍。第二個是公司關聯步驟每篇新聞都重建一次公司規則，改成只準備一次後，同規模測試從約 6 秒降到 0.134 秒。第三個是 TWSE 公告數量過多，所以 Dashboard 改成每個來源顯示最新 60 篇，但 MySQL 仍保留完整資料。這些案例讓我理解正確性、效能與顯示策略是不同問題。

---

# 第 12 頁｜目前限制

## 理解重點

| 目前限制 | 技術原因 | 使用時應如何解讀 |
|---|---|---|
| 只有五個新聞／公告取得來源 | 每個來源都需 Adapter、測試與維護 | 不代表涵蓋所有公司消息 |
| 主要是 TWSE 上市公司 | 公司目錄與市場 API 以 TWSE 為主 | 上櫃、海外公司資料可能不足 |
| 沒有文章全文分析 | 目前主要保存標題與來源欄位 | 晨報與關聯可能缺少內文語意 |
| 公司辨識是規則式 | 使用名稱、別名、代號和重疊規則 | 仍可能漏判、誤判或遇到同名詞 |
| 關鍵字不是生成式 AI | jieba 斷詞後以 Pandas 計數 | 高頻詞不一定等於重要投資事件 |
| 晨報是規則式摘要 | 對結構化欄位與時間窗整理 | 不是模型閱讀全文後生成的摘要 |
| 股價不是即時行情 | 使用 TWSE 盤後資料 | 不能用於即時交易決策 |
| Event Observation 不代表因果 | 只比較新聞附近的價格時間變化 | 不能宣稱新聞造成漲跌 |
| Watchlist 是本機單一使用者 | 沒有帳號、登入與權限模型 | 不適合直接做多人公開服務 |
| Flask 是開發型部署 | 沒有完整 HTTPS、rate limit、production server | 不應直接暴露到公開 Internet |

## Event Observation 應如何解讀

假設一則新聞發布後股價上漲，也可能同時受到大盤、產業、財報、匯率或其他新聞影響。Morning Alpha 只能說「新聞事件附近觀察到價格變化」，不能說「新聞造成價格上漲」。

這也是程式 API 明確使用 `event-market-observations` 與 methodology／limitations，而不命名成 prediction 的原因。

## 設計態度

清楚標示限制不是否定專案，而是區分：

- 系統實際做了什麼。
- 資料能支持什麼結論。
- 哪些結論目前沒有足夠證據。

## 上台建議講法（約 70 秒）

> 目前專案仍有清楚的界線。新聞來源只有五個，主要涵蓋 TWSE 上市公司，也沒有分析文章全文。公司辨識、事件分組和晨報都是規則式方法，因此可能誤判或漏判。市場價格是盤後資料，不是即時行情；新聞附近的價格變化只能表示時間上的關聯，不能證明因果。專案目前適合本機學習和個人研究，尚未具備帳號、安全和正式部署能力，因此不能視為正式投資平台。

---

# 第 13 頁｜未來發展方向

## 理解重點：優先順序比功能數量重要

### 短期：先提升資料可信度

- 增加來源 fixture 與結構異常測試。
- 改善公司別名、同名詞與跨來源事件辨識。
- 擴充上櫃公司與更多可靠官方資料來源。
- 加入資料品質指標，例如來源涵蓋率與缺漏率。

### 中期：改善分析與個人化

- 在合法範圍內取得文章摘要或全文，再做更可靠的語意分析。
- 讓使用者設定自選公司、產業與關鍵字。
- 提供 Email 或通訊軟體的排程晨報。
- 將事件觀察加入大盤與產業基準，避免只看單一股票漲跌。

### 長期：成為多人服務

- 帳號、登入、權限與每人獨立 Watchlist。
- 正式工作佇列與 scheduler，取代單機 subprocess 狀態。
- Production server、HTTPS、rate limit、監控與備份。
- 進行模型評估後，才考慮 AI 摘要或事件分類。

## 設計原因

下一步不應只追求「再加一個功能」。資料品質若不足，加入更複雜的 AI 或預測只會放大錯誤。比較合理的順序是：

```text
資料完整性
→ 關聯正確性
→ 分析方法
→ 個人化
→ 多人部署與安全
```

## 上台建議講法（約 55 秒）

> 未來短期會優先改善來源涵蓋率、公司辨識與資料品質，而不是立刻加入股價預測。中期可以在合法取得更多文字內容後，改善語意分析與個人化晨報；事件分析也應加入大盤和產業基準。若要發展成公開服務，長期還需要帳號權限、背景工作佇列、HTTPS、監控和備份。我認為這個專案目前最重要的成果，是完成從資料取得、整理、保存，到 API 和網頁呈現的完整流程。以上是我的報告。

---

# 報告時最值得說清楚的三個技術觀念

## 1. Pipeline 和 Flask API 不一樣

- **Pipeline**：負責連接外部來源並更新 Database，是較慢的批次工作。
- **Flask API**：負責接收瀏覽器 request、查詢現有 Database 並快速回傳 JSON。
- **Dashboard**：呼叫 API 並顯示資料，不直接存取 MySQL。

一句話版本：

> Pipeline 負責把新資料搬進來，Flask API 負責把已保存的資料提供出去。

## 2. Pandas 和 MySQL 不一樣

- **Pandas** 適合一次處理一批記憶體中的表格資料，例如轉日期、排序、分組與統計。
- **MySQL** 適合永久保存資料、建立關聯、使用 UNIQUE constraint 與支援多次查詢。

一句話版本：

> Pandas 是資料加工桌，MySQL 是有規則、可長期保存的資料倉庫。

## 3. JSON 是交換格式，不是整個 Database

Flask 使用 JSON 把 Python 資料傳給 JavaScript。JSON 適合前後端交換，但目前主要真實資料仍保存在 MySQL。Pipeline 產生的 `news.json`、`chart_data.json` 和 `keyword.json` 是相容與匯出結果，不應和 Database 的完整歷史資料混為一談。

一句話版本：

> MySQL 負責保存，JSON 負責傳遞或匯出，JavaScript 負責顯示。

---

# 老師可能提問與回答

## 為什麼使用 Pandas？

多個 Adapter 產生共同欄位後，Pandas 很適合把 `list[dict]` 轉成 DataFrame，批次處理日期轉換、排序、分組和關鍵字統計。Pandas 不是永久儲存工具，所以整理完成後仍交給 MySQL。

## 為什麼需要 Flask API？

瀏覽器不應直接取得 MySQL 帳密或執行 SQL。Flask 位在中間，負責驗證 request、查詢 Database、將 Python 資料轉成 JSON，並用 HTTP status 告訴前端成功或失敗。

## Flask 在這個專案中算什麼？

它同時負責兩件事：第一，提供 Dashboard 的 HTML/CSS/JavaScript 靜態檔案；第二，提供 `/api/news`、`/api/watchlist`、`/api/pipeline/run` 等資料與操作 endpoints。它是前端和 MySQL／Pipeline 之間的後端介面。

## 為什麼不用標題去重？

相同標題可能是不同媒體的獨立文章，略有不同的標題也可能是同一篇文章。完全相同文章使用 canonical URL 與來源文章 ID 去重；不同文章但同事件則保留並分組。

## 為什麼還保留 JSON 檔案，Dashboard 不是已經使用 API 嗎？

目前 Dashboard 的主要動態資料來自 Flask API；Pipeline 仍匯出幾個 JSON，作為舊流程相容、離線檢查與可讀的分析產物。它們不是 MySQL 的完整替代品。

## `source` 和 `publisher` 有什麼不同？

`source` 是 Morning Alpha 實際取得資料的管道，例如 Yahoo RSS；`publisher` 是文章原始發布者，例如中央社。直接來源通常兩者相同，聚合來源則可能不同。

## 為什麼需要 Adapter？

Adapter 把外部來源的特殊格式轉成共同 News Record。網站變動時主要修改對應 Adapter；後面的 Pandas、MySQL、API 和 Dashboard 不需要一起改。

## 如果網站結構改變會怎樣？

Adapter 可能解析不到文章，因此程式會把空結果視為來源失敗，保存來源健康狀態並寫入 log。Fixture tests 使用固定 HTML、RSS 或 JSON 樣本檢查正常與異常結構，但真實網站改版後仍需要更新 Adapter。

## 為什麼 retry 最多三次？

短暫 timeout 可能下一次就恢復，所以 retry 能提高成功率；但無限重試會讓 Pipeline 永遠卡住。三次是在容錯與執行時間之間的簡單折衷。

## 為什麼選擇 MySQL？

新聞、公司、股票代號、公司別名、價格、財務資料和 Watchlist 彼此有明確關聯。關聯式 Database 可以使用 primary key、foreign key、JOIN、index 和 UNIQUE constraint 管理一致性。

## 為什麼 Dashboard 每個來源最多 60 篇？

TWSE 公告數量遠高於媒體新聞，若完全混合，畫面與統計會失去來源平衡。系統針對每個取得來源顯示發布時間最新 60 篇；MySQL 仍保存所有原始紀錄。

## 關鍵字分析有使用 AI 嗎？

沒有使用生成式 AI。系統先用 jieba 對中文標題斷詞，再用 Pandas 計算詞頻並取 Top 20。它是統計結果，不代表系統理解文章完整語意。

## 公司新聞關聯如何建立？

系統使用公司正式名稱、別名與股票代號比對標題，並處理短名稱重疊。這種方法容易理解與測試，但仍可能漏掉沒有直接寫出公司名稱的文章。

## Morning Alpha 可以預測股價嗎？

目前不能。Event Observation 只把新聞時間附近的歷史價格放在一起觀察，沒有控制大盤、產業、財報與其他事件，因此不能宣稱因果，也不能當成交易訊號。

## 為什麼股價資料可能不是今天？

週末和休市日沒有交易資料，官方盤後資料也可能延遲。系統會比較預期最近交易日與實際最新日期、顯示 stale warning，並嘗試回補近期缺漏平日。

## 為什麼 Pipeline 要用 subprocess？

完整更新可能要數秒或更久。若讓一個 HTTP request 一直等待，瀏覽器容易 timeout。Flask 因此啟動背景 subprocess，先回覆 `202 Accepted`，前端再定期查詢狀態。

## Docker 是不是唯一執行方式？

不是。專案可以使用本機 virtual environment、MySQL 和 `python3 start.py` 執行；Docker Compose 是另一種把 Python、套件與 MySQL 環境一起封裝的選項，主要幫助不同電腦重現環境。

## 其他人能不能直接使用？

可以 clone 後依 README 設定 Python、MySQL、Migration 和 `.env`，也可選擇 Docker。但目前是本機單一使用者架構，沒有登入、權限、HTTPS 和 production server，不適合直接公開到 Internet。

---

# 初學者名詞速查

| 名詞 | 在本專案中的白話意思 |
|---|---|
| Crawler | 主動下載並解析外部網站資料的程式 |
| Adapter | 把某個來源的特殊格式翻成共同格式的模組 |
| Data contract | 模組間約定好的欄位、型態與必要規則 |
| DataFrame | Pandas 提供的記憶體表格結構 |
| Schema | Database 有哪些 tables、columns、types 和 constraints |
| Migration | 依版本修改既有 Database Schema 的 SQL |
| Primary key | 唯一識別一筆資料的 key，例如 `company_id` |
| Foreign key | 指向另一張 table 資料的欄位 |
| UNIQUE constraint | 阻止某個值或欄位組合重複的 Database 規則 |
| Canonical URL | 移除不必要差異後，用來代表文章身分的標準網址 |
| API endpoint | 後端提供的一個 HTTP 路徑，例如 `/api/news` |
| JSON | 前後端交換結構化資料的文字格式 |
| HTTP status | API 回覆結果，例如 200、202、409、500 |
| Subprocess | 由目前 Python 程式另外啟動的一個作業系統程序 |
| Logging | 以不同等級保存程式執行與錯誤資訊 |
| Fixture | 測試使用的固定 HTML、RSS 或 JSON 樣本 |
| Graceful degradation | 一個來源失敗時，讓其他可用功能繼續運作 |
| Backfill | 回頭補齊先前缺少的歷史資料 |
| Correlation | 兩件事同時或先後發生的關聯，不等於因果 |

---

# 最後濃縮：如果只能記住整個專案的六句話

1. Morning Alpha 把分散的科技、財經、公司公告與市場資料整理到同一個 Dashboard。
2. HTML、RSS 與 JSON 由不同 Adapter 解析，但最後都轉成共同 News Record。
3. Pandas 負責批次整理，MySQL 負責永久保存與資料一致性。
4. Pipeline 負責更新資料，Flask API 負責把已保存資料提供給 JavaScript。
5. 相同文章用 URL／文章 ID 去重，同一事件的不同報導只分組、不刪除。
6. 目前的公司關聯、晨報與事件觀察是規則式輔助工具，不是 AI 投資預測。
