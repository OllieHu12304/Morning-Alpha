# Morning Alpha 期中報告理解講義與演講草稿

> 適用版本：Morning Alpha v0.3.2 之後的目前版本
>
> 文件定位：先理解專案，再從中整理成 15 分鐘內的口頭報告
>
> 建議分配：簡報約 9 分 30 秒、實機操作約 3 分 30 秒、切換與緩衝約 2 分鐘

## 這次改版的重點

新版簡報由 13 頁收斂成 10 頁，合併原本重複的功能、資料流、Pipeline、專案演進、限制與展望內容。技術說明以初學者能掌握的核心邏輯為主：

- 第 3 頁把「能做什麼、技術棧、資料流」整合成一張圖。
- 第 5 頁用實際例子解釋 Adapter 與「解耦」。
- 第 6 頁用白話區分「同一篇文章」與「同一件事」。
- 第 7 頁把 Pipeline 執行順序與專案演進整合。
- 第 9 頁聚焦三個具代表性的 commits。
- 第 10 頁把目前限制與未來方向放在同一個判斷架構中。

每一頁包含：

- **理解重點**：報告前應真正弄懂的內容。
- **程式對照**：repository 中負責此功能的檔案或精簡程式。
- **設計原因**：為什麼採用這個做法。
- **上台建議講法**：可以再濃縮成口語報告的版本。

---

## 報告前準備

1. 在 repository 根目錄啟動 Morning Alpha：

   ```bash
   python3 start.py
   ```

2. 確認 `http://127.0.0.1:5050` 可以顯示 Dashboard。
3. 預先執行一次 Pipeline，避免現場等待外部網站下載。
4. 在 My Watchlist 保留兩間有新聞與市場資料的公司。
5. 預先確認 Company Market Data 可以搜尋並快速切換追蹤公司。
6. 另開 Terminal，保留最近一次成功 Pipeline 的輸出。
7. 關閉 `.env` 或任何可能顯示密碼的畫面。

---

# 第 1 頁｜Morning Alpha

## 理解重點

Morning Alpha 是一個小型資料產品，不只是爬蟲，也不只是網頁。它把分散的科技新聞、財經新聞、公司公告、價格與財務資料整理到同一個 Dashboard。

```text
Morning Alpha
＝ 資料收集
＋ 資料整理
＋ MySQL 保存
＋ Flask API
＋ Dashboard 呈現
```

專案的主要價值是減少使用者在不同網站之間搜尋、整理和比對資訊的時間。目前定位是個人資訊整理與學習工具，不是自動投資決策系統。

## 上台建議講法（約 30 秒）

> 大家好，我的專案叫做 Morning Alpha。它會收集不同來源的科技、財經新聞、公司公告和市場資料，整理後保存到 MySQL，再透過 Flask API 顯示在 Dashboard。它的目的不是預測股票，而是把原本分散的資訊整理成一個可以搜尋、追蹤和觀察的入口。   

---

# 第 2 頁｜資訊很多，但彼此分散

## 理解重點

使用者真正遇到的不只是「新聞太多」，而是資料散落在不同網站，格式也不相同：

- 今天有哪些重要科技與財經新聞？
- 這則新聞可能與哪間上市公司有關？
- 公司近期新聞、股價與財務資料在哪裡？
- 不同媒體是不是正在報導同一件事情？
- 如何只追蹤自己真正關心的公司？

Morning Alpha 將新聞網站、RSS、公司公告、股價與財務摘要集中到一個 Dashboard，讓使用者不必自行維護多個網站與資料格式。

## 設計原因

專案不是要取代所有原始網站，而是建立一個「索引與整理層」。使用者仍能點回原始文章，但搜尋、篩選與公司關聯先由 Morning Alpha 完成。

## 上台建議講法（約 45 秒）

> 我一開始觀察到，科技新聞、財經 RSS、證交所公告和市場資料分散在不同地方。使用者不只要一直切換網站，還要自行判斷新聞和公司之間的關係。因此 Morning Alpha 的核心問題不是單純爬更多新聞，而是把不同資料整理成相同格式，再提供一個可以一鍵搜尋、追蹤和整理的統一入口。

