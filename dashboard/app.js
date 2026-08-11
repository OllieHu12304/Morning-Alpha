const NEWS_API = "/api/news";
const ANALYTICS_API = "/api/analytics";
const KEYWORD_CHART_LIMIT = 10;

const SOURCE_LABELS = {
    cna: "中央通訊社",
    technews: "TechNews 科技新報",
};

const tableBody = document.querySelector("#news-table-body");
const statusMessage = document.querySelector("#status-message");
const chartStatusMessage = document.querySelector("#chart-status-message");
const lastUpdatedMessage = document.querySelector("#last-updated");
const searchInput = document.querySelector("#news-search");
const sourceFilter = document.querySelector("#source-filter");
const categoryFilter = document.querySelector("#category-filter");
const pageSizeSelect = document.querySelector("#page-size");
const clearFiltersButton = document.querySelector("#clear-filters");
const previousPageButton = document.querySelector("#previous-page");
const nextPageButton = document.querySelector("#next-page");
const pageStatus = document.querySelector("#page-status");
const tableHeaders = document.querySelectorAll("th[data-key]");

let newsRecords = [];
let sortKey = "publish_time";
let sortDirection = "desc";
let currentPage = 1;
let pageSize = Number(pageSizeSelect.value);
let eventGroupFilter = null;


async function fetchJson(url) {
    const response = await fetch(url, { cache: "no-store" });

    if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
    }

    return response.json();
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


function populateFilters() {
    const sources = new Set();
    const categories = new Set();

    for (const record of newsRecords) {
        sources.add(getSourceName(record));
        categories.add(getCategoryName(record));
    }

    populateSelect(sourceFilter, sources, "全部來源");
    populateSelect(categoryFilter, categories, "全部分類");
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
        const searchableText = [record.title, sourceName, categoryName]
            .map((value) => String(value || "").toLocaleLowerCase("zh-TW"))
            .join(" ");
        const matchesSearch = !query || searchableText.includes(query);
        const matchesSource = !sourceFilter.value || sourceName === sourceFilter.value;
        const matchesCategory = !categoryFilter.value || categoryName === categoryFilter.value;
        const matchesEvent = (
            !eventGroupFilter
            || record.event_group_id === eventGroupFilter
        );

        return matchesSearch && matchesSource && matchesCategory && matchesEvent;
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

    if (record.event_group_id && Number(record.event_group_size) > 1) {
        const eventButton = document.createElement("button");
        eventButton.className = "event-filter-button";
        eventButton.type = "button";
        eventButton.textContent = `查看同事件 ${record.event_group_size} 篇`;
        eventButton.addEventListener("click", () => {
            searchInput.value = "";
            sourceFilter.value = "";
            categoryFilter.value = "";
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

pageSizeSelect.addEventListener("change", () => {
    pageSize = Number(pageSizeSelect.value);
    currentPage = 1;
    renderTable();
});

clearFiltersButton.addEventListener("click", clearFilters);

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
