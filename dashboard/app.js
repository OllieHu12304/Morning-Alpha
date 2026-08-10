const JSON_FILE = "./news.json";
const CHART_DATA_FILE = "./chart_data.json";

const tableBody = document.querySelector("#news-table-body");
const statusMessage = document.querySelector("#status-message");
const chartStatusMessage = document.querySelector("#chart-status-message");
const tableHeaders = document.querySelectorAll("th[data-key]");

let newsRecords = [];
let sortKey = "publish_time";
let sortDirection = "desc";


async function loadNews() {
    try {
        const response = await fetch(JSON_FILE, { cache: "no-store" });

        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }

        const data = await response.json();

        if (!Array.isArray(data)) {
            throw new Error("JSON 最外層必須是 array。");
        }

        newsRecords = data;
        renderTable();
    } catch (error) {
        showError(`無法載入 news.json：${error.message}`);
    }
}


async function loadChartData() {
    try {
        const response = await fetch(CHART_DATA_FILE, { cache: "no-store" });

        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }

        const data = await response.json();
        const chartData = {
            sources: validateChartSeries(data.sources, "sources"),
            categories: validateChartSeries(data.categories, "categories"),
            keywords: validateChartSeries(data.keywords, "keywords"),
        };

        renderCharts(chartData);
    } catch (error) {
        showChartError(`無法載入 chart_data.json：${error.message}`);
    }
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
            label: "標題出現篇數",
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
        series.labels.map((item, index) => `${item} ${series.values[index]} 篇`).join("、"),
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
                        return `${context.label}：${value} 篇`;
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


function getSortedRecords() {
    const sortedRecords = [...newsRecords];

    sortedRecords.sort((firstRecord, secondRecord) => {
        const firstValue = firstRecord[sortKey] ?? "";
        const secondValue = secondRecord[sortKey] ?? "";
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

        if (sortDirection === "desc") {
            return comparison * -1;
        }

        return comparison;
    });

    return sortedRecords;
}


function getTimeValue(value) {
    if (!value) {
        return 0;
    }

    const timeValue = new Date(value).getTime();

    if (Number.isNaN(timeValue)) {
        return 0;
    }

    return timeValue;
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


function createNewsRow(record) {
    const row = document.createElement("tr");

    const titleCell = document.createElement("td");
    titleCell.className = "news-title";
    titleCell.textContent = record.title || "未提供標題";

    const timeCell = document.createElement("td");
    timeCell.className = "publish-time";
    timeCell.textContent = formatPublishTime(record.publish_time);

    const urlCell = document.createElement("td");
    const link = createSafeLink(record.url);
    urlCell.appendChild(link);

    row.append(titleCell, timeCell, urlCell);
    return row;
}


function createSafeLink(value) {
    const text = value || "未提供 URL";

    try {
        const url = new URL(text);

        if (url.protocol !== "http:" && url.protocol !== "https:") {
            throw new Error("不支援的 URL protocol");
        }

        const link = document.createElement("a");
        link.className = "news-link";
        link.href = url.href;
        link.target = "_blank";
        link.rel = "noopener noreferrer";
        link.textContent = text;
        return link;
    } catch (error) {
        const fallbackText = document.createElement("span");
        fallbackText.textContent = text;
        return fallbackText;
    }
}


function renderTable() {
    tableBody.replaceChildren();
    const sortedRecords = getSortedRecords();

    if (sortedRecords.length === 0) {
        const row = document.createElement("tr");
        const cell = document.createElement("td");
        cell.className = "empty-message";
        cell.colSpan = 3;
        cell.textContent = "目前沒有可顯示的新聞資料。";
        row.appendChild(cell);
        tableBody.appendChild(row);
    } else {
        for (const record of sortedRecords) {
            tableBody.appendChild(createNewsRow(record));
        }
    }

    updateSortIndicators();
    statusMessage.textContent = `共 ${sortedRecords.length} 篇新聞`;
}


function updateSortIndicators() {
    for (const header of tableHeaders) {
        const indicator = header.querySelector(".sort-indicator");
        const key = header.dataset.key;

        if (key === sortKey) {
            const isAscending = sortDirection === "asc";
            header.setAttribute(
                "aria-sort",
                isAscending ? "ascending" : "descending",
            );
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


loadNews();
loadChartData();
