const JSON_FILE = "./news.json";

const tableBody = document.querySelector("#news-table-body");
const statusMessage = document.querySelector("#status-message");
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
