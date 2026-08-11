const NEWS_API = "/api/news";
const ANALYTICS_API = "/api/analytics";
const SOURCE_HEALTH_API = "/api/source-health";
const PIPELINE_RUNS_API = "/api/pipeline-runs";
const LATEST_DAILY_BRIEF_API = "/api/daily-briefs/latest";
const MARKET_COMPANIES_API = "/api/market-companies";
const EVENT_MARKET_API = "/api/event-market-observations";
const WATCHLIST_API = "/api/watchlist";
const PERSONALIZED_BRIEF_API = "/api/personalized-brief";
const KEYWORD_CHART_LIMIT = 10;
const PIPELINE_RUN_DISPLAY_LIMIT = 5;

const SOURCE_LABELS = {
    cna: "中央通訊社",
    technews: "TechNews 科技新報",
};

const tableBody = document.querySelector("#news-table-body");
const statusMessage = document.querySelector("#status-message");
const chartStatusMessage = document.querySelector("#chart-status-message");
const sourceHealthMessage = document.querySelector("#source-health-message");
const sourceHealthGrid = document.querySelector("#source-health-grid");
const pipelineHistoryMessage = document.querySelector("#pipeline-history-message");
const pipelineRunsList = document.querySelector("#pipeline-runs-list");
const dailyBriefMessage = document.querySelector("#daily-brief-message");
const dailyBriefContent = document.querySelector("#daily-brief-content");
const personalizedBriefMessage = document.querySelector("#personalized-brief-message");
const personalizedBriefResult = document.querySelector("#personalized-brief-result");
const watchlistItems = document.querySelector("#watchlist-items");
const lastUpdatedMessage = document.querySelector("#last-updated");
const searchInput = document.querySelector("#news-search");
const sourceFilter = document.querySelector("#source-filter");
const categoryFilter = document.querySelector("#category-filter");
const companyFilter = document.querySelector("#company-filter");
const pageSizeSelect = document.querySelector("#page-size");
const clearFiltersButton = document.querySelector("#clear-filters");
const previousPageButton = document.querySelector("#previous-page");
const nextPageButton = document.querySelector("#next-page");
const pageStatus = document.querySelector("#page-status");
const tableHeaders = document.querySelectorAll("th[data-key]");
const marketCompanySelect = document.querySelector("#market-company-select");
const watchlistToggle = document.querySelector("#watchlist-toggle");
const companyMarketMessage = document.querySelector("#company-market-message");
const latestClosePrice = document.querySelector("#latest-close-price");
const latestTradeDate = document.querySelector("#latest-trade-date");
const latestPriceChange = document.querySelector("#latest-price-change");
const latestEps = document.querySelector("#latest-eps");
const latestFinancialPeriod = document.querySelector("#latest-financial-period");
const companyFinancialBody = document.querySelector("#company-financial-body");
const companyPriceEmpty = document.querySelector("#company-price-empty");
const eventMarketMessage = document.querySelector("#event-market-message");
const eventMarketMethodology = document.querySelector("#event-market-methodology");
const eventMarketBody = document.querySelector("#event-market-body");
const eventMarketLimitations = document.querySelector("#event-market-limitations");

let newsRecords = [];
let sortKey = "publish_time";
let sortDirection = "desc";
let currentPage = 1;
let pageSize = Number(pageSizeSelect.value);
let eventGroupFilter = null;
let companyPriceChart = null;
let watchlistCompanyIds = new Set();


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


async function loadWatchlist() {
    try {
        const payload = await fetchJson(WATCHLIST_API);

        if (!payload || !Array.isArray(payload.items)) {
            throw new Error("watchlist API 格式不正確。");
        }

        watchlistCompanyIds = new Set(
            payload.items.map((item) => String(item.company_id)),
        );
        renderWatchlistItems(payload.items);
        updateWatchlistButton();
        return true;
    } catch (error) {
        watchlistItems.replaceChildren();
        watchlistToggle.disabled = true;
        personalizedBriefMessage.textContent = `無法載入追蹤清單：${error.message}`;
        personalizedBriefMessage.classList.add("error-message");
        return false;
    }
}


function renderWatchlistItems(items) {
    watchlistItems.replaceChildren();

    if (items.length === 0) {
        const item = document.createElement("li");
        item.className = "watchlist-empty";
        item.textContent = "尚未追蹤公司，可從下方公司市場資料加入。";
        watchlistItems.appendChild(item);
        return;
    }

    for (const company of items) {
        if (!company.company_id || !company.name) {
            throw new Error("追蹤清單包含無效公司資料。");
        }

        const item = document.createElement("li");
        const name = company.short_name || company.name;
        item.textContent = company.ticker
            ? `${company.ticker} ${name}`
            : name;
        watchlistItems.appendChild(item);
    }
}


async function loadPersonalizedBrief() {
    try {
        const payload = await fetchJson(PERSONALIZED_BRIEF_API);

        if (!payload || !payload.brief) {
            throw new Error("personalized brief API 格式不正確。");
        }

        renderPersonalizedBrief(payload.brief);
    } catch (error) {
        personalizedBriefResult.replaceChildren();
        personalizedBriefMessage.textContent = `無法載入個人化晨報：${error.message}`;
        personalizedBriefMessage.classList.add("error-message");
    }
}


function renderPersonalizedBrief(brief) {
    validateDailyBrief(brief);

    if (
        !Number.isInteger(Number(brief.watchlist_count))
        || !Array.isArray(brief.watched_companies)
    ) {
        throw new Error("個人化晨報欄位格式不正確。");
    }

    personalizedBriefResult.replaceChildren();
    personalizedBriefMessage.classList.remove("error-message");

    const summary = document.createElement("p");
    summary.className = "personalized-summary";
    summary.textContent = String(brief.summary);
    personalizedBriefResult.appendChild(summary);

    const highlights = document.createElement("ol");
    highlights.className = "personalized-highlights";

    for (const highlight of brief.highlights) {
        highlights.appendChild(createBriefHighlight(highlight));
    }

    if (brief.highlights.length === 0) {
        const item = document.createElement("li");
        item.textContent = "本期沒有可顯示的追蹤公司新聞。";
        highlights.appendChild(item);
    }

    personalizedBriefResult.appendChild(highlights);
    personalizedBriefMessage.textContent = `追蹤 ${brief.watchlist_count} 家公司・相關新聞 ${brief.article_count} 篇`;
}


