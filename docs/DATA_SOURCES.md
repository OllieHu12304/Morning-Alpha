# Morning Alpha 市場與財務資料來源契約

這份文件記錄 Morning Alpha Phase 4 實際使用哪些外部資料，以及 Python
adapter 轉換成什麼格式。契約最初由 Feature 4.11 定義，目前下載、驗證、
MySQL upsert、API 與 Dashboard 已由後續 Features 實作。

## 選擇原則

1. 優先使用官方、免費且公開的 API。
2. v0.3 第一版只支援 TWSE 上市公司，不宣稱已支援 TPEx 上櫃公司。
3. 原始欄位先經 adapter 驗證，再轉成 Morning Alpha 英文共同欄位。
4. 原始資料缺欄、空白或無法轉換時，不用 `0` 代替。
5. 所有數據都必須保留來源名稱與取得時間。
6. 市場與財務資料只供資訊整理，不構成投資建議。

## 1. 上市個股每日價格

| 項目 | 決定 |
| --- | --- |
| Provider | 臺灣證券交易所（TWSE） |
| Dataset | 上市個股日成交資訊 |
| Endpoint | `https://openapi.twse.com.tw/v1/exchangeReport/STOCK_DAY_ALL` |
| 官方說明 | [TWSE OpenAPI](https://openapi.twse.com.tw/) |
| 政府資料集 | [上市個股日成交資訊](https://data.gov.tw/dataset/11549) |
| 更新策略 | 每個排程日於收盤後取得一次 |
| 計費 | 免費 |
| 授權 | 政府資料開放授權條款－第 1 版 |
| 範圍 | TWSE 上市證券；目前不含 TPEx |

### 原始欄位轉換

| TWSE 欄位 | Morning Alpha 欄位 | 說明 |
| --- | --- | --- |
| `Date` | `trade_date` | 民國年月日，adapter 轉為 `YYYY-MM-DD` |
| `Code` | `ticker` | 股票代號，以文字保存 |
| `Name` | `name` | 證券名稱，只供核對 |
| `TradeVolume` | `volume` | 成交股數 |
| `TradeValue` | `trade_value` | 成交金額 |
| `OpeningPrice` | `open_price` | 開盤價 |
| `HighestPrice` | `high_price` | 最高價 |
| `LowestPrice` | `low_price` | 最低價 |
| `ClosingPrice` | `close_price` | 收盤價 |
| `Change` | `price_change` | 與前一交易日的價差 |
| `Transaction` | `transaction_count` | 成交筆數 |

adapter 還會補上 `exchange="TWSE"`、`currency="TWD"`、`source` 與
`fetched_at`。MySQL 實際以 `security_id + trade_date` 作為唯一識別。

### 價格資料限制

- 這是每日盤後資料，不是盤中即時報價。
- 不將排程執行日期直接當成交易日，必須使用來源的 `Date`。
- 無成交資料可能使用空白或特殊符號，adapter 必須轉成 `null`，不能轉成 `0`。
- 此 endpoint 用於每日快照；第一版不承諾補齊任意過往日期。

## 2. 上市公司財務指標

| 項目 | 決定 |
| --- | --- |
| Provider | 臺灣證券交易所（TWSE） |
| Dataset | 上市公司各產業 EPS 統計資訊 |
| Endpoint | `https://openapi.twse.com.tw/v1/opendata/t187ap14_L` |
| 官方資料 | [TWSE EPS OpenAPI](https://openapi.twse.com.tw/v1/opendata/t187ap14_L) |
| 政府資料集 | [上市公司各產業 EPS 統計資訊](https://data.gov.tw/dataset/20756) |
| 更新策略 | 每日檢查；內容依公司季報更新 |
| 計費 | 免費 |
| 授權 | 政府資料開放授權條款－第 1 版 |
| 範圍 | TWSE 上市公司；目前不含 TPEx |

### 原始欄位轉換

| TWSE 欄位 | Morning Alpha 欄位 | 說明 |
| --- | --- | --- |
| `出表日期` | `report_date` | 民國年月日，轉為 `YYYY-MM-DD` |
| `年度` | `fiscal_year` | 民國年度，轉為西元年度 |
| `季別` | `fiscal_quarter` | 1 到 4 |
| `公司代號` | `ticker` | 股票代號，以文字保存 |
| `公司名稱` | `name` | 公司名稱，只供核對 |
| `產業別` | `industry` | 官方產業分類 |
| `基本每股盈餘(元)` | `earnings_per_share` | 基本 EPS |
| `普通股每股面額` | `face_value_text` | 保留官方原始文字 |
| `營業收入` | `operating_revenue` | 保留官方原始數值尺度 |
| `營業利益` | `operating_income` | 保留官方原始數值尺度 |
| `營業外收入及支出` | `non_operating_income_expense` | 保留官方原始數值尺度 |
| `稅後淨利` | `net_income` | 保留官方原始數值尺度 |

adapter 還會補上 `exchange="TWSE"`、`currency="TWD"`、`source` 與
`fetched_at`。MySQL 實際以 `security_id + fiscal_year + fiscal_quarter`
作為唯一識別。

### 財務資料限制

- endpoint 每日可能更新，但同一公司通常是依季度增加新內容。
- 第一版使用摘要指標，不等於完整財務報表。
- 官方資料的金額尺度在這份資料中未明確標示，因此第一版不自行乘以千或萬。
- 不同產業的財務結構不同，不能只靠單一 EPS 或營收數字判斷公司好壞。
- 財報可能更正；相同公司與季度再次出現時應更新既有紀錄。

## 3. Adapter 共同規則

每筆轉換完成的紀錄都必須：

1. 可透過 `ticker + exchange` 對應 `securities`。
2. 數字移除千分位後再轉換；無效值保存為 `null`。
3. 民國年加 `1911` 轉成西元年。
4. 保存 `source` 和帶 timezone 的 `fetched_at`。
5. 原始 payload 不是非空 JSON list、必要欄位消失或全部紀錄無效時，明確中止並記錄錯誤。

## 4. 暫不採用的選項

- `yfinance`：方便但不是臺灣市場官方來源，ticker 規則與可用性可能改變。
- FinMind：適合研究與歷史資料，但 Phase 4 第一版優先建立官方來源流程。
- 券商即時 API：通常需要帳號、憑證或行情授權，超出目前免費本機 MVP 範圍。
- 網頁 HTML 爬蟲：市場與財務資料已有官方結構化 API，不需要依賴容易改版的頁面結構。

若未來需要 TPEx、完整歷史回補或即時行情，必須新增獨立 adapter、來源契約與測試，不能默默混入 TWSE 資料。