---

# 第 3 頁｜使用者任務背後，是一條完整技術鏈

## 本頁圖形化內容

簡報以六個相連步驟呈現主要技術棧：

```text
外部來源
HTML／RSS／JSON
    ↓
Python 解析
Requests／BeautifulSoup
    ↓
資料整理
Pandas／jieba
    ↓
永久保存
MySQL／PyMySQL
    ↓
後端服務
Flask API／JSON
    ↓
互動介面
HTML／CSS／JavaScript／Chart.js
```

圖下方再放置使用者能完成的任務：

```text
閱讀新聞｜搜尋篩選｜追蹤公司｜查看市場資料｜一鍵更新
```

## 理解重點：每項技術各自負責什麼

| 技術 | 在 Morning Alpha 的角色 |
|---|---|
| Python | 串起 crawler、資料整理、Database 與 Pipeline |
| Requests | 向外部網站發出 HTTP request |
| BeautifulSoup | 從 TechNews HTML 找出文章資訊 |
| RSS/XML parser | 讀取中央社、自由時報與 Yahoo feed |
| Pandas | 轉換時間、排序、分組與統計資料 |
| jieba | 對中文新聞標題進行斷詞 |
| MySQL | 永久保存新聞、公司、價格、關聯與執行紀錄 |
| PyMySQL | 讓 Python 執行 MySQL SQL |
| Flask | 提供 Dashboard 頁面與 JSON API |
| HTML/CSS | 建立頁面結構與視覺樣式 |
| JavaScript | 呼叫 API、搜尋、切換公司與更新畫面 |
| Chart.js | 把統計與價格資料畫成圖表 |

## 完整資料型態如何變化

```text
HTTP response
→ list[dict]
→ Pandas DataFrame
→ MySQL rows
→ Flask JSON response
→ JavaScript Array/Object
→ Dashboard
```

## 程式對照

Pandas 將文字時間轉成可排序的時間型態：

```python
dataframe["publish_time"] = pd.to_datetime(
    dataframe["publish_time"],
    errors="coerce",
)
```

Flask 從 MySQL 讀取資料並回傳 JSON：

```python
@app.get("/api/news")
def news():
    dataframe = load_all_news()
    company_links = load_news_company_links()
    return jsonify(build_news_payload(dataframe, company_links))
```

JavaScript 再呼叫 API 並更新畫面：

```javascript
const payload = await fetchJson("/api/news");
newsRecords = payload.news;
renderTable();
```

## 重要區分

- **Pipeline** 負責把新資料搬進 MySQL。
- **Flask API** 負責把已保存的資料提供給 Dashboard。
- **JavaScript 搜尋**只篩選已載入資料，不會每輸入一次就重新爬網站。

## 上台建議講法（約 90 秒）

> 使用者看到的是一個 Dashboard，但背後其實是一條技術鏈。Requests 先下載 HTML、RSS 或 JSON；BeautifulSoup 或 parser 負責解析；Pandas 將多筆資料整理成 DataFrame；PyMySQL 再把資料寫進 MySQL。使用者打開網頁時，Flask API 從 MySQL 查詢並回傳 JSON，最後由 JavaScript 和 Chart.js 顯示成表格與圖表。每項技術不是各自獨立，而是接力處理同一筆資料。Pipeline 負責更新資料，API 負責提供資料，前端則負責互動。

---

# 第 4 頁｜五個新聞管道，三種資料格式

## 理解重點

| 來源 | 資料內容 | 格式 | 解析方式 |
|---|---|---|---|
| TechNews | 科技新聞 | HTML | Requests + BeautifulSoup |
| 中央社財經 | 財經新聞 | RSS/XML | XML parser |
| 自由時報財經 | 財經新聞 | RSS/XML | XML parser |
| Yahoo 股市 | 聚合型台股新聞 | RSS/XML | XML parser |
| TWSE | 重大訊息、公司、價格與財務 | JSON API | Python dict/list |

三種方法不是刻意增加複雜度，而是來源本身提供不同介面：