function updateWatchlistButton() {
    const companyId = marketCompanySelect.value;

    if (!companyId || marketCompanySelect.disabled) {
        watchlistToggle.disabled = true;
        watchlistToggle.textContent = "加入追蹤";
        return;
    }

    watchlistToggle.disabled = false;
    watchlistToggle.textContent = watchlistCompanyIds.has(companyId)
        ? "移除追蹤"
        : "加入追蹤";
}


async function toggleSelectedCompanyWatchlist() {
    const companyId = marketCompanySelect.value;

    if (!companyId) {
        return;
    }

    const isTracked = watchlistCompanyIds.has(companyId);
    watchlistToggle.disabled = true;

    try {
        await fetchJson(`${WATCHLIST_API}/${companyId}`, {
            method: isTracked ? "DELETE" : "POST",
        });
        const loaded = await loadWatchlist();

        if (loaded) {
            await loadPersonalizedBrief();
        }
    } catch (error) {
        personalizedBriefMessage.textContent = `無法更新追蹤清單：${error.message}`;
        personalizedBriefMessage.classList.add("error-message");
        updateWatchlistButton();
    }
}


async function loadNews() {
    try {
        const payload = await fetchJson(NEWS_API);

        if (!payload || !Array.isArray(payload.news)) {
            throw new Error("news API 格式不正確。");
        }

        newsRecords = payload.news;
        populateFilters();
        renderTable();
    } catch (error) {
        showError(`無法載入新聞 API：${error.message}`);
    }
}


async function loadAnalytics() {
    try {
        const payload = await fetchJson(ANALYTICS_API);

        if (!payload || !Array.isArray(payload.keywords)) {
            throw new Error("analytics API 格式不正確。");
        }

        const analytics = {
            sources: validateChartSeries(payload.sources, "sources"),
            categories: validateChartSeries(payload.categories, "categories"),
            keywords: keywordRecordsToSeries(payload.keywords),
        };

        renderCharts(analytics);
        lastUpdatedMessage.textContent = formatLastUpdated(payload.last_updated);
    } catch (error) {
        showChartError(`無法載入統計 API：${error.message}`);
        lastUpdatedMessage.textContent = `資料庫最後新增：無法載入（${error.message}）`;
    }
}


async function loadMarketCompanies() {
    try {
        const payload = await fetchJson(MARKET_COMPANIES_API);

        if (!payload || !Array.isArray(payload.companies)) {
            throw new Error("market companies API 格式不正確。");
        }

        populateMarketCompanySelect(payload.companies);

        if (payload.companies.length > 0) {
            await loadSelectedCompanyMarketData();
        }
    } catch (error) {
        showCompanyMarketError(`無法載入公司市場資料：${error.message}`);
    }
}


async function loadEventMarketObservations() {
    try {
        const payload = await fetchJson(EVENT_MARKET_API);

        if (
            !payload
            || payload.analysis_type !== "observational"
            || typeof payload.methodology !== "string"
            || !Array.isArray(payload.limitations)
            || !Array.isArray(payload.observations)
        ) {
            throw new Error("event market API 格式不正確。");
        }

        renderEventMarketObservations(payload);
    } catch (error) {
        eventMarketBody.replaceChildren();
        appendEventMarketEmptyRow("事件市場觀察暫時無法顯示。");
        eventMarketMessage.textContent = `無法載入事件觀察：${error.message}`;
        eventMarketMessage.classList.add("error-message");
    }
}


function renderEventMarketObservations(payload) {
    eventMarketBody.replaceChildren();
    eventMarketLimitations.replaceChildren();
    eventMarketMethodology.textContent = `觀察方法：${payload.methodology}`;
    eventMarketMessage.classList.remove("error-message");

    if (payload.observations.length === 0) {
        appendEventMarketEmptyRow(
            "目前沒有足夠的公司新聞與前後交易日價格可供觀察。",
        );
    } else {
        for (const observation of payload.observations) {
            eventMarketBody.appendChild(createEventMarketRow(observation));
        }
    }

    for (const limitation of payload.limitations) {
        const item = document.createElement("li");
        item.textContent = String(limitation);
        eventMarketLimitations.appendChild(item);
    }

    eventMarketMessage.textContent = `顯示 ${payload.observations.length} 筆時間關聯觀察`;
}


function createEventMarketRow(observation) {
    if (
        !observation
        || observation.analysis_type !== "observational"
        || !observation.title
        || !observation.company_name
        || !observation.ticker
        || !observation.baseline_trade_date
        || !observation.observation_trade_date
    ) {
        throw new Error("事件市場觀察包含無效資料。");
    }

    const row = document.createElement("tr");
    const newsCell = document.createElement("td");
    newsCell.appendChild(createSafeLink(
        observation.url,
        observation.title,
    ));
    const publishTime = document.createElement("span");
    publishTime.className = "event-observation-detail";
    publishTime.textContent = `發布：${formatPublishTime(observation.publish_time)}`;
    newsCell.appendChild(publishTime);

    const companyCell = document.createElement("td");
    companyCell.textContent = `${observation.ticker} ${observation.short_name || observation.company_name}`;

    const windowCell = document.createElement("td");
    windowCell.textContent = `${observation.baseline_trade_date} → ${observation.observation_trade_date}`;

    const changeCell = document.createElement("td");
    const changePercent = optionalNumber(observation.change_percent);
    changeCell.className = "event-price-change";
    changeCell.textContent = changePercent === null
        ? "—"
        : `${formatSignedNumber(changePercent)}%`;
    const closeDetail = document.createElement("span");
    closeDetail.className = "event-observation-detail";
    closeDetail.textContent = `${formatMarketNumber(observation.baseline_close, 4)} → ${formatMarketNumber(observation.observation_close, 4)} TWD`;
    changeCell.appendChild(closeDetail);

    row.append(newsCell, companyCell, windowCell, changeCell);
    return row;
}


function appendEventMarketEmptyRow(message) {
    const row = document.createElement("tr");
    const cell = document.createElement("td");
    cell.colSpan = 4;
    cell.className = "empty-message";
    cell.textContent = message;
    row.appendChild(cell);
    eventMarketBody.appendChild(row);
}


