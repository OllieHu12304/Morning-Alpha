const { expect, test } = require("@playwright/test");


const newsRecords = Array.from({ length: 12 }, (_, index) => {
    const isCna = index % 2 === 0;

    return {
        source: isCna ? "cna" : "technews",
        source_category: isCna ? "產經證券" : null,
        analysis_category: index % 3 === 0 ? "半導體" : "財經",
        title: index === 0 ? "台積電焦點測試新聞" : `測試新聞 ${index + 1}`,
        publish_time: `2026-08-11T${String(12 - index).padStart(2, "0")}:00:00`,
        url: `https://example.com/news/${index + 1}`,
        event_group_id: null,
        event_group_size: 1,
    };
});

const analyticsPayload = {
    sources: {
        labels: ["中央通訊社", "TechNews 科技新報"],
        values: [6, 6],
    },
    categories: {
        labels: ["半導體", "財經"],
        values: [4, 8],
    },
    keywords: [
        { keyword: "測試新聞", count: 12 },
        { keyword: "台積電", count: 1 },
    ],
    last_updated: "2026-08-11T12:30:00",
};

const sourceHealthPayload = {
    sources: [
        {
            source: "cna",
            status: "success",
            article_count: 8,
            error_message: null,
            last_attempt_at: "2026-08-11T12:35:00",
            last_success_at: "2026-08-11T12:35:00",
        },
        {
            source: "technews",
            status: "failure",
            article_count: 0,
            error_message: "HTTP 503",
            last_attempt_at: "2026-08-11T12:34:00",
            last_success_at: "2026-08-11T10:00:00",
        },
    ],
};


test.beforeEach(async ({ page }) => {
    await page.route("**/api/news", (route) => route.fulfill({
        contentType: "application/json",
        body: JSON.stringify({
            count: newsRecords.length,
            news: newsRecords,
        }),
    }));
    await page.route("**/api/analytics", (route) => route.fulfill({
        contentType: "application/json",
        body: JSON.stringify(analyticsPayload),
    }));
    await page.route("**/api/source-health", (route) => route.fulfill({
        contentType: "application/json",
        body: JSON.stringify(sourceHealthPayload),
    }));
    await page.route("https://cdn.jsdelivr.net/**", (route) => route.fulfill({
        contentType: "application/javascript",
        body: "window.Chart = class { constructor() {} };",
    }));

    await page.goto("/");
});


test("loads Dashboard data from mocked APIs", async ({ page }) => {
    await expect(
        page.getByRole("heading", { name: "科技與財經新聞分析" }),
    ).toBeVisible();
    await expect(page.locator("#news-table-body tr")).toHaveCount(10);
    await expect(page.locator("#status-message")).toContainText(
        "篩選結果 12 / 12 篇",
    );
    await expect(page.locator("#chart-status-message")).toHaveText(
        "統計資料已更新",
    );
    await expect(page.locator("#last-updated")).toContainText(
        "資料庫最後新增：",
    );
    await expect(page.locator(".source-health-card")).toHaveCount(2);
    await expect(page.locator("#source-health-grid")).toContainText("正常");
    await expect(page.locator("#source-health-grid")).toContainText("失敗");
    await expect(page.locator("#source-health-grid")).toContainText("HTTP 503");
});


test("searches and filters news records", async ({ page }) => {
    await page.locator("#news-search").fill("台積電");
    await expect(page.locator("#news-table-body tr")).toHaveCount(1);
    await expect(page.locator("#news-table-body")).toContainText(
        "台積電焦點測試新聞",
    );

    await page.getByRole("button", { name: "清除篩選" }).click();
    await page.locator("#source-filter").selectOption("中央通訊社");
    await expect(page.locator("#news-table-body tr")).toHaveCount(6);
    await expect(page.locator("#status-message")).toContainText(
        "篩選結果 6 / 12 篇",
    );
});


test("moves between Dashboard pages", async ({ page }) => {
    await expect(page.locator("#page-status")).toHaveText("第 1 / 2 頁");

    await page.getByRole("button", { name: "下一頁" }).click();

    await expect(page.locator("#page-status")).toHaveText("第 2 / 2 頁");
    await expect(page.locator("#news-table-body tr")).toHaveCount(2);
});