- **HTML** 是給人閱讀的網頁，需要找出 DOM 標籤與 class。
- **RSS/XML** 是給程式訂閱內容的 feed，通常已有標題、網址與時間。
- **JSON API** 是給程式交換資料的格式，可直接轉成 Python `dict` 和 `list`。

## 程式對照

`src/news_sources.py` 集中管理所有來源：

```python
source_fetchers = [
    ("technews", "TechNews", fetch_technews),
    ("cna", "中央社財經 RSS", fetch_cna_finance),
    ("ltn", "自由時報財經 RSS", fetch_ltn_business),
    ("yahoo_tw_finance", "Yahoo股市 RSS", fetch_yahoo_finance),
    ("twse_disclosure", "TWSE 重大訊息", fetch_twse_disclosures),
]
```

如果單一來源失敗，程式會記錄錯誤並繼續其他來源。這稱為 graceful degradation：部分外部服務異常時，整個系統不必完全停止。

## 上台建議講法（約 65 秒）

> 目前共有五個新聞與公告取得管道。TechNews 是一般 HTML，所以使用 BeautifulSoup；中央社、自由時報與 Yahoo 提供 RSS，因此解析 XML；TWSE 提供官方 JSON API，可以直接轉成 Python 字典。三種方法的差異來自來源本身。系統會分開記錄每個來源的成功或失敗，因此其中一個網站 timeout 時，其他來源仍能繼續更新。

---

# 第 5 頁｜Adapter 用「解耦」隔離網站差異

## 先用白話理解解耦

「耦合」代表兩段程式彼此知道太多細節，改動其中一邊時，另一邊也必須跟著修改。

「解耦」則是先約定一個共同介面，讓兩邊只依賴這個約定，不依賴彼此的內部做法。

可以把 Adapter 想成插座轉接頭：

```text
不同規格插頭
HTML／RSS／JSON
       ↓
    Adapter
       ↓
統一規格插座
共同 News Record
```

## 沒有 Adapter 時

假設 Pandas 必須知道每個網站的欄位：

```python
if source == "TechNews":
    title = article["post_title"]
elif source == "Yahoo":
    title = item["title"]
elif source == "TWSE":
    title = record["主旨"]
```

這代表新增或修改來源時，Pandas、MySQL 和後續分析都可能一起被迫修改，耦合很高。

## 使用 Adapter 後

每個 Adapter 自己理解來源格式，但都輸出相同欄位：

```python
return create_news_record(
    source=source,
    publisher=publisher,
    source_article_id=article_id,
    title=title,
    publish_time=publish_time,
    url=url,
)
```

共同 News Record 包含：

```text
source｜publisher｜source_article_id
title｜publish_time｜url｜source_category
```

後面的 Pandas 與 MySQL 只認共同格式，不需要知道資料原本來自 HTML、RSS 還是 JSON。

## 具體例子

如果 TechNews 改變 HTML class：

- 主要修改 `src/technews_adapter.py`。
- `src/analyze_news.py` 不需要知道 HTML 改版。
- `src/store_news.py` 仍然接收相同 News Record。
- Flask API 與 Dashboard 也不需要跟著重寫。

這就是 Adapter 帶來的解耦：**把容易變動的網站細節，限制在一個小範圍內。**

## 設計取捨

- 優點：新增來源時不必重寫整條 Pipeline。
- 優點：每個 Adapter 可使用 fixture 獨立測試。
- 代價：每個來源仍需要自己的解析程式與維護成本。

## 上台建議講法（約 85 秒）

> 接下來想要講一下爬蟲之後進行的解耦的概念，先約定一個共同介面，讓兩邊只依賴這個約定，不依賴彼此的內部做法。也就是不要讓後面的 Pandas、MySQL 知道每個網站的特殊結構。可以把它想成轉接頭：HTML、RSS 和 JSON 是不同插頭，Adapter 把它們轉成統一 News Record。假設 TechNews 改了 HTML class，我只需要修 TechNews Adapter；只要輸出欄位不變，後面的資料整理、Database 和 Dashboard 就不用一起修改。這能把外部網站最容易變動的部分隔離起來。

---

# 第 6 頁｜先判斷是不是同一篇，再決定是否分組

## 白話理解