function populateMarketCompanySelect(companies) {
    marketCompanySelect.replaceChildren();

    if (companies.length === 0) {
        const option = document.createElement("option");
        option.value = "";
        option.textContent = "尚無市場或財務資料";
        marketCompanySelect.appendChild(option);
        marketCompanySelect.disabled = true;
        companyMarketMessage.textContent = "請先同步 TWSE 資料";
        renderCompanyMarketData([], []);
        updateWatchlistButton();
        return;
    }

    for (const company of companies) {
        if (!company.company_id || !company.ticker || !company.name) {
            throw new Error("公司選單包含無效資料。");
        }

        const option = document.createElement("option");
        option.value = String(company.company_id);
        const name = company.short_name || company.name;
        option.textContent = `${company.ticker} ${name}`;
        marketCompanySelect.appendChild(option);
    }

    marketCompanySelect.disabled = false;
    updateWatchlistButton();
}


async function loadSelectedCompanyMarketData() {
    const companyId = marketCompanySelect.value;

    if (!companyId) {
        updateWatchlistButton();
        return;
    }

    updateWatchlistButton();

    companyMarketMessage.textContent = "正在載入價格與財務資料…";
    companyMarketMessage.classList.remove("error-message");

    try {
        const [pricePayload, financialPayload] = await Promise.all([
            fetchJson(`/api/companies/${companyId}/market-prices`),
            fetchJson(`/api/companies/${companyId}/financial-metrics`),
        ]);

        if (!pricePayload || !Array.isArray(pricePayload.prices)) {
            throw new Error("market prices API 格式不正確。");
        }

        if (!financialPayload || !Array.isArray(financialPayload.metrics)) {
            throw new Error("financial metrics API 格式不正確。");
        }

        renderCompanyMarketData(
            pricePayload.prices,
            financialPayload.metrics,
        );
        companyMarketMessage.textContent = "公司資料已更新";
    } catch (error) {
        showCompanyMarketError(`無法載入公司資料：${error.message}`);
    }
}


function optionalNumber(value) {
    if (value === null || value === undefined || value === "") {
        return null;
    }

    const number = Number(value);
    return Number.isFinite(number) ? number : null;
}


function formatMarketNumber(value, maximumFractionDigits = 2) {
    const number = optionalNumber(value);

    if (number === null) {
        return "—";
    }

    return new Intl.NumberFormat("zh-TW", {
        maximumFractionDigits,
    }).format(number);
}


function renderCompanyMarketData(prices, metrics) {
    const latestPrice = prices[0] || null;
    const latestMetric = metrics[0] || null;

    latestClosePrice.textContent = latestPrice
        ? `${formatMarketNumber(latestPrice.close_price, 4)} TWD`
        : "—";
    latestTradeDate.textContent = latestPrice
        ? `交易日 ${latestPrice.trade_date}`
        : "尚無交易資料";
    latestPriceChange.textContent = latestPrice
        ? formatSignedNumber(latestPrice.price_change)
        : "—";
    latestEps.textContent = latestMetric
        ? `${formatMarketNumber(latestMetric.earnings_per_share, 4)} 元`
        : "—";
    latestFinancialPeriod.textContent = latestMetric
        ? `${latestMetric.fiscal_year} Q${latestMetric.fiscal_quarter}`
        : "尚無季度資料";

    renderCompanyPriceChart(prices);
    renderFinancialTable(metrics);
}


function formatSignedNumber(value) {
    const number = optionalNumber(value);

    if (number === null) {
        return "—";
    }

    const prefix = number > 0 ? "+" : "";
    return `${prefix}${formatMarketNumber(number, 4)}`;
}


function renderCompanyPriceChart(prices) {
    const chartPrices = [...prices]
        .reverse()
        .filter((record) => optionalNumber(record.close_price) !== null);
    const canvas = document.querySelector("#company-price-chart");

    if (companyPriceChart) {
        companyPriceChart.destroy();
        companyPriceChart = null;
    }

    if (chartPrices.length === 0 || typeof Chart === "undefined") {
        canvas.hidden = true;
        companyPriceEmpty.hidden = false;
        companyPriceEmpty.textContent = chartPrices.length === 0
            ? "目前沒有可顯示的收盤價。"
            : "Chart.js 尚未載入。";
        return;
    }

    canvas.hidden = false;
    companyPriceEmpty.hidden = true;
    companyPriceChart = new Chart(canvas, {
        type: "line",
        data: {
            labels: chartPrices.map((record) => record.trade_date),
            datasets: [{
                label: "收盤價（TWD）",
                data: chartPrices.map((record) => Number(record.close_price)),
                borderColor: "#0b6e69",
                backgroundColor: "rgba(11, 110, 105, 0.12)",
                fill: true,
                tension: 0.2,
            }],
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false },
            },
            scales: {
                y: { beginAtZero: false },
            },
        },
    });
}


function renderFinancialTable(metrics) {
    companyFinancialBody.replaceChildren();

    if (metrics.length === 0) {
        const row = document.createElement("tr");
        const cell = document.createElement("td");
        cell.colSpan = 4;
        cell.className = "empty-message";
        cell.textContent = "目前沒有季度財務資料。";
        row.appendChild(cell);
        companyFinancialBody.appendChild(row);
        return;
    }

    for (const metric of metrics) {
        const row = document.createElement("tr");
        const values = [
            `${metric.fiscal_year} Q${metric.fiscal_quarter}`,
            formatMarketNumber(metric.earnings_per_share, 4),
            formatMarketNumber(metric.operating_revenue, 2),
            formatMarketNumber(metric.net_income, 2),
        ];

        for (const value of values) {
            const cell = document.createElement("td");
            cell.textContent = value;
            row.appendChild(cell);
        }

        companyFinancialBody.appendChild(row);
    }
}


function showCompanyMarketError(message) {
    companyMarketMessage.textContent = message;
    companyMarketMessage.classList.add("error-message");
    renderCompanyMarketData([], []);
}


