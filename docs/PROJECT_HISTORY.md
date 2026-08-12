# Morning Alpha 專案更迭歷史

> 從第一個 TechNews crawler 到新聞、公司、市場資料與個人化晨報，記錄 Morning Alpha 每一步為什麼改、如何改，以及可以學到什麼。

| 📦 Commit 數量 | 🗓️ 紀錄範圍 | 🕐 時區 | ↕️ 排列方式 |
|:---:|:---:|:---:|:---:|
| **76** | **2026-08-07 ～ 2026-08-12** | **UTC+8** | **由新到舊** |

## 快速導覽

[**2026-08-12**](#2026-08-12) · [**2026-08-11**](#2026-08-11) · [**2026-08-10**](#2026-08-10) · [**2026-08-08**](#2026-08-08) · [**2026-08-07**](#2026-08-07)

### 變更類型

| 🟢 Feature | 🔴 Fix | 🟣 Performance | 🔵 Documentation | 🟠 Test | ⚙️ Build／CI／Chore | 🏁 Initial |
|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| 新功能 | 問題修正 | 效能改善 | 文件更新 | 測試 | 環境與維護 | 專案起點 |

<sub>點擊每一筆 commit 標題即可展開完整說明；最新一筆預設展開。</sub>

---

## 2026-08-12

<details open>
<summary>🔵 <strong><code>docs: add complete project evolution history</code></strong> · <sub>2026-08-12 11:49:01（UTC+8）</sub></summary>

<br>

<strong>Commit：</strong> [`0662575`](https://github.com/OllieHu12304/Morning-Alpha/commit/06625756d289c72c9872cc662ed4b3ff62ca2097)

根據 Repository 中 75 筆既有 commit 建立完整專案更迭歷史，逐筆整理變更原因、實作方向、精確時間與學習重點。

> 💡 <strong>學習重點：</strong> 將版本紀錄轉化為可閱讀的技術筆記，有助於回顧設計決策並在面試中清楚說明專案成長過程。

</details>

<details>
<summary>🟣 <strong><code>perf: reuse prepared company matching context</code></strong> · <sub>2026-08-12 11:08:52（UTC+8）</sub></summary>

<br>

<strong>Commit：</strong> [`ff09d4a`](https://github.com/OllieHu12304/Morning-Alpha/commit/ff09d4a7718bdff799191658cd4a2f91c9e923b2)

解決 Pipeline `Step 3/9` 過久的問題：將公司名稱、別名與股票代號規則預先整理成共用 context，避免每則新聞重複計算。同規模基準由約 6.031 秒降至 0.134 秒，約提升 45 倍；完整測試為 267 passed、10 skipped。

> 💡 <strong>學習重點：</strong> 將不變資料移到迴圈外預先處理，可以在不犧牲正確性的前提下大幅提升效能。

</details>

<details>
<summary>🟢 <strong><code>feat: add publisher and source article identity</code></strong> · <sub>2026-08-12 10:46:17（UTC+8）</sub></summary>

<br>

<strong>Commit：</strong> [`05f3387`](https://github.com/OllieHu12304/Morning-Alpha/commit/05f3387e26c5a75cf3b1fb5c0491078e39184ff8)

正式區分「擷取來源」與「原始發布者」，並加入來源文章 ID 與 Migration 013，讓不同 adapter 能保存一致的文章身分，Dashboard 也能顯示真正的發布媒體。

> 💡 <strong>學習重點：</strong> 資料來源與內容發布者是不同概念，明確建模能改善追蹤、去重與後續擴充。

</details>

<details>
<summary>🟢 <strong><code>feat: add Liberty Times business RSS source</code></strong> · <sub>2026-08-12 00:22:11（UTC+8）</sub></summary>

<br>

<strong>Commit：</strong> [`b51e784`](https://github.com/OllieHu12304/Morning-Alpha/commit/b51e784f5be5d8f2125ae1cce387ab3c73b20844)

新增自由時報財經 RSS adapter、固定 fixture、異常測試與 Pipeline 整合，擴充財經新聞來源並讓 Dashboard 統計能辨識新來源。

> 💡 <strong>學習重點：</strong> 新增外部來源時應同時建立 adapter、固定測試資料與錯誤處理，避免網站變動直接破壞 Pipeline。

</details>

## 2026-08-11

<details>
<summary>🟢 <strong><code>feat: add layered cross-source article grouping</code></strong> · <sub>2026-08-11 18:24:21（UTC+8）</sub></summary>

<br>

<strong>Commit：</strong> [`9ab2c82`](https://github.com/OllieHu12304/Morning-Alpha/commit/9ab2c8283002886e002d780927ba82687494c1d0)

建立分層式跨來源事件分組：先使用可靠識別資訊，再使用標題相似度判斷相關文章；相似新聞只分組、不刪除原文。

> 💡 <strong>學習重點：</strong> 跨平台去重不應只看標題是否完全相同，且「事件分組」與「刪除重複文章」應分開處理。

</details>

<details>
<summary>🔴 <strong><code>fix: prevent overlapping company alias matches</code></strong> · <sub>2026-08-11 18:19:08（UTC+8）</sub></summary>

<br>

<strong>Commit：</strong> [`8e479b4`](https://github.com/OllieHu12304/Morning-Alpha/commit/8e479b4bb3c0339ab39e44c3e06a36b9d8df7bda)

修正「中華電」同時誤判為華電、中華與中華電的問題；當命中文字位置重疊時，優先保留較長、較明確的公司名稱。

> 💡 <strong>學習重點：</strong> 字串包含比對容易產生部分重疊誤判，需要考慮文字位置、長度與匹配信心。

</details>

<details>
<summary>🟢 <strong><code>feat: add TWSE company disclosures</code></strong> · <sub>2026-08-11 18:02:06（UTC+8）</sub></summary>

<br>

<strong>Commit：</strong> [`822ee75`](https://github.com/OllieHu12304/Morning-Alpha/commit/822ee753264c1a40f4f75446dbb0f941c819d77e)

接入 TWSE 上市公司每日重大訊息，並整合至新聞來源、關鍵字與 Dashboard，讓自選公司除了媒體新聞外也能取得官方揭露資訊。

> 💡 <strong>學習重點：</strong> 官方 Open Data 結構較穩定且可追溯，適合補足一般新聞來源對特定公司的涵蓋不足。

</details>

<details>
<summary>🟢 <strong><code>feat: add searchable company watchlist</code></strong> · <sub>2026-08-11 17:48:29（UTC+8）</sub></summary>

<br>

<strong>Commit：</strong> [`f19dfac`](https://github.com/OllieHu12304/Morning-Alpha/commit/f19dfac22fee15b015e0f8e05bcd89a76e93d365)

將笨重的公司下拉選單改為可搜尋的自選股介面，支援以公司名稱或股票代號尋找並加入追蹤清單。

> 💡 <strong>學習重點：</strong> 當選項數量超過上千筆時，搜尋式選擇器比單純下拉選單更符合實際使用需求。

</details>

<details>
<summary>⚙️ <strong><code>chore: reduce Docker build context</code></strong> · <sub>2026-08-11 17:40:10（UTC+8）</sub></summary>

<br>

<strong>Commit：</strong> [`7e572aa`](https://github.com/OllieHu12304/Morning-Alpha/commit/7e572aab97c6da814cee4c058bb6f86aebe2a033)

擴充 `.dockerignore` 與忽略規則，避免虛擬環境、快取和執行產物被送入 Docker build context，降低重複建置的時間與空間浪費。

> 💡 <strong>學習重點：</strong> Docker image 大小不只取決於 Dockerfile，也受到 build context 中不必要檔案的影響。

</details>

<details>
<summary>🔴 <strong><code>fix: exclude CNA lottery news</code></strong> · <sub>2026-08-11 17:21:24（UTC+8）</sub></summary>

<br>

<strong>Commit：</strong> [`36ad56f`](https://github.com/OllieHu12304/Morning-Alpha/commit/36ad56f4defad8ca9238e98e3805adee37346e6f)

新增新聞相關性規則，排除中央社財經 RSS 中的彩券等非目標內容，避免無關文章污染財經分析與 Dashboard。

> 💡 <strong>學習重點：</strong> 來源名稱是「財經」不代表每篇內容都符合需求，資料進入分析前仍需要品質過濾。

</details>

<details>
<summary>🟢 <strong><code>feat: add personalized watchlist workflow</code></strong> · <sub>2026-08-11 16:05:05（UTC+8）</sub></summary>

<br>

<strong>Commit：</strong> [`0d565c7`](https://github.com/OllieHu12304/Morning-Alpha/commit/0d565c78cf9ed86ecd4cbefa1e23538202fac94b)

建立自選股資料表、API、Dashboard 操作與個人化晨報，讓使用者追蹤公司並查看與其相關的新聞摘要。

> 💡 <strong>學習重點：</strong> 個人化功能需要串起資料庫狀態、API、分析邏輯與前端互動，而不只是新增一個畫面按鈕。

</details>

<details>
<summary>🟢 <strong><code>feat: add event market observations</code></strong> · <sub>2026-08-11 15:46:03（UTC+8）</sub></summary>

<br>

<strong>Commit：</strong> [`3846a70`](https://github.com/OllieHu12304/Morning-Alpha/commit/3846a70d0747c693d221bd1e16b7451194d5ddca)

將新聞事件與市場價格變化放在同一視圖觀察，並在 API 與 Dashboard 中明確標示為規則式觀察與推論限制。

> 💡 <strong>學習重點：</strong> 同時發生不代表因果關係；呈現市場推論時必須揭露資料窗口、方法與限制。

</details>

<details>
<summary>🟢 <strong><code>feat: display company market data on dashboard</code></strong> · <sub>2026-08-11 15:41:36（UTC+8）</sub></summary>

<br>

<strong>Commit：</strong> [`0d6f750`](https://github.com/OllieHu12304/Morning-Alpha/commit/0d6f750adacc6c9dffe2afde5d21d7f95bd1e729)

新增公司市場資料 API 與 Dashboard 區塊，將公司基本資料、價格及財務摘要整合為可查詢的畫面。

> 💡 <strong>學習重點：</strong> 前端顯示前應由後端組合穩定資料格式，避免瀏覽器直接理解多張資料表。

</details>

<details>
<summary>🟢 <strong><code>feat: sync TWSE quarterly financial metrics</code></strong> · <sub>2026-08-11 15:35:00（UTC+8）</sub></summary>

<br>

<strong>Commit：</strong> [`1a414e5`](https://github.com/OllieHu12304/Morning-Alpha/commit/1a414e56bab946ed1ef94a1ae3e6f3a8a67ad16c)

新增 TWSE 季度財務資料 adapter、儲存表、同步程序、fixture 與 Migration 011，保存公司財務摘要。

> 💡 <strong>學習重點：</strong> 財務資料具有期間與指標維度，Schema 必須能表達公司、年度、季度與數值的關係。

</details>

<details>
<summary>🟢 <strong><code>feat: sync TWSE daily market prices</code></strong> · <sub>2026-08-11 15:30:46（UTC+8）</sub></summary>

<br>

<strong>Commit：</strong> [`dadd9a1`](https://github.com/OllieHu12304/Morning-Alpha/commit/dadd9a1a842686b0963c46f87c319eacc677f7cf)

新增 TWSE 每日價格 adapter、資料表、同步程序與 Migration 010，將官方市場價格寫入 MySQL。

> 💡 <strong>學習重點：</strong> 外部市場資料應先轉為專案共同格式，再由獨立儲存層處理資料庫寫入。

</details>

<details>
<summary>🔵 <strong><code>docs: define market data source contracts</code></strong> · <sub>2026-08-11 15:26:37（UTC+8）</sub></summary>

<br>

<strong>Commit：</strong> [`0f93cb4`](https://github.com/OllieHu12304/Morning-Alpha/commit/0f93cb441c56d32e75a7b163bec93b7a41f38ce5)

定義市場與財務資料的共同欄位及來源文件，先確立 adapter 應輸出的資料契約，再開始串接外部資料。

> 💡 <strong>學習重點：</strong> 先定義 data contract 能降低不同來源格式造成的耦合與後續修改成本。

</details>

<details>
<summary>🟢 <strong><code>feat: add company filters to dashboard</code></strong> · <sub>2026-08-11 15:22:40（UTC+8）</sub></summary>

<br>

<strong>Commit：</strong> [`59c41fb`](https://github.com/OllieHu12304/Morning-Alpha/commit/59c41fb01f7f00059835bd7090a45073a41e7870)

將新聞公司關聯接入 API、JSON 匯出與 Dashboard，支援依公司篩選新聞並顯示命中的公司資訊。

> 💡 <strong>學習重點：</strong> 分析結果只有接入使用介面後才真正產生價值，且 API 與離線 JSON 應維持一致欄位。

</details>

<details>
<summary>🟢 <strong><code>feat: store news company relationships</code></strong> · <sub>2026-08-11 15:19:22（UTC+8）</sub></summary>

<br>

<strong>Commit：</strong> [`178689a`](https://github.com/OllieHu12304/Morning-Alpha/commit/178689a6be038c7ee2022ecb4d3a62e579a99942)

新增新聞與公司的多對多關聯表、同步程序及查詢 API，使規則式公司辨識結果可以持久保存與重建。

> 💡 <strong>學習重點：</strong> 一則新聞可關聯多家公司、一家公司也可擁有多則新聞，適合使用關聯表建模。

</details>

<details>
<summary>🟢 <strong><code>feat: match news titles to companies</code></strong> · <sub>2026-08-11 15:16:02（UTC+8）</sub></summary>

<br>

<strong>Commit：</strong> [`4af7af7`](https://github.com/OllieHu12304/Morning-Alpha/commit/4af7af76244ae79da67bda5b0999b66242f674a7)

建立以公司名稱、簡稱、別名與股票代號辨識新聞標題的規則，並回傳比對方法與信心分數。

> 💡 <strong>學習重點：</strong> 可解釋的規則式比對雖不如 NLP 彈性，但容易測試、除錯並說明判斷依據。

</details>

<details>
<summary>🟢 <strong><code>feat: import TWSE company directory</code></strong> · <sub>2026-08-11 15:11:48（UTC+8）</sub></summary>

<br>

<strong>Commit：</strong> [`95c12c3`](https://github.com/OllieHu12304/Morning-Alpha/commit/95c12c34731e99b184eb591458ed625122985b98)

新增 TWSE 公司基本資料 adapter 與同步程式，把上市公司、產業、股票代號及別名匯入公司目錄。

> 💡 <strong>學習重點：</strong> 公司主檔是新聞、股票代號與市場資料之間的共同鍵值，必須先建立可靠的識別資料。

</details>

<details>
<summary>🟢 <strong><code>feat: add company and security data model</code></strong> · <sub>2026-08-11 15:08:03（UTC+8）</sub></summary>

<br>

<strong>Commit：</strong> [`d9aa616`](https://github.com/OllieHu12304/Morning-Alpha/commit/d9aa616536347d03aac6450f38868d7755a2337b)

透過 Migration 008 建立公司、產業、證券與別名資料模型，為公司關聯及市場資料奠定 Schema 基礎。

> 💡 <strong>學習重點：</strong> 將公司與上市證券拆開建模，可以支援一家公司擁有不同市場或代號的情況。

</details>

<details>
<summary>🟢 <strong><code>feat: show daily brief on dashboard</code></strong> · <sub>2026-08-11 15:05:03（UTC+8）</sub></summary>

<br>

<strong>Commit：</strong> [`fec2c0a`](https://github.com/OllieHu12304/Morning-Alpha/commit/fec2c0aefca1ff971240cf35b67940e686467761)

在 Dashboard 顯示每日晨報的摘要、重點、來源、分類、關鍵字及分析限制，並加入前端測試。

> 💡 <strong>學習重點：</strong> 摘要介面不只呈現結論，也應同時揭露資料來源與限制，避免使用者過度解讀。

</details>

<details>
<summary>🟢 <strong><code>feat: add daily brief API</code></strong> · <sub>2026-08-11 14:59:24（UTC+8）</sub></summary>

<br>

<strong>Commit：</strong> [`ee5ed7f`](https://github.com/OllieHu12304/Morning-Alpha/commit/ee5ed7f13858706e1275052c3211916182eff722)

新增每日晨報 API，讓前端可以從 MySQL 讀取指定日期或最新的結構化晨報。

> 💡 <strong>學習重點：</strong> API 是資料庫與前端之間的穩定介面，可以隱藏儲存細節並集中處理錯誤。

</details>

<details>
<summary>🟢 <strong><code>feat: store daily brief history</code></strong> · <sub>2026-08-11 14:57:44（UTC+8）</sub></summary>

<br>

<strong>Commit：</strong> [`37536f5`](https://github.com/OllieHu12304/Morning-Alpha/commit/37536f5cfa6a42c266a17417b894716af6efae9f)

新增每日晨報資料表、儲存層與 Migration 007，讓每日產出的摘要可以保存並回顧歷史版本。

> 💡 <strong>學習重點：</strong> 將計算結果持久化能支援歷史查詢，也避免每次開啟頁面都重新分析。

</details>

<details>
<summary>🟢 <strong><code>feat: generate structured daily brief</code></strong> · <sub>2026-08-11 14:54:52（UTC+8）</sub></summary>

<br>

<strong>Commit：</strong> [`eb3d1d8`](https://github.com/OllieHu12304/Morning-Alpha/commit/eb3d1d807efd8c8c007df14bde749f2c2dbbcb0e)

依新聞標題與既有欄位產生結構化每日晨報，包含重點文章、來源、分類、關鍵字及明確限制。

> 💡 <strong>學習重點：</strong> 結構化摘要比純文字更容易被 API、Dashboard 與後續功能重複利用。

</details>

<details>
<summary>🟢 <strong><code>feat: define daily brief time window</code></strong> · <sub>2026-08-11 14:49:57（UTC+8）</sub></summary>

<br>

<strong>Commit：</strong> [`760a235`](https://github.com/OllieHu12304/Morning-Alpha/commit/760a235ebc11ded0a26bbcf10ca25dca7d2e2abc)

定義每日晨報的固定起訖時間與時區規則，避免同一篇新聞因執行時間不同被歸入不同日期。

> 💡 <strong>學習重點：</strong> 每日批次功能需要明確的業務日與時區定義，不能只依電腦當下時間切割資料。

</details>

<details>
<summary>🔴 <strong><code>fix: standardize source health timestamps as UTC</code></strong> · <sub>2026-08-11 14:38:37（UTC+8）</sub></summary>

<br>

<strong>Commit：</strong> [`e148b02`](https://github.com/OllieHu12304/Morning-Alpha/commit/e148b02e7c10f22c347cf5d2fb5cd4b33d8868e8)

統一來源健康紀錄使用 UTC 儲存與輸出，修正不同環境或時區造成的時間偏移問題。

> 💡 <strong>學習重點：</strong> 後端時間通常應以 UTC 保存，顯示時再轉換成使用者所在地時區。

</details>

<details>
<summary>🔵 <strong><code>docs: close out phase 3 automation</code></strong> · <sub>2026-08-11 12:44:47（UTC+8）</sub></summary>

<br>

<strong>Commit：</strong> [`6716c7d`](https://github.com/OllieHu12304/Morning-Alpha/commit/6716c7dfed0a18837014b05b6cfaef1be57bd6e9)

更新 README 與使用手冊，總結第三階段已完成的環境設定、API、測試、CI、Docker、排程與監控能力。

> 💡 <strong>學習重點：</strong> 階段收斂文件可以讓功能狀態、操作方式與限制保持一致，避免專案資訊分散。

</details>

<details>
<summary>🟢 <strong><code>feat: add history retention and failure alerts</code></strong> · <sub>2026-08-11 12:36:50（UTC+8）</sub></summary>

<br>

<strong>Commit：</strong> [`73415c6`](https://github.com/OllieHu12304/Morning-Alpha/commit/73415c60faf9d909206a6f9b6f2477efd631b003)

新增歷史紀錄保留期限與 Pipeline 失敗通知，可定期清理舊紀錄並透過設定好的管道回報錯誤。

> 💡 <strong>學習重點：</strong> 自動化系統不只要能執行，也要限制資料成長並在失敗時主動通知維護者。

</details>

<details>
<summary>🟢 <strong><code>feat: record pipeline execution history</code></strong> · <sub>2026-08-11 12:22:09（UTC+8）</sub></summary>

<br>

<strong>Commit：</strong> [`bf16066`](https://github.com/OllieHu12304/Morning-Alpha/commit/bf160662bb3668d2bb42d8a6321527567a6fd2dc)

建立 Pipeline 執行歷史表，記錄每個步驟的狀態、耗時、摘要與錯誤，並在 Dashboard 顯示最近執行結果。

> 💡 <strong>學習重點：</strong> 將批次執行結果結構化保存，比只閱讀終端輸出更容易追蹤與除錯。

</details>

<details>
<summary>🟢 <strong><code>feat: show news source health status</code></strong> · <sub>2026-08-11 12:05:36（UTC+8）</sub></summary>

<br>

<strong>Commit：</strong> [`a3def28`](https://github.com/OllieHu12304/Morning-Alpha/commit/a3def28c48ce5dacf5e8b7e675a87cd1061cb63c)

新增來源健康事件、API 與 Dashboard 狀態區，記錄各新聞來源最近嘗試、成功時間、文章數及錯誤。

> 💡 <strong>學習重點：</strong> 多來源爬蟲需要分來源監控，否則整體成功訊息可能掩蓋個別來源長期失效。

</details>

<details>
<summary>⚙️ <strong><code>chore: remove generated runtime artifacts</code></strong> · <sub>2026-08-11 11:51:56（UTC+8）</sub></summary>

<br>

<strong>Commit：</strong> [`b2cc3ab`](https://github.com/OllieHu12304/Morning-Alpha/commit/b2cc3abe0e9fad3adda925a36866ef54959a4e2e)

從 Git 移除 JSON、快取與系統檔等執行產物，並更新忽略規則，避免無關內容持續進入版本歷史。

> 💡 <strong>學習重點：</strong> 原始碼與可重建的執行產物應分開管理，Repository 才會乾淨且容易協作。

</details>

<details>
<summary>🟢 <strong><code>feat: add optional Docker pipeline scheduler</code></strong> · <sub>2026-08-11 11:47:15（UTC+8）</sub></summary>

<br>

<strong>Commit：</strong> [`8d532db`](https://github.com/OllieHu12304/Morning-Alpha/commit/8d532db88ef03716a4ea08bffa54bd2d20f54e80)

加入可選的 Docker Pipeline scheduler，依設定間隔自動更新資料，同時保留手動執行方式。

> 💡 <strong>學習重點：</strong> 排程器應與實際工作程序分開，才能獨立測試執行邏輯與等待週期。

</details>

<details>
<summary>🔵 <strong><code>docs: add Docker quick start guide</code></strong> · <sub>2026-08-11 11:39:28（UTC+8）</sub></summary>

<br>

<strong>Commit：</strong> [`2f570c7`](https://github.com/OllieHu12304/Morning-Alpha/commit/2f570c7c1776adda6aff1be65003c0f630bac177)

在 README 補上 Docker Compose 的環境設定、建置、Migration、Pipeline 與啟動指令，降低新電腦設定門檻。

> 💡 <strong>學習重點：</strong> 可重現環境仍需要清楚的操作文件，Docker 不會自動解決設定順序與使用者理解問題。

</details>

<details>
<summary>🔴 <strong><code>fix: continue pipeline when one news source fails</code></strong> · <sub>2026-08-11 11:36:01（UTC+8）</sub></summary>

<br>

<strong>Commit：</strong> [`268f956`](https://github.com/OllieHu12304/Morning-Alpha/commit/268f9564bf40c78cdd8503764bcc28e5156ae848)

將新聞來源改為彼此隔離執行；單一來源逾時或回傳錯誤時會記錄失敗，但其他成功來源仍可繼續進入 Pipeline。

> 💡 <strong>學習重點：</strong> 多來源系統應採部分成功策略，避免一個外部網站故障拖垮全部資料更新。

</details>

<details>
<summary>⚙️ <strong><code>build: add Docker Compose local environment</code></strong> · <sub>2026-08-11 11:27:34（UTC+8）</sub></summary>

<br>

<strong>Commit：</strong> [`58189d7`](https://github.com/OllieHu12304/Morning-Alpha/commit/58189d7382dd7ad0701ec6812ec30cd40fa094b0)

新增 Dockerfile 與 Compose 設定，把 API 與 MySQL 組成可攜式本機環境，減少不同電腦安裝差異。

> 💡 <strong>學習重點：</strong> Docker image、container 與 volume 分別負責執行環境、程序實例和持久資料，三者用途不同。

</details>

<details>
<summary>⚙️ <strong><code>ci: add Python MySQL and Playwright test workflow</code></strong> · <sub>2026-08-11 10:53:43（UTC+8）</sub></summary>

<br>

<strong>Commit：</strong> [`b98770b`](https://github.com/OllieHu12304/Morning-Alpha/commit/b98770b88d57090ad1bcd9e9206b970a0e3aaa00)

建立 GitHub Actions CI，在推送程式碼後自動執行 Python 單元測試、MySQL integration tests 與 Playwright 前端測試。

> 💡 <strong>學習重點：</strong> CI 能在乾淨環境重複驗證專案，及早發現只在開發者電腦上才能成功的問題。

</details>

<details>
<summary>🟠 <strong><code>test: add dashboard end-to-end tests</code></strong> · <sub>2026-08-11 10:29:21（UTC+8）</sub></summary>

<br>

<strong>Commit：</strong> [`0669c65`](https://github.com/OllieHu12304/Morning-Alpha/commit/0669c653af10af67c882c72d53e60f10f90162a9)

導入 Playwright，以真實瀏覽器測試 Dashboard 載入、搜尋、篩選和主要互動流程。

> 💡 <strong>學習重點：</strong> 單元測試驗證函式，End-to-End test 則驗證使用者從瀏覽器看到的完整流程。

</details>

<details>
<summary>🟠 <strong><code>test: add MySQL integration coverage</code></strong> · <sub>2026-08-11 10:13:33（UTC+8）</sub></summary>

<br>

<strong>Commit：</strong> [`914889d`](https://github.com/OllieHu12304/Morning-Alpha/commit/914889d8c3353dd138a265d652b009a121dd1f22)

新增需連接測試 MySQL 的 integration tests，驗證 Schema、資料寫入、去重與查詢能在真實資料庫共同運作。

> 💡 <strong>學習重點：</strong> Mock 適合隔離單元，但 SQL 欄位、constraint 與 transaction 仍需要真實資料庫測試。

</details>

<details>
<summary>🟢 <strong><code>feat: load dashboard data from API</code></strong> · <sub>2026-08-11 10:09:06（UTC+8）</sub></summary>

<br>

<strong>Commit：</strong> [`15a9af2`](https://github.com/OllieHu12304/Morning-Alpha/commit/15a9af29f9c2e40c41ac69a9af5106aa522cbabb)

將 Dashboard 從手動產生 JSON 改為優先讀取 Flask API，讓頁面直接取得 MySQL 中的新聞與統計資料。

> 💡 <strong>學習重點：</strong> API backend 能讓資料更新與前端顯示解耦，不必每次都人工複製或開啟 JSON。

</details>

<details>
<summary>🟢 <strong><code>feat: add MySQL-backed dashboard API</code></strong> · <sub>2026-08-11 10:03:32（UTC+8）</sub></summary>

<br>

<strong>Commit：</strong> [`daed5ae`](https://github.com/OllieHu12304/Morning-Alpha/commit/daed5ae88cd5453e1c2c05d25f1dba68de520929)

建立 Flask API 與健康檢查，從 MySQL 提供新聞、圖表、關鍵字與 metadata 給 Dashboard 使用。

> 💡 <strong>學習重點：</strong> Web API 將 Python 資料處理能力轉成瀏覽器可使用的 HTTP/JSON 介面。

</details>

<details>
<summary>🟢 <strong><code>feat: load local configuration from dotenv</code></strong> · <sub>2026-08-11 09:28:42（UTC+8）</sub></summary>

<br>

<strong>Commit：</strong> [`6d43c7a`](https://github.com/OllieHu12304/Morning-Alpha/commit/6d43c7a454bcbfceb51d03f8143efe0de7e44088)

導入 `python-dotenv` 與 `.env.example`，讓本機 MySQL 帳密從未追蹤的 `.env` 載入，不需每次手動 export。

> 💡 <strong>學習重點：</strong> 敏感設定不應寫死或提交到 Git；範例檔只描述欄位，不應包含真實密碼。

</details>

<details>
<summary>⚙️ <strong><code>build: pin Python package versions</code></strong> · <sub>2026-08-11 09:17:55（UTC+8）</sub></summary>

<br>

<strong>Commit：</strong> [`86ab5b8`](https://github.com/OllieHu12304/Morning-Alpha/commit/86ab5b8222f496cc89f79ece37c315e134844c06)

在 `requirements.txt` 鎖定 Python package versions，使不同電腦與 CI 能安裝相同依賴版本。

> 💡 <strong>學習重點：</strong> 只寫套件名稱可能因新版相容性改變而失敗；版本鎖定有助於環境重現。

</details>

<details>
<summary>🔵 <strong><code>docs: rewrite README for Morning Alpha v0.2</code></strong> · <sub>2026-08-11 03:03:50（UTC+8）</sub></summary>

<br>

<strong>Commit：</strong> [`2874e2f`](https://github.com/OllieHu12304/Morning-Alpha/commit/2874e2fb3fb41ca1a6043777094294739e978013)

重寫 README，依 v0.2 的實際架構整理功能、安裝、Migration、Pipeline、Dashboard 與限制。

> 💡 <strong>學習重點：</strong> README 應描述目前可執行的版本，而不是仍未完成的原始規劃。

</details>

<details>
<summary>🔴 <strong><code>fix: filter non-finance articles from CNA feed</code></strong> · <sub>2026-08-11 02:59:31（UTC+8）</sub></summary>

<br>

<strong>Commit：</strong> [`89c3ffc`](https://github.com/OllieHu12304/Morning-Alpha/commit/89c3ffc99592fd421726852d8ac077ef7d38dd45)

在中央社 RSS adapter 加入財經相關性篩選，排除來源 Feed 中明顯不屬於目標範圍的文章。

> 💡 <strong>學習重點：</strong> 爬蟲取得資料後仍需建立領域過濾規則，來源本身的分類不能視為絕對正確。

</details>

<details>
<summary>🔴 <strong><code>fix: convert missing source category to MySQL null</code></strong> · <sub>2026-08-11 02:49:05（UTC+8）</sub></summary>

<br>

<strong>Commit：</strong> [`caf090b`](https://github.com/OllieHu12304/Morning-Alpha/commit/caf090b34e809735c8f140e9d3d112529fa14902)

修正 Pandas 缺失值 `NaN` 無法寫入 MySQL 的錯誤，將缺少的來源分類轉成 Python `None`，由資料庫保存為 `NULL`。

> 💡 <strong>學習重點：</strong> Pandas `NaN`、Python `None` 與 SQL `NULL` 意義相近但型別不同，寫入前需要明確轉換。

</details>

<details>
<summary>🔵 <strong><code>docs: update guide for data quality upgrade</code></strong> · <sub>2026-08-11 02:41:06（UTC+8）</sub></summary>

<br>

<strong>Commit：</strong> [`963a0e1`](https://github.com/OllieHu12304/Morning-Alpha/commit/963a0e13518b20332005337ad189839f70931740)

更新 README 與使用手冊，補上多來源、URL 去重、中文斷詞、事件分組及 Migration 的實際操作方式。

> 💡 <strong>學習重點：</strong> 資料模型與執行流程改變時，安裝和操作文件也必須同步更新。

</details>

<details>
<summary>🟢 <strong><code>feat: add safe MySQL migration runner</code></strong> · <sub>2026-08-11 02:36:38（UTC+8）</sub></summary>

<br>

<strong>Commit：</strong> [`feabaa0`](https://github.com/OllieHu12304/Morning-Alpha/commit/feabaa07879e8f9baca624ec68b5643acdd093fa)

新增 Migration runner，依序執行尚未套用的 SQL 並記錄版本，避免使用者手動修改 Schema 或重複執行。

> 💡 <strong>學習重點：</strong> Database Migration 讓 Schema 變更可追蹤、可重現，也能確保不同環境使用相同結構。

</details>

<details>
<summary>🟢 <strong><code>feat: show related news events in dashboard</code></strong> · <sub>2026-08-11 02:33:50（UTC+8）</sub></summary>

<br>

<strong>Commit：</strong> [`35ef837`](https://github.com/OllieHu12304/Morning-Alpha/commit/35ef837da5f7e4e1cc748ab45185e818132d209a)

將事件分組結果接入 Dashboard，讓使用者查看同一事件下的其他相關報導，而不必刪除任何來源文章。

> 💡 <strong>學習重點：</strong> 後端分析結果需要清楚的前端呈現，使用者才能理解「相關」而非「完全重複」。

</details>

<details>
<summary>🟢 <strong><code>feat: group similar news events</code></strong> · <sub>2026-08-11 02:30:18（UTC+8）</sub></summary>

<br>

<strong>Commit：</strong> [`b39efad`](https://github.com/OllieHu12304/Morning-Alpha/commit/b39efad852c12ed0a6f45a9ac1a829128eef0a48)

新增規則式標題相似度分析，把可能描述同一事件的文章分組，同時保留每個來源的原始文章。

> 💡 <strong>學習重點：</strong> 同事件辨識屬於相似度推論，應保存原文並允許結果存在漏判或誤判。

</details>

<details>
<summary>🟢 <strong><code>feat: analyze keywords with Chinese segmentation</code></strong> · <sub>2026-08-11 02:28:32（UTC+8）</sub></summary>

<br>

<strong>Commit：</strong> [`c216efd`](https://github.com/OllieHu12304/Morning-Alpha/commit/c216efd41b5174e2f47642d75143274f89a60b1e)

導入 jieba 中文斷詞與自訂字典，取代固定候選詞庫，讓 Top 20 關鍵字能從新聞標題實際抽取。

> 💡 <strong>學習重點：</strong> 中文沒有天然空格，不能直接用英文式 split；斷詞品質也會受到自訂詞典與停用詞影響。

</details>

<details>
<summary>🟠 <strong><code>test: add fixed crawler fixtures</code></strong> · <sub>2026-08-11 02:24:36（UTC+8）</sub></summary>

<br>

<strong>Commit：</strong> [`b36c6cf`](https://github.com/OllieHu12304/Morning-Alpha/commit/b36c6cfd50e0c218172825aed9e4856744920c7f)

加入固定的 TechNews HTML 與中央社 RSS fixtures，使 crawler tests 不需要每次連線到外部網站。

> 💡 <strong>學習重點：</strong> 固定 fixture 能提供可重現測試，避免網路、即時內容或網站暫時故障造成不穩定結果。

</details>

<details>
<summary>🟢 <strong><code>feat: add crawler retry logging and structure checks</code></strong> · <sub>2026-08-11 02:23:50（UTC+8）</sub></summary>

<br>

<strong>Commit：</strong> [`5d448a9`](https://github.com/OllieHu12304/Morning-Alpha/commit/5d448a9bcf8b90f4abb55d21299c0d4569ab7a69)

新增 HTTP retry、結構化 logging 與來源結構檢查，遇到暫時連線錯誤會重試，網站格式異常則明確回報。

> 💡 <strong>學習重點：</strong> retry 適合處理暫時性網路失敗，但資料結構改變不能無限重試，必須視為需要維護的異常。

</details>

<details>
<summary>🟢 <strong><code>feat: add dashboard search filters and pagination</code></strong> · <sub>2026-08-11 02:21:57（UTC+8）</sub></summary>

<br>

<strong>Commit：</strong> [`d94b9b9`](https://github.com/OllieHu12304/Morning-Alpha/commit/d94b9b9fff483a4720c5384501c109e881833080)

在 Dashboard 加入文字搜尋、來源篩選、分類篩選、排序與分頁，改善新聞數量增加後的瀏覽效率。

> 💡 <strong>學習重點：</strong> 搜尋、篩選與分頁應使用同一份前端狀態重新計算，避免不同操作彼此覆蓋。

</details>

<details>
<summary>🟢 <strong><code>feat: export dashboard news dimensions and metadata</code></strong> · <sub>2026-08-11 02:15:28（UTC+8）</sub></summary>

<br>

<strong>Commit：</strong> [`2073e64`](https://github.com/OllieHu12304/Morning-Alpha/commit/2073e64a47453573e376b4cc892fc97ff8f9b56b)

匯出新聞來源、分類等 Dashboard 維度及 metadata，並加入最後更新時間，讓前端可建立篩選器與更新提示。

> 💡 <strong>學習重點：</strong> 除了主要 records，前端通常還需要 metadata 來解釋資料範圍、維度與產生時間。

</details>

<details>
<summary>🟢 <strong><code>feat: unify keyword analysis rules</code></strong> · <sub>2026-08-11 02:10:50（UTC+8）</sub></summary>

<br>

<strong>Commit：</strong> [`c8c95f6`](https://github.com/OllieHu12304/Morning-Alpha/commit/c8c95f6a915d4310fdfcbae96f70fb1f540d51c7)

統一圖表與 `keyword.json` 的關鍵字計數規則，消除 Top 10 和 Top 20 使用不同候選詞庫而產生的不一致。

> 💡 <strong>學習重點：</strong> 同一指標應由單一分析函式產生，避免多處各自實作後得到互相矛盾的數字。

</details>

<details>
<summary>🟢 <strong><code>feat: add CNA finance RSS source</code></strong> · <sub>2026-08-11 02:02:20（UTC+8）</sub></summary>

<br>

<strong>Commit：</strong> [`83d0a0f`](https://github.com/OllieHu12304/Morning-Alpha/commit/83d0a0f9ac6b0cc16db955523a4adef474f6b6e5)

新增中央社財經 RSS adapter，並建立多來源收集流程，讓 Pipeline 可同時處理 TechNews 與財經新聞。

> 💡 <strong>學習重點：</strong> RSS 是結構化且相對穩定的資料來源，通常比直接解析新聞網站 HTML 更容易維護。

</details>

<details>
<summary>🟢 <strong><code>feat: convert TechNews crawler into adapter</code></strong> · <sub>2026-08-11 02:00:30（UTC+8）</sub></summary>

<br>

<strong>Commit：</strong> [`c653066`](https://github.com/OllieHu12304/Morning-Alpha/commit/c653066b54ca48e355a54da887a6c3cdbde54201)

將原本直接耦合的 TechNews crawler 改為來源 adapter，使來源下載、解析及共同新聞格式彼此分離。

> 💡 <strong>學習重點：</strong> Adapter pattern 能把各網站差異包在獨立模組中，新增來源時不必改寫整條 Pipeline。

</details>

<details>
<summary>🔴 <strong><code>fix: preserve news with duplicate titles</code></strong> · <sub>2026-08-11 01:58:57（UTC+8）</sub></summary>

<br>

<strong>Commit：</strong> [`c4ce188`](https://github.com/OllieHu12304/Morning-Alpha/commit/c4ce1889b3787a94574b834c28fe4d31b9a05aef)

修正 Pandas 整理階段依標題刪除資料的行為，保留標題相同但 URL 或來源不同的文章。

> 💡 <strong>學習重點：</strong> 標題不是可靠的唯一識別值；資料清理規則必須與資料庫的去重策略一致。

</details>

<details>
<summary>🟢 <strong><code>feat: define common news record format</code></strong> · <sub>2026-08-11 01:58:24（UTC+8）</sub></summary>

<br>

<strong>Commit：</strong> [`5a95bb1`](https://github.com/OllieHu12304/Morning-Alpha/commit/5a95bb1511493d1179b5845125a17fd77c8ea183)

建立多來源共同新聞格式與欄位驗證，使不同 adapter 都輸出一致的 title、URL、source、category 等資料。

> 💡 <strong>學習重點：</strong> 共同 record format 是多來源系統的邊界，可防止來源特有欄位擴散到所有模組。

</details>

<details>
<summary>🟢 <strong><code>feat: allow duplicate news titles</code></strong> · <sub>2026-08-11 01:57:13（UTC+8）</sub></summary>

<br>

<strong>Commit：</strong> [`a91dff6`](https://github.com/OllieHu12304/Morning-Alpha/commit/a91dff600cb3519334dff260f80a4ba778c28d57)

透過 Migration 004 移除 title UNIQUE，允許不同來源或不同文章使用相同標題，改由 canonical URL 負責唯一性。

> 💡 <strong>學習重點：</strong> Database unique constraint 必須建立在真正穩定的識別欄位上，不能因方便而選擇標題。

</details>

<details>
<summary>🟢 <strong><code>feat: enforce canonical URL uniqueness</code></strong> · <sub>2026-08-11 01:56:40（UTC+8）</sub></summary>

<br>

<strong>Commit：</strong> [`14e8987`](https://github.com/OllieHu12304/Morning-Alpha/commit/14e8987507d1b6bbf9d2fa8410a38c1403e0a0a8)

新增 canonical URL hash、舊資料回填與 UNIQUE constraint，以正規化網址阻止同一篇文章重複寫入。

> 💡 <strong>學習重點：</strong> 長網址可先標準化再雜湊，讓資料庫用固定長度索引有效判斷唯一性。

</details>

<details>
<summary>🟢 <strong><code>feat: normalize canonical news URLs</code></strong> · <sub>2026-08-11 01:44:02（UTC+8）</sub></summary>

<br>

<strong>Commit：</strong> [`e59ab24`](https://github.com/OllieHu12304/Morning-Alpha/commit/e59ab241441828b078f2e18d994269de6192e045)

新增 URL canonicalization，移除追蹤參數、fragment 等不影響文章內容的網址差異，產生穩定 canonical URL。

> 💡 <strong>學習重點：</strong> 看似不同的 URL 可能指向相同內容，去重前應先定義哪些網址部分具有識別意義。

</details>

<details>
<summary>🟢 <strong><code>feat: add news quality fields to storage schema</code></strong> · <sub>2026-08-11 01:23:24（UTC+8）</sub></summary>

<br>

<strong>Commit：</strong> [`bab6de3`](https://github.com/OllieHu12304/Morning-Alpha/commit/bab6de34204d4adbfa1c1850cd796c7aeb2ec9a0)

在新聞 Schema 加入 `source`、`category`、`source_category` 與 canonical URL 等正式欄位，提升來源與分類的可追蹤性。

> 💡 <strong>學習重點：</strong> 重要分析維度應成為正式欄位，而不是暫時從標題猜測或藏在非結構化文字中。

</details>

<details>
<summary>🟢 <strong><code>feat: add unified data pipeline runner</code></strong> · <sub>2026-08-11 00:35:25（UTC+8）</sub></summary>

<br>

<strong>Commit：</strong> [`13e9130`](https://github.com/OllieHu12304/Morning-Alpha/commit/13e9130a883e142d4ce511cacf9cb45104c15a73)

新增 `src/run_pipeline.py` 統一入口，一次完成爬取、整理、MySQL 寫入、JSON 匯出與統計產生。

> 💡 <strong>學習重點：</strong> 統一 orchestrator 能固定執行順序、集中錯誤處理，避免使用者手動執行多個 script。

</details>

## 2026-08-10

<details>
<summary>🔵 <strong><code>docs: add Morning Alpha v0.1 user guide</code></strong> · <sub>2026-08-10 21:25:34（UTC+8）</sub></summary>

<br>

<strong>Commit：</strong> [`2e4611f`](https://github.com/OllieHu12304/Morning-Alpha/commit/2e4611f259a20d025a051751b7c8ad84f9eb6eb2)

依 Repository 實際內容建立 v0.1 使用手冊，整理架構、安裝、MySQL、執行流程、Dashboard、限制與學習重點。

> 💡 <strong>學習重點：</strong> 好的使用文件必須以已實作程式為準，清楚區分實際功能與未來規劃。

</details>

<details>
<summary>🟢 <strong><code>feat: analyze top keywords with pandas</code></strong> · <sub>2026-08-10 17:48:02（UTC+8）</sub></summary>

<br>

<strong>Commit：</strong> [`401fe2c`](https://github.com/OllieHu12304/Morning-Alpha/commit/401fe2c0a5759e04445ffefaede4162d782e2d96)

使用 Pandas 計算新聞標題 Top 20 關鍵字並匯出 `keyword.json`，為 Dashboard 關鍵字分析準備資料。

> 💡 <strong>學習重點：</strong> Pandas 可將文字計數結果整理成表格，再轉成 JSON 供前端使用。

</details>

<details>
<summary>🟢 <strong><code>feat: add news analytics charts to dashboard</code></strong> · <sub>2026-08-10 17:40:26（UTC+8）</sub></summary>

<br>

<strong>Commit：</strong> [`2c7b2ea`](https://github.com/OllieHu12304/Morning-Alpha/commit/2c7b2ea2ecfdd2008b169776e3b51f194a546945)

使用 Pandas 產生圖表統計 JSON，並以 Chart.js 在 Dashboard 顯示新聞分析圖表。

> 💡 <strong>學習重點：</strong> 後端負責彙總資料、前端負責視覺化，可以讓資料邏輯與畫面呈現各自保持單純。

</details>

## 2026-08-08

<details>
<summary>🟢 <strong><code>feat: add sortable HTML news dashboard</code></strong> · <sub>2026-08-08 01:59:06（UTC+8）</sub></summary>

<br>

<strong>Commit：</strong> [`fcb2486`](https://github.com/OllieHu12304/Morning-Alpha/commit/fcb248687ed461a3f6efe15f91b2f4d2b3b0f54e)

建立 HTML、CSS、JavaScript 新聞 Dashboard，將 MySQL 資料匯出成 `news.json`，並使用 DataTables 提供排序與表格瀏覽。

> 💡 <strong>學習重點：</strong> 瀏覽器可透過 JSON 接收 Python 處理結果，再由 JavaScript 動態建立互動介面。

</details>

<details>
<summary>🟢 <strong><code>feat: read MySQL news into a DataFrame</code></strong> · <sub>2026-08-08 01:44:50（UTC+8）</sub></summary>

<br>

<strong>Commit：</strong> [`d94d876`](https://github.com/OllieHu12304/Morning-Alpha/commit/d94d8763cc654b79a9b23191ad71e40031c171b8)

新增 MySQL 查詢程式，使用 PyMySQL 讀取新聞，再轉成 Pandas DataFrame 供後續分析與匯出。

> 💡 <strong>學習重點：</strong> Database row 適合持久保存，DataFrame 則適合清理、統計與轉換，兩者各有用途。

</details>

<details>
<summary>🟢 <strong><code>feat: add MySQL news storage and setup guide</code></strong> · <sub>2026-08-08 01:09:09（UTC+8）</sub></summary>

<br>

<strong>Commit：</strong> [`dbe8d0b`](https://github.com/OllieHu12304/Morning-Alpha/commit/dbe8d0b3122461435e02278ac80098b1cb849cf8)

新增 MySQL 新聞儲存程式、PyMySQL 依賴與設定說明，讓整理後的新聞能長期保存而非只存在記憶體。

> 💡 <strong>學習重點：</strong> 資料庫連線、Schema 與參數化 SQL 是 Python 應用保存結構化資料的基礎。

</details>

<details>
<summary>🔵 <strong><code>update README of Feature03</code></strong> · <sub>2026-08-08 00:11:28（UTC+8）</sub></summary>

<br>

<strong>Commit：</strong> [`80bb45c`](https://github.com/OllieHu12304/Morning-Alpha/commit/80bb45c781aac84c9a07a0080fe2a0cb92b1bf7c)

更新 README，補充 Feature 3 的 Pandas 新聞整理方式與執行說明。

> 💡 <strong>學習重點：</strong> 每完成一個功能就同步文件，能降低實作與操作說明逐漸不一致的風險。

</details>

<details>
<summary>🟢 <strong><code>feat: transform crawler results with pandas</code></strong> · <sub>2026-08-08 00:08:26（UTC+8）</sub></summary>

<br>

<strong>Commit：</strong> [`f09e348`](https://github.com/OllieHu12304/Morning-Alpha/commit/f09e348a33af53af1db42ae5c9a412cd24ccafe5)

新增 Pandas 整理流程，把 crawler 回傳的新聞轉成 DataFrame，進行欄位選取、清理與基本去重。

> 💡 <strong>學習重點：</strong> 爬蟲負責取得原始資料，Pandas 負責轉換與清理，分工後更容易單獨測試。

</details>

## 2026-08-07

<details>
<summary>🟢 <strong><code>feat: add TechNews homepage crawler</code></strong> · <sub>2026-08-07 23:39:59（UTC+8）</sub></summary>

<br>

<strong>Commit：</strong> [`bc2f3aa`](https://github.com/OllieHu12304/Morning-Alpha/commit/bc2f3aa427f34ee15ad2f957b72c8688b1f2dc63)

建立第一個可執行的 TechNews 首頁 crawler，使用 Requests 下載 HTML，再以 BeautifulSoup 擷取文章標題與網址。

> 💡 <strong>學習重點：</strong> 網頁爬蟲的基本流程是 HTTP 請求、HTML 解析、CSS selector 擷取及資料驗證。

</details>

<details>
<summary>🟢 <strong><code>feat: add first TechNews crawler</code></strong> · <sub>2026-08-07 23:20:37（UTC+8）</sub></summary>

<br>

<strong>Commit：</strong> [`f1165a7`](https://github.com/OllieHu12304/Morning-Alpha/commit/f1165a78074427de6d2a82d8c0f4fa04fb412610)

建立 Morning Alpha 的初始資料夾、requirements 與功能規劃，準備 crawler、資料、SQL、Dashboard 和 tests 的基本位置。

> 💡 <strong>學習重點：</strong> 在開始寫功能前先建立清楚的最小專案骨架，有助於後續程式依責任分類。

</details>

<details>
<summary>🏁 <strong><code>Initial commit</code></strong> · <sub>2026-08-07 23:02:23（UTC+8）</sub></summary>

<br>

<strong>Commit：</strong> [`bbb29b5`](https://github.com/OllieHu12304/Morning-Alpha/commit/bbb29b5bc86db15026292fd5a29a3e23b663d5c7)

建立 Repository 與最初版 README，正式開始 Morning Alpha 專案的版本歷史。

> 💡 <strong>學習重點：</strong> 初始 commit 提供清楚的專案起點，後續每個功能才能被獨立追蹤與回溯。

</details>