系統需要分清楚兩種情況：

### 情況一：完全相同的文章

例如同一篇文章因為 Pipeline 執行兩次而再次出現。這種資料不應重複寫入。

系統使用兩個主要線索：

1. 將網址整理成標準形式，再比較 canonical URL。
2. 比較 `source + source_article_id`。

### 情況二：不同媒體報導同一件事

例如中央社與 Yahoo 都報導同一場法說會。雖然事件相同，但它們仍是不同 publisher 的文章，因此應該全部保留，只在 Dashboard 標示為同一事件群組。

## 主要技術邏輯

```text
同一網址或同一來源文章 ID
→ 視為同一篇文章
→ MySQL 不重複寫入

不同網址、不同 publisher，但事件相似
→ 保留每篇文章
→ Dashboard 只做分組
```

MySQL 使用 UNIQUE constraint 最後把關：

```sql
UNIQUE KEY unique_canonical_url_hash (canonical_url_hash),
UNIQUE KEY unique_source_article (source, source_article_id)
```

寫入使用 `INSERT IGNORE`，遇到已存在的唯一資料時不再新增。

## 為什麼不直接比較標題

- 不同媒體可能使用完全相同的標題，但仍是不同文章。
- 同一篇文章也可能稍微修改標題。
- 只看標題容易誤刪或漏掉重複資料。

## 上台建議講法（約 65 秒）

> 由於需要從各種來源爬取同樣都是財經相關新聞的資料，舉凡在相對短讀時間內重複爬取，或是不同媒體報導同一事件，都有可能造成資料的重複。目前專案處理去重的邏輯是：如果網址整理後相同，或來源和文章 ID 相同，MySQL 就不再重複寫入。但如果只是不同媒體在報導同一件事，系統會保留每篇文章，只在 Dashboard 把它們分組。這樣既能避免 Pipeline 重複寫入，又不會因為標題相似而誤刪不同媒體的內容。

---

# 第 7 頁｜從多支程式，整合成一個九步 Pipeline

## 專案演進

Morning Alpha 早期需要分別執行多支 Python scripts。這容易出現兩個問題：

- 使用者必須記住執行順序。
- 少執行一支程式，就可能讓 Dashboard 使用舊資料。

Commit `13e9130 feat: add unified data pipeline runner` 首次建立 `src/run_pipeline.py`，將多項資料工作整合成單一入口：

```bash
python3 src/run_pipeline.py
```

後續功能增加後，Pipeline 發展成目前九個步驟：

| 步驟 | 工作 |
|---|---|
| 1 | 爬取、整理並儲存新聞 |
| 2 | 同步 TWSE 公司資料 |
| 3 | 建立新聞公司關聯 |
| 4 | 同步 TWSE 每日價格 |
| 5 | 同步 TWSE 財務摘要 |
| 6 | 產生並保存每日晨報 |
| 7 | 匯出 Dashboard 新聞 JSON |
| 8 | 產生圖表資料 |
| 9 | 產生 Top 20 關鍵字 |

## Pipeline 的角色

`run_pipeline.py` 是協調者，不是把所有功能重寫在同一個檔案。它依照資料相依順序呼叫現有模組：

```python
collect_and_store_news()
sync_company_data()
run_news_company_sync()
sync_market_prices()
```

這種設計讓每個功能仍能單獨測試，而使用者只需要一個入口。

## 從 Dashboard 啟動

現在使用者還可以按下「立即更新資料」：

```text
JavaScript
→ POST /api/pipeline/run
→ Flask
→ subprocess 啟動 run_pipeline.py
→ 前端輪詢執行狀態
→ 完成後重新載入 Dashboard
```

## 設計原因

- 固定執行順序，避免漏步驟。
- 每一步記錄成功、失敗、耗時與摘要。
- 同一支 `run_pipeline.py` 可由 Terminal 或 Dashboard 執行。
- 各功能仍保留獨立函式與測試。

## 上台建議講法（約 90 秒）