async function loadSourceHealth() {
    try {
        const payload = await fetchJson(SOURCE_HEALTH_API);

        if (!payload || !Array.isArray(payload.sources)) {
            throw new Error("source health API 格式不正確。");
        }

        renderSourceHealth(payload.sources);
    } catch (error) {
        showSourceHealthError(`無法載入來源狀態：${error.message}`);
    }
}


function validateSourceHealthRecord(record) {
    if (!record || typeof record !== "object") {
        throw new Error("來源狀態包含無效資料。");
    }

    const articleCount = Number(record.article_count);

    if (
        !record.source
        || !["success", "failure"].includes(record.status)
        || !Number.isInteger(articleCount)
        || articleCount < 0
    ) {
        throw new Error("來源狀態欄位格式不正確。");
    }

    return {
        ...record,
        article_count: articleCount,
    };
}


function renderSourceHealth(records) {
    sourceHealthGrid.replaceChildren();
    sourceHealthMessage.classList.remove("error-message");

    if (records.length === 0) {
        const emptyMessage = document.createElement("p");
        emptyMessage.className = "source-health-empty";
        emptyMessage.textContent = "尚無來源執行紀錄，請先執行 Pipeline。";
        sourceHealthGrid.appendChild(emptyMessage);
        sourceHealthMessage.textContent = "尚無紀錄";
        return;
    }

    for (const sourceRecord of records) {
        const record = validateSourceHealthRecord(sourceRecord);
        sourceHealthGrid.appendChild(createSourceHealthCard(record));
    }

    sourceHealthMessage.textContent = `已載入 ${records.length} 個來源`;
}


function createSourceHealthCard(record) {
    const card = document.createElement("article");
    card.className = "source-health-card";

    const heading = document.createElement("div");
    heading.className = "source-health-card-heading";

    const title = document.createElement("h3");
    title.textContent = SOURCE_LABELS[record.source] || String(record.source);

    const badge = document.createElement("span");
    const isSuccessful = record.status === "success";
    badge.className = `source-health-badge source-health-badge-${record.status}`;
    badge.textContent = isSuccessful ? "正常" : "失敗";
    heading.append(title, badge);

    const details = document.createElement("dl");
    details.className = "source-health-details";
    appendSourceHealthDetail(
        details,
        "最近嘗試",
        formatHealthTime(record.last_attempt_at),
    );
    appendSourceHealthDetail(
        details,
        "最近成功",
        formatHealthTime(record.last_success_at),
    );
    appendSourceHealthDetail(
        details,
        "本次文章",
        `${record.article_count} 篇`,
    );

    card.append(heading, details);

    if (!isSuccessful && record.error_message) {
        const errorMessage = document.createElement("p");
        errorMessage.className = "source-health-error";
        errorMessage.textContent = `失敗原因：${record.error_message}`;
        card.appendChild(errorMessage);
    }

    return card;
}


function appendSourceHealthDetail(container, label, value) {
    const detail = document.createElement("div");
    const term = document.createElement("dt");
    const description = document.createElement("dd");
    term.textContent = label;
    description.textContent = value;
    detail.append(term, description);
    container.appendChild(detail);
}


function formatHealthTime(value) {
    return value ? formatPublishTime(value) : "尚無紀錄";
}


function showSourceHealthError(message) {
    sourceHealthGrid.replaceChildren();
    const errorMessage = document.createElement("p");
    errorMessage.className = "source-health-empty error-message";
    errorMessage.textContent = "來源狀態暫時無法顯示。";
    sourceHealthGrid.appendChild(errorMessage);
    sourceHealthMessage.textContent = message;
    sourceHealthMessage.classList.add("error-message");
}


async function loadDailyBrief() {
    try {
        const payload = await fetchJson(LATEST_DAILY_BRIEF_API);

        if (!payload || !("brief" in payload)) {
            throw new Error("daily brief API 格式不正確。");
        }

        renderDailyBrief(payload.brief);
    } catch (error) {
        showDailyBriefError(`無法載入每日晨報：${error.message}`);
    }
}


function validateDailyBrief(brief) {
    if (!brief || typeof brief !== "object") {
        throw new Error("每日晨報包含無效資料。");
    }

    const articleCount = Number(brief.article_count);
    const arrayFields = [
        "sources",
        "categories",
        "keywords",
        "highlights",
        "limitations",
    ];

    if (
        !brief.brief_date
        || !brief.window_start
        || !brief.window_end
        || typeof brief.summary !== "string"
        || !Number.isInteger(articleCount)
        || articleCount < 0
        || arrayFields.some((field) => !Array.isArray(brief[field]))
    ) {
        throw new Error("每日晨報欄位格式不正確。");
    }

    return {
        ...brief,
        article_count: articleCount,
    };
}


function renderDailyBrief(briefValue) {
    dailyBriefContent.replaceChildren();
    dailyBriefMessage.classList.remove("error-message");

    if (briefValue === null) {
        const emptyMessage = document.createElement("p");
        emptyMessage.className = "daily-brief-empty";
        emptyMessage.textContent = "尚無每日晨報，請先完成晨報資料更新。";
        dailyBriefContent.appendChild(emptyMessage);
        dailyBriefMessage.textContent = "尚無晨報";
        return;
    }

    const brief = validateDailyBrief(briefValue);
    const summaryBlock = document.createElement("div");
    summaryBlock.className = "daily-brief-summary";
    const dateHeading = document.createElement("h3");
    dateHeading.textContent = `${brief.brief_date} 晨報`;
    const windowText = document.createElement("p");
    windowText.className = "daily-brief-window";
    windowText.textContent = `資料時間：${formatPublishTime(brief.window_start)} 至 ${formatPublishTime(brief.window_end)}`;
    const summaryText = document.createElement("p");
    summaryText.className = "daily-brief-summary-text";
    summaryText.textContent = brief.summary;
    summaryBlock.append(dateHeading, windowText, summaryText);

    const dimensions = document.createElement("div");
    dimensions.className = "daily-brief-dimensions";
    appendBriefDimension(dimensions, "主要來源", brief.sources);
    appendBriefDimension(dimensions, "熱門分類", brief.categories);
    appendBriefDimension(dimensions, "熱門關鍵字", brief.keywords);

    const highlights = document.createElement("div");
    highlights.className = "daily-brief-highlights";
    const highlightsHeading = document.createElement("h3");
    highlightsHeading.textContent = "本期 Highlights";
    const highlightList = document.createElement("ol");

    for (const highlight of brief.highlights) {
        highlightList.appendChild(createBriefHighlight(highlight));
    }

    if (brief.highlights.length === 0) {
        const emptyHighlight = document.createElement("p");
        emptyHighlight.className = "daily-brief-muted";
        emptyHighlight.textContent = "本期沒有可顯示的新聞。";
        highlights.append(highlightsHeading, emptyHighlight);
    } else {
        highlights.append(highlightsHeading, highlightList);
    }

    const limitations = document.createElement("div");
    limitations.className = "daily-brief-limitations";
    const limitationsHeading = document.createElement("h3");
    limitationsHeading.textContent = "解讀限制";
    const limitationList = document.createElement("ul");

    for (const limitation of brief.limitations) {
        const item = document.createElement("li");
        item.textContent = String(limitation);
        limitationList.appendChild(item);
    }

    limitations.append(limitationsHeading, limitationList);
    dailyBriefContent.append(
        summaryBlock,
        dimensions,
        highlights,
        limitations,
    );
    dailyBriefMessage.textContent = `收錄 ${brief.article_count} 篇新聞`;
}


function appendBriefDimension(container, label, items) {
    const group = document.createElement("div");
    const heading = document.createElement("h3");
    heading.textContent = label;
    const list = document.createElement("ul");
    list.className = "daily-brief-chip-list";

    for (const item of items) {
        if (!item || !item.name || !Number.isFinite(Number(item.count))) {
            throw new Error("晨報統計項目格式不正確。");
        }

        const listItem = document.createElement("li");
        listItem.textContent = `${item.name} ${Number(item.count)}`;
        list.appendChild(listItem);
    }

    if (items.length === 0) {
        const listItem = document.createElement("li");
        listItem.textContent = "無資料";
        list.appendChild(listItem);
    }

    group.append(heading, list);
    container.appendChild(group);
}


function createBriefHighlight(highlight) {
    if (!highlight || typeof highlight !== "object" || !highlight.title) {
        throw new Error("晨報 highlight 格式不正確。");
    }

    const item = document.createElement("li");
    const title = document.createElement(highlight.url ? "a" : "span");
    title.textContent = String(highlight.title);

    if (highlight.url) {
        title.href = String(highlight.url);
        title.target = "_blank";
        title.rel = "noopener noreferrer";
    }

    const metadata = document.createElement("span");
    metadata.textContent = String(
        highlight.selection_reason || "時間窗內文章",
    );
    item.append(title, metadata);
    return item;
}


function showDailyBriefError(message) {
    dailyBriefContent.replaceChildren();
    const errorMessage = document.createElement("p");
    errorMessage.className = "daily-brief-empty error-message";
    errorMessage.textContent = "每日晨報暫時無法顯示。";
    dailyBriefContent.appendChild(errorMessage);
    dailyBriefMessage.textContent = message;
    dailyBriefMessage.classList.add("error-message");
}


async function loadPipelineRuns() {
    try {
        const payload = await fetchJson(PIPELINE_RUNS_API);

        if (!payload || !Array.isArray(payload.runs)) {
            throw new Error("pipeline runs API 格式不正確。");
        }

        renderPipelineRuns(payload.runs);
    } catch (error) {
        showPipelineRunsError(`無法載入 Pipeline 紀錄：${error.message}`);
    }
}


function validatePipelineRun(record) {
    if (!record || typeof record !== "object") {
        throw new Error("Pipeline 紀錄包含無效資料。");
    }

    const durationMs = Number(record.duration_ms);

    if (
        !["success", "failure"].includes(record.status)
        || !Number.isInteger(durationMs)
        || durationMs < 0
        || !Array.isArray(record.step_results)
        || ![4, 9].includes(record.step_results.length)
    ) {
        throw new Error("Pipeline 紀錄欄位格式不正確。");
    }

    for (const stepResult of record.step_results) {
        validatePipelineStep(stepResult);
    }

    return {
        ...record,
        duration_ms: durationMs,
    };
}


function validatePipelineStep(stepResult) {
    if (
        !stepResult
        || typeof stepResult !== "object"
        || !stepResult.step
        || !stepResult.label
        || !["pending", "success", "failure"].includes(stepResult.status)
    ) {
        throw new Error("Pipeline step 格式不正確。");
    }

    if (
        stepResult.duration_ms !== null
        && (
            !Number.isInteger(Number(stepResult.duration_ms))
            || Number(stepResult.duration_ms) < 0
        )
    ) {
        throw new Error("Pipeline step duration 格式不正確。");
    }
}


function renderPipelineRuns(records) {
    pipelineRunsList.replaceChildren();
    pipelineHistoryMessage.classList.remove("error-message");

    if (records.length === 0) {
        const emptyMessage = document.createElement("p");
        emptyMessage.className = "pipeline-runs-empty";
        emptyMessage.textContent = "尚無完整 Pipeline 紀錄，請執行新版 Pipeline。";
        pipelineRunsList.appendChild(emptyMessage);
        pipelineHistoryMessage.textContent = "尚無紀錄";
        return;
    }

    const displayedRecords = records.slice(0, PIPELINE_RUN_DISPLAY_LIMIT);

    displayedRecords.forEach((runRecord, index) => {
        const record = validatePipelineRun(runRecord);
        pipelineRunsList.appendChild(createPipelineRunCard(record, index === 0));
    });

    pipelineHistoryMessage.textContent = `顯示最近 ${displayedRecords.length} 次執行`;
}