> 專案早期需要手動執行多支 Python scripts，使用者不但要記住順序，也可能漏掉其中一步。Commit 13e9130 首次建立統一的 `run_pipeline.py`。後續功能增加後，目前已經有九個步驟，從新聞、公司、價格、財務到晨報與關鍵字。Pipeline 本身是協調者，它依序呼叫各模組，而不是把所有程式寫在一起。現在同一支 Pipeline 也能由 Dashboard 按鈕透過 Flask 啟動，使用者不必再記指令。

---

# 第 8 頁｜實際操作 Morning Alpha

## Demo 前要理解的流程

```text
使用者操作
→ JavaScript event
→ Flask API
→ MySQL
→ JSON response
→ JavaScript 更新畫面
```

## Demo 1：搜尋與篩選新聞（約 45 秒）

1. 在 Latest News 搜尋一間公司。
2. 切換來源或分類。
3. 指出 publisher、分析分類、公司標籤與發布時間。

講法：

> 新聞由 Flask API 從 MySQL 載入，JavaScript 再處理搜尋、篩選、排序和分頁，因此操作時不會重新爬網站。

## Demo 2：加入 My Watchlist（約 45 秒）

1. 使用公司名稱或股票代號搜尋。
2. 加入一間追蹤公司。
3. 指出個人化近期追蹤新聞。

講法：

> Watchlist 保存的是 `company_id`，再透過新聞公司關聯找到近期文章，不是只保存畫面文字。

## Demo 3：快速切換 Company Market Data（約 55 秒）

1. 在 Company Market Data 搜尋公司。
2. 使用「我的追蹤公司」按鈕快速切換兩間公司。
3. 指出最新交易日、收盤價、趨勢圖與季度摘要。

講法：

> My Watchlist 與市場資料共用同一個 `company_id`。切換按鈕後，JavaScript 會重新呼叫該公司的價格與財務 API。這些是 TWSE 盤後資料，不是即時行情。

## Demo 4：Pipeline 更新入口（約 55 秒）

1. 展示「立即更新資料」按鈕。
2. 指出最近一次成功紀錄與九個步驟。
3. 不必等待完整 Pipeline 現場執行完成。

講法：

> 這個按鈕啟動的就是和 Terminal 相同的 Pipeline。因為外部網站下載時間不固定，我使用最近一次成功紀錄說明每一步的結果與耗時。

## Demo 失敗備案

### 單一來源 timeout

> 共用 HTTP client 最多嘗試三次。最後仍失敗時會記錄來源異常，但其他來源可以繼續。

### 市場資料日期不是今天

> 週末與休市日沒有交易資料，官方盤後資料也可能延遲。系統會顯示實際最新交易日，並嘗試回補近期缺漏，而不會自行製造日期。

---

# 第 9 頁｜三次關鍵修正：更快、更準、更容易使用

## 案例一：`ff09d4a` 公司關聯效率提升

### 問題

Pipeline Step 3 要把新聞標題與上千間公司的名稱、別名和股票代號比對。原本每處理一篇新聞，都重新準備一次相同的公司規則，造成大量重複計算。

### 修正