function createPipelineRunCard(record, isLatest) {
    const card = document.createElement("article");
    card.className = "pipeline-run-card";

    if (isLatest) {
        card.classList.add("pipeline-run-card-latest");
    }

    const heading = document.createElement("div");
    heading.className = "pipeline-run-heading";

    const titleGroup = document.createElement("div");
    const title = document.createElement("h3");
    title.textContent = isLatest ? "最近一次執行" : `執行紀錄 #${record.id}`;
    const metadata = document.createElement("p");
    metadata.textContent = `${formatPublishTime(record.started_at)}・總耗時 ${formatDuration(record.duration_ms)}`;
    titleGroup.append(title, metadata);

    const badge = document.createElement("span");
    badge.className = `pipeline-run-badge pipeline-run-badge-${record.status}`;
    badge.textContent = record.status === "success" ? "成功" : "失敗";
    heading.append(titleGroup, badge);

    const stepList = document.createElement("ul");
    stepList.className = "pipeline-step-list";

    for (const stepResult of record.step_results) {
        stepList.appendChild(createPipelineStepItem(stepResult));
    }

    card.append(heading, stepList);

    if (record.status === "failure") {
        const failedStep = record.step_results.find(
            (stepResult) => stepResult.step === record.failed_step,
        );
        const errorMessage = document.createElement("p");
        errorMessage.className = "pipeline-run-error";
        const failedLabel = failedStep ? failedStep.label : record.failed_step;
        errorMessage.textContent = `失敗步驟：${failedLabel || "未知"}。${record.error_message || "沒有錯誤訊息。"}`;
        card.appendChild(errorMessage);
    }

    return card;
}


function createPipelineStepItem(stepResult) {
    const item = document.createElement("li");
    item.className = `pipeline-step pipeline-step-${stepResult.status}`;

    const name = document.createElement("span");
    name.className = "pipeline-step-name";
    name.textContent = stepResult.label;

    const status = document.createElement("span");
    status.className = "pipeline-step-status";
    status.textContent = formatPipelineStepStatus(stepResult);
    item.append(name, status);
    return item;
}


function formatPipelineStepStatus(stepResult) {
    if (stepResult.status === "pending") {
        return "未執行";
    }

    const statusLabel = stepResult.status === "success" ? "成功" : "失敗";
    return `${statusLabel}・${formatDuration(Number(stepResult.duration_ms))}`;
}


function formatDuration(durationMs) {
    if (durationMs < 1000) {
        return `${durationMs} ms`;
    }

    return `${(durationMs / 1000).toFixed(1)} 秒`;
}


function showPipelineRunsError(message) {
    pipelineRunsList.replaceChildren();
    const errorMessage = document.createElement("p");
    errorMessage.className = "pipeline-runs-empty error-message";
    errorMessage.textContent = "Pipeline 執行紀錄暫時無法顯示。";
    pipelineRunsList.appendChild(errorMessage);
    pipelineHistoryMessage.textContent = message;
    pipelineHistoryMessage.classList.add("error-message");
}


function keywordRecordsToSeries(records) {
    const topKeywords = records.slice(0, KEYWORD_CHART_LIMIT);
    const labels = [];
    const values = [];

    for (const record of topKeywords) {
        if (!record || typeof record !== "object") {
            throw new Error("keywords 包含無效資料。");
        }

        const count = Number(record.count);

        if (!record.keyword || !Number.isFinite(count) || count < 0) {
            throw new Error("keywords 的 keyword 或 count 格式不正確。");
        }

        labels.push(String(record.keyword));
        values.push(count);
    }

    return { labels, values };
}


function validateChartSeries(series, name) {
    if (
        !series
        || !Array.isArray(series.labels)
        || !Array.isArray(series.values)
        || series.labels.length !== series.values.length
    ) {
        throw new Error(`${name} 的 labels 與 values 格式不正確。`);
    }

    const labels = series.labels.map((label) => String(label));
    const values = series.values.map((value) => Number(value));

    if (values.some((value) => !Number.isFinite(value) || value < 0)) {
        throw new Error(`${name} 包含無效的統計數值。`);
    }

    return { labels, values };
}


function hasChartValues(series) {
    return series.values.some((value) => value > 0);
}


function renderCharts(chartData) {
    if (typeof Chart === "undefined") {
        showChartError("圖表套件載入失敗，請確認網路連線後重新整理頁面。");
        return;
    }

    const chartDefinitions = [
        {
            canvasId: "source-chart",
            series: chartData.sources,
            type: "doughnut",
            label: "文章數",
            colors: ["#0b6e69", "#2b8c82", "#75d2c8", "#c5ebe6", "#64748b"],
        },
        {
            canvasId: "category-chart",
            series: chartData.categories,
            type: "bar",
            label: "文章數",
            colors: ["#0b6e69"],
        },
        {
            canvasId: "keyword-chart",
            series: chartData.keywords,
            type: "bar",
            label: "標題出現次數",
            colors: ["#c17c28"],
            horizontal: true,
        },
    ];

    let renderedCount = 0;

    for (const definition of chartDefinitions) {
        if (hasChartValues(definition.series)) {
            createChart(definition);
            renderedCount += 1;
        } else {
            showEmptyChart(definition.canvasId, "目前沒有足夠的新聞資料可產生圖表。");
        }
    }

    chartStatusMessage.textContent = renderedCount === chartDefinitions.length
        ? "統計資料已更新"
        : `已顯示 ${renderedCount} / ${chartDefinitions.length} 張圖表`;
}


function createChart({ canvasId, series, type, label, colors, horizontal = false }) {
    const canvas = document.querySelector(`#${canvasId}`);
    canvas.setAttribute(
        "aria-label",
        series.labels.map((item, index) => `${item} ${series.values[index]} 次`).join("、"),
    );

    const options = {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
            legend: {
                display: type === "doughnut",
                position: "bottom",
                labels: { boxWidth: 12, padding: 18 },
            },
            tooltip: {
                callbacks: {
                    label(context) {
                        const value = type === "doughnut" ? context.parsed : context.raw;
                        return `${context.label}：${value}`;
                    },
                },
            },
        },
    };

    if (type === "bar") {
        options.indexAxis = horizontal ? "y" : "x";
        const valueAxis = horizontal ? "x" : "y";
        options.scales = {
            [valueAxis]: {
                beginAtZero: true,
                ticks: { precision: 0 },
            },
        };
    }

    new Chart(canvas, {
        type,
        data: {
            labels: series.labels,
            datasets: [{
                label,
                data: series.values,
                backgroundColor: colors,
                borderColor: colors,
                borderWidth: type === "doughnut" ? 0 : 1,
                borderRadius: type === "bar" ? 5 : 0,
            }],
        },
        options,
    });
}


function showEmptyChart(canvasId, message) {
    const canvas = document.querySelector(`#${canvasId}`);
    const emptyMessage = canvas.parentElement.querySelector(".chart-empty-message");
    canvas.hidden = true;
    emptyMessage.textContent = message;
    emptyMessage.hidden = false;
}


function showChartError(message) {
    chartStatusMessage.textContent = message;
    chartStatusMessage.classList.add("error-message");

    for (const canvas of document.querySelectorAll(".chart-container canvas")) {
        showEmptyChart(canvas.id, "圖表暫時無法顯示。");
    }
}


function getSourceName(record) {
    if (record.source) {
        return SOURCE_LABELS[record.source] || String(record.source);
    }

    try {
        const hostname = new URL(record.url).hostname.replace(/^www\./, "");
        return hostname;
    } catch (error) {
        return "未知來源";
    }
}


function getCategoryName(record) {
    return record.analysis_category || "未分類";
}


function getCompanies(record) {
    return Array.isArray(record.companies) ? record.companies : [];
}


function getCompanyLabel(company) {
    const name = company.short_name || company.name || "未知公司";
    return company.ticker ? `${name} (${company.ticker})` : String(name);
}


function populateFilters() {
    const sources = new Set();
    const categories = new Set();

    for (const record of newsRecords) {
        sources.add(getSourceName(record));
        categories.add(getCategoryName(record));
    }

    populateSelect(sourceFilter, sources, "全部來源");
    populateSelect(categoryFilter, categories, "全部分類");
    populateCompanyFilter();
}


function populateCompanyFilter() {
    const companiesById = new Map();

    for (const record of newsRecords) {
        for (const company of getCompanies(record)) {
            if (company.company_id !== null && company.company_id !== undefined) {
                companiesById.set(String(company.company_id), company);
            }
        }
    }

    companyFilter.replaceChildren();
    const defaultOption = document.createElement("option");
    defaultOption.value = "";
    defaultOption.textContent = "全部公司";
    companyFilter.appendChild(defaultOption);

    const companies = [...companiesById.values()].sort((first, second) => (
        getCompanyLabel(first).localeCompare(
            getCompanyLabel(second),
            "zh-Hant",
            { numeric: true },
        )
    ));

    for (const company of companies) {
        const option = document.createElement("option");
        option.value = String(company.company_id);
        option.textContent = getCompanyLabel(company);
        companyFilter.appendChild(option);
    }
}


function populateSelect(selectElement, values, defaultLabel) {
    selectElement.replaceChildren();
    const defaultOption = document.createElement("option");
    defaultOption.value = "";
    defaultOption.textContent = defaultLabel;
    selectElement.appendChild(defaultOption);

    const sortedValues = [...values].sort((first, second) => (
        first.localeCompare(second, "zh-Hant")
    ));

    for (const value of sortedValues) {
        const option = document.createElement("option");
        option.value = value;
        option.textContent = value;
        selectElement.appendChild(option);
    }
}


function getFilteredRecords() {
    const query = searchInput.value.trim().toLocaleLowerCase("zh-TW");

    return newsRecords.filter((record) => {
        const sourceName = getSourceName(record);
        const categoryName = getCategoryName(record);
        const companies = getCompanies(record);
        const companyText = companies.flatMap((company) => [
            company.name,
            company.short_name,
            company.ticker,
            company.industry,
        ]);
        const searchableText = [
            record.title,
            sourceName,
            categoryName,
            ...companyText,
        ]
            .map((value) => String(value || "").toLocaleLowerCase("zh-TW"))
            .join(" ");
        const matchesSearch = !query || searchableText.includes(query);
        const matchesSource = !sourceFilter.value || sourceName === sourceFilter.value;
        const matchesCategory = !categoryFilter.value || categoryName === categoryFilter.value;
        const matchesCompany = (
            !companyFilter.value
            || companies.some((company) => (
                String(company.company_id) === companyFilter.value
            ))
        );
        const matchesEvent = (
            !eventGroupFilter
            || record.event_group_id === eventGroupFilter
        );

        return (
            matchesSearch
            && matchesSource
            && matchesCategory
            && matchesCompany
            && matchesEvent
        );
    });
}


function getSortedRecords(records) {
    const sortedRecords = [...records];

    sortedRecords.sort((firstRecord, secondRecord) => {
        const firstValue = getSortValue(firstRecord, sortKey);
        const secondValue = getSortValue(secondRecord, sortKey);
        let comparison = 0;

        if (sortKey === "publish_time") {
            comparison = getTimeValue(firstValue) - getTimeValue(secondValue);
        } else {
            comparison = String(firstValue).localeCompare(
                String(secondValue),
                "zh-Hant",
                { numeric: true, sensitivity: "base" },
            );
        }

        return sortDirection === "desc" ? comparison * -1 : comparison;
    });

    return sortedRecords;
}


function getSortValue(record, key) {
    if (key === "source") {
        return getSourceName(record);
    }

    if (key === "analysis_category") {
        return getCategoryName(record);
    }

    return record[key] ?? "";
}


function getTimeValue(value) {
    if (!value) {
        return 0;
    }

    const timeValue = new Date(value).getTime();
    return Number.isNaN(timeValue) ? 0 : timeValue;
}


function formatPublishTime(value) {
    if (!value) {
        return "未知時間";
    }

    const date = new Date(value);

    if (Number.isNaN(date.getTime())) {
        return "未知時間";
    }

    return new Intl.DateTimeFormat("zh-TW", {
        year: "numeric",
        month: "2-digit",
        day: "2-digit",
        hour: "2-digit",
        minute: "2-digit",
        hour12: false,
    }).format(date);
}


function formatLastUpdated(value) {
    if (!value) {
        return "資料庫最後新增：目前沒有新聞";
    }

    return `資料庫最後新增：${formatPublishTime(value)}`;
}