Commit：[`ff09d4a perf: reuse prepared company matching context`](https://github.com/OllieHu12304/Morning-Alpha/commit/ff09d4a7718bdff799191658cd4a2f91c9e923b2)

```text
修改前：每篇新聞都重新準備公司比對規則
修改後：先準備一次 matching context，再重複使用
```

同規模基準由約 **6.031 秒降至 0.134 秒**，約提升 **45 倍**。

### 學習重點

效能改善不一定要使用艱深演算法。先找出迴圈中沒有必要重複執行的工作，往往就能得到明顯改善。

## 案例二：`36ad56f` 排除不相關新聞

### 問題

中央社財經 RSS 曾出現「今彩 539」等與科技、財經分析目標無關的內容。雖然爬蟲成功取得文章，但「取得成功」不等於「資料符合需求」。

### 修正

Commit：[`36ad56f fix: exclude CNA lottery news`](https://github.com/OllieHu12304/Morning-Alpha/commit/36ad56f4defad8ca9238e98e3805adee37346e6f)

- 在 CNA Adapter 取得資料時先過濾明顯不相關內容。
- 在讀取既有 Database 新聞時再次套用 relevance rule。
- 加入固定 RSS fixture 與測試，避免日後回歸。

```text
原始 RSS
→ 相關性規則
→ 只保留符合 Morning Alpha 目標的新聞
```

### 學習重點

Crawler 的品質不能只看抓到幾篇，也要驗證抓到的內容是不是使用者真正需要的資料。

## 案例三：`13e9130` 整合多支 Python 執行序

### 問題

早期流程需要依序執行不同 scripts。只要漏掉其中一支，Database、JSON 或 Dashboard 就可能不同步。

### 修正

Commit：[`13e9130 feat: add unified data pipeline runner`](https://github.com/OllieHu12304/Morning-Alpha/commit/13e9130a883e142d4ce511cacf9cb45104c15a73)

- 建立單一 `src/run_pipeline.py`。
- 明確定義執行順序。
- 任一步驟失敗時停止並回傳非零 exit code。
- 為 Pipeline orchestration 建立獨立測試。

```text
多支手動 scripts
→ 一個統一入口
→ 固定順序、統一錯誤處理、統一摘要
```

### 學習重點

自動化不只是省下輸入指令的時間，也能減少人為漏步驟與不同資料版本混用。

## 上台建議講法（約 110 秒）

> 我選三個 commits 說明專案如何從問題中改進。第一個是 ff09d4a，公司關聯原本每篇新聞都重建相同規則，改成先準備一次再重用後，基準時間從約 6 秒降到 0.134 秒，提升約 45 倍。第二個是 36ad56f，Crawler 曾抓到今彩 539 這類不相關新聞，因此加入相關性規則、舊資料過濾和 fixture tests。第三個是 13e9130，將原本多支 Python scripts 整合成單一 Pipeline，固定執行順序與錯誤處理。這三次修改分別改善了效能、資料品質與操作可靠性。

---

# 第 10 頁｜先承認限制，再決定下一步

## 目前限制

- 目前只有五個新聞／公告取得來源，主要涵蓋 TWSE 上市公司。
- 晨報、公司辨識、分類與事件分組主要使用標題和規則式方法。
- 尚未合法取得並分析所有文章全文。
- 市場價格是盤後資料，不是即時行情。
- Event Observation 只表示新聞附近的時間關聯，不能證明因果。
- Watchlist 仍是本機單一使用者，沒有登入與權限管理。
- Flask 目前是本機開發服務，尚不是正式公開部署架構。

## 未來方向

### 近期：先提升資料可信度

- 增加可靠合法來源與來源結構測試。
- 改善公司別名、同名詞與跨來源事件辨識。
- 補強歷史市場資料與資料品質指標。

### 中期：再改善個人化

- 增加上櫃與更多市場資料。
- 提供每位使用者獨立 Watchlist。
- 加入 Email 或通訊軟體晨報推播。

### 長期：研究更完整的分析

- 在合法取得內容後研究全文 NLP／AI 摘要。
- 加入大盤與產業基準，改善事件觀察方法。
- 建立正式部署、安全、監控與備份機制。

## 核心原則

```text
資料完整性
→ 關聯正確性
→ 分析方法
→ 個人化
→ 正式部署
```

先確保資料可信，再增加複雜分析，避免錯誤資料被包裝成看似精準的結論。

## 上台建議講法（約 75 秒）

> Morning Alpha 目前仍是資訊整理工具，不是投資預測平台。新聞來源只有五個，公司辨識和晨報主要依賴標題與規則，股價也是盤後資料。新聞附近的價格變化只能表示時間關聯，不能證明因果。未來短期會先改善資料來源、公司辨識和歷史資料品質；中期再發展多使用者與晨報推播；最後才研究全文 NLP、AI 摘要和正式部署。我的核心原則是先讓資料更完整、更準確，再擴大功能。

---

# 老師可能提問與回答

## Pipeline 和 Flask API 有什麼不同？

Pipeline 負責連接外部來源、整理資料並寫入 MySQL，是較慢的批次工作；Flask API 負責快速查詢已保存資料並回傳 JSON。簡單來說：

> Pipeline 把資料搬進來，Flask API 把資料提供出去。

## Adapter 和一般函式有什麼不同？

Adapter 也是以函式或 class 實作，但它的設計目的很明確：把外部來源特殊介面轉換成系統內部共同介面。在這個專案中，每個 Adapter 都輸出相同 News Record，讓後續流程不依賴網站細節。

## 什麼是解耦？

解耦是讓不同模組只透過清楚的介面合作，而不是互相知道所有內部細節。TechNews HTML 改版時只修 Adapter，而不需要一起重寫 Pandas、MySQL 和 Dashboard，就是解耦的效果。

## 為什麼使用 Pandas？

Pandas 適合將多筆 `dict` 轉成 DataFrame，再批次處理日期、排序、分組與統計。永久資料仍交給 MySQL 保存。

## 為什麼需要 Flask API？

瀏覽器不應直接取得 MySQL 帳密或執行 SQL。Flask 位在中間，負責接收 request、查詢 Database、回傳 JSON 並處理錯誤。

## 為什麼不用標題去重？

不同媒體可能使用相同標題，但仍是不同文章；同一篇文章也可能修改標題。因此同一篇文章使用 canonical URL 和來源文章 ID 去重，同事件的不同文章則保留並分組。

## `source` 與 `publisher` 有什麼差異？

`source` 是 Morning Alpha 從哪個管道取得文章，例如 Yahoo RSS；`publisher` 是原始發布者，例如中央社。直接來源通常兩者相同，聚合來源則可能不同。

## 關鍵字分析有使用 AI 嗎？

沒有使用生成式 AI。系統使用 jieba 對中文標題斷詞，再用 Pandas 計算詞頻和 Top 20。

## 公司新聞關聯如何建立？

系統使用公司正式名稱、簡稱、別名與股票代號比對標題，並處理短名稱重疊。它容易理解與測試，但仍可能漏掉沒有直接寫出公司名稱的新聞。

## Morning Alpha 可以預測股價嗎？

目前不能。Event Observation 只把新聞附近的歷史價格放在一起觀察，沒有控制大盤、產業、財報和其他事件，所以不能宣稱因果或當成交易訊號。

## 啟動 Morning Alpha 需要哪些環境？

專案使用本機 Python virtual environment、MySQL 與 `.env`。完成安裝後只要在 repository 根目錄執行 `python3 start.py`，啟動器就會使用 `.venv` 開啟 Flask API 與 Dashboard。

---

# 初學者名詞速查

| 名詞 | 在 Morning Alpha 中的白話意思 |
|---|---|
| Crawler | 下載並解析外部網站資料的程式 |
| Adapter | 把來源特殊格式轉成共同格式的轉接層 |
| Coupling | 模組彼此知道太多細節，修改時容易互相影響 |
| Decoupling | 模組透過共同介面合作，降低互相影響 |
| Data contract | 模組間約定好的欄位、型態和規則 |
| DataFrame | Pandas 提供的記憶體表格 |
| Schema | Database 的 tables、columns、types 與 constraints |
| UNIQUE constraint | 阻止欄位值重複的 Database 規則 |
| Canonical URL | 清除不必要差異後的標準文章網址 |
| API endpoint | 後端提供的 HTTP 路徑，例如 `/api/news` |
| JSON | 前後端交換結構化資料的文字格式 |
| Subprocess | 由目前程式另外啟動的一個作業系統程序 |
| Fixture | 測試使用的固定 HTML、RSS 或 JSON 樣本 |
| Graceful degradation | 單一來源失敗時，其他可用功能仍繼續 |
| Backfill | 回頭補齊先前缺少的歷史資料 |

---

# 最後濃縮：報告時記住這六句話

1. Morning Alpha 把分散的新聞、公司與市場資料整理到同一個 Dashboard。
2. HTML、RSS 與 JSON 由不同 Adapter 轉成共同 News Record。
3. Adapter 將網站細節與後續流程解耦，來源改版時不必重寫整個系統。
4. Pandas 負責整理，MySQL 負責保存，Flask API 負責提供 JSON，JavaScript 負責互動。
5. Pipeline 將多支 Python 工作整合成一個固定順序的更新入口。
6. 目前是規則式資訊整理工具，不是 AI 投資預測平台。