function createNewsRow(record) {
    const row = document.createElement("tr");

    const titleCell = document.createElement("td");
    titleCell.className = "news-title";
    titleCell.appendChild(createSafeLink(record.url, record.title || "未提供標題"));

    const companies = getCompanies(record);

    if (companies.length > 0) {
        const companyTags = document.createElement("div");
        companyTags.className = "company-tags";

        for (const company of companies) {
            const tag = document.createElement("span");
            tag.className = "company-tag";
            tag.textContent = getCompanyLabel(company);
            companyTags.appendChild(tag);
        }

        titleCell.appendChild(companyTags);
    }

    if (record.event_group_id && Number(record.event_group_size) > 1) {
        const eventButton = document.createElement("button");
        eventButton.className = "event-filter-button";
        eventButton.type = "button";
        eventButton.textContent = `查看同事件 ${record.event_group_size} 篇`;
        eventButton.addEventListener("click", () => {
            searchInput.value = "";
            sourceFilter.value = "";
            categoryFilter.value = "";
            companyFilter.value = "";
            eventGroupFilter = record.event_group_id;
            currentPage = 1;
            renderTable();
        });
        titleCell.appendChild(eventButton);
    }

    const sourceCell = document.createElement("td");
    sourceCell.className = "source-name";
    sourceCell.textContent = getSourceName(record);

    const categoryCell = document.createElement("td");
    categoryCell.className = "category-name";
    const analysisCategory = document.createElement("span");
    analysisCategory.className = "analysis-category";
    analysisCategory.textContent = getCategoryName(record);
    categoryCell.appendChild(analysisCategory);

    if (record.source_category) {
        const sourceCategory = document.createElement("span");
        sourceCategory.className = "source-category";
        sourceCategory.textContent = `${getSourceName(record)}・${record.source_category}`;
        categoryCell.appendChild(sourceCategory);
    }

    const timeCell = document.createElement("td");
    timeCell.className = "publish-time";
    timeCell.textContent = formatPublishTime(record.publish_time);

    row.append(titleCell, sourceCell, categoryCell, timeCell);
    return row;
}


function createSafeLink(value, label) {
    try {
        const url = new URL(value);

        if (url.protocol !== "http:" && url.protocol !== "https:") {
            throw new Error("不支援的 URL protocol");
        }

        const link = document.createElement("a");
        link.href = url.href;
        link.target = "_blank";
        link.rel = "noopener noreferrer";
        link.textContent = label;
        return link;
    } catch (error) {
        const fallbackText = document.createElement("span");
        fallbackText.textContent = label;
        return fallbackText;
    }
}


function renderTable() {
    tableBody.replaceChildren();
    const filteredRecords = getFilteredRecords();
    const sortedRecords = getSortedRecords(filteredRecords);
    const totalPages = Math.max(1, Math.ceil(sortedRecords.length / pageSize));
    currentPage = Math.min(currentPage, totalPages);

    const startIndex = (currentPage - 1) * pageSize;
    const pageRecords = sortedRecords.slice(startIndex, startIndex + pageSize);

    if (pageRecords.length === 0) {
        const row = document.createElement("tr");
        const cell = document.createElement("td");
        cell.className = "empty-message";
        cell.colSpan = 4;
        cell.textContent = "沒有符合目前條件的新聞。";
        row.appendChild(cell);
        tableBody.appendChild(row);
    } else {
        for (const record of pageRecords) {
            tableBody.appendChild(createNewsRow(record));
        }
    }

    updateSortIndicators();
    updatePagination(totalPages);

    const firstNumber = pageRecords.length === 0 ? 0 : startIndex + 1;
    const lastNumber = startIndex + pageRecords.length;
    const eventLabel = eventGroupFilter ? "同事件篩選，" : "";
    statusMessage.textContent = `${eventLabel}顯示 ${firstNumber}–${lastNumber}，篩選結果 ${sortedRecords.length} / ${newsRecords.length} 篇`;
}


function updatePagination(totalPages) {
    pageStatus.textContent = `第 ${currentPage} / ${totalPages} 頁`;
    previousPageButton.disabled = currentPage <= 1;
    nextPageButton.disabled = currentPage >= totalPages;
}


function updateSortIndicators() {
    for (const header of tableHeaders) {
        const indicator = header.querySelector(".sort-indicator");
        const key = header.dataset.key;

        if (key === sortKey) {
            const isAscending = sortDirection === "asc";
            header.setAttribute("aria-sort", isAscending ? "ascending" : "descending");
            indicator.textContent = isAscending ? "↑" : "↓";
        } else {
            header.setAttribute("aria-sort", "none");
            indicator.textContent = "↕";
        }
    }
}


function changeSort(newSortKey) {
    if (sortKey === newSortKey) {
        sortDirection = sortDirection === "asc" ? "desc" : "asc";
    } else {
        sortKey = newSortKey;
        sortDirection = newSortKey === "publish_time" ? "desc" : "asc";
    }

    currentPage = 1;
    renderTable();
}


function clearFilters() {
    searchInput.value = "";
    sourceFilter.value = "";
    categoryFilter.value = "";
    companyFilter.value = "";
    eventGroupFilter = null;
    currentPage = 1;
    renderTable();
}


function showError(message) {
    tableBody.replaceChildren();
    statusMessage.textContent = message;
    statusMessage.classList.add("error-message");
}


for (const header of tableHeaders) {
    const button = header.querySelector(".sort-button");
    button.addEventListener("click", () => {
        changeSort(header.dataset.key);
    });
}

searchInput.addEventListener("input", () => {
    currentPage = 1;
    renderTable();
});

sourceFilter.addEventListener("change", () => {
    currentPage = 1;
    renderTable();
});

categoryFilter.addEventListener("change", () => {
    currentPage = 1;
    renderTable();
});

companyFilter.addEventListener("change", () => {
    currentPage = 1;
    renderTable();
});

pageSizeSelect.addEventListener("change", () => {
    pageSize = Number(pageSizeSelect.value);
    currentPage = 1;
    renderTable();
});

clearFiltersButton.addEventListener("click", clearFilters);

marketCompanySelect.addEventListener("change", loadSelectedCompanyMarketData);
watchlistToggle.addEventListener("click", toggleSelectedCompanyWatchlist);

previousPageButton.addEventListener("click", () => {
    if (currentPage > 1) {
        currentPage -= 1;
        renderTable();
    }
});

nextPageButton.addEventListener("click", () => {
    currentPage += 1;
    renderTable();
});

loadNews();
loadAnalytics();
loadSourceHealth();
loadPipelineRuns();
loadDailyBrief();
loadMarketCompanies();
loadEventMarketObservations();
loadWatchlist().then((loaded) => {
    if (loaded) {
        loadPersonalizedBrief();
    }
});
