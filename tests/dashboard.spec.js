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
            article_count: 6,
            error_message: null,
            last_attempt_at: "2026-08-11T12:35:00",
            last_success_at: "2026-08-11T12:35:00",
        },
        {
            source: "technews",
            status: "failure",
            article_count: 6,
            error_message: "HTTP 503",
            last_attempt_at: "2026-08-11T12:34:00",
            last_success_at: "2026-08-11T10:00:00",
        },
    ],
};

const pipelineRunsPayload = {
    runs: [
        {
            id: 2,
            status: "failure",
            started_at: "2026-08-11T12:40:00",
            finished_at: "2026-08-11T12:40:02",
            duration_ms: 2000,
            failed_step: "export_news",
            step_results: [
                {
                    step: "collect_news",
                    label: "爬取、整理並儲存新聞",
                    status: "success",
                    duration_ms: 1500,
                    summary: { inserted_news: 5 },
                },
                {
                    step: "export_news",
                    label: "匯出 Dashboard 新聞資料",
                    status: "failure",
                    duration_ms: 500,
                    summary: null,
                },
                {
                    step: "chart_data",
                    label: "產生 Dashboard 圖表資料",
                    status: "pending",
                    duration_ms: null,
                    summary: null,
                },
                {
                    step: "keywords",
                    label: "產生 Top 20 關鍵字資料",
                    status: "pending",
                    duration_ms: null,
                    summary: null,
                },
            ],
            error_message: "JSON 格式錯誤",
        },
    ],
};

const dailyBriefPayload = {
    brief: {
        brief_date: "2026-08-12",
        window_start: "2026-08-11T07:00:00+08:00",
        window_end: "2026-08-12T07:00:00+08:00",
        article_count: 12,
        summary: "本期共收錄 12 篇新聞，主要來源為中央通訊社。",
        sources: [{ name: "中央通訊社", count: 6 }],
        categories: [{ name: "財經", count: 8 }],
        keywords: [{ name: "台積電", count: 3 }],
        highlights: [{
            title: "台積電焦點測試新聞",
            url: "https://example.com/news/1",
            selection_reason: "同事件共有 2 篇報導",
        }],
        limitations: ["本摘要不構成投資建議。"],
    },
};

const marketCompaniesPayload = {
    companies: [
        {
            company_id: 8,
            name: "台灣積體電路製造股份有限公司",
            short_name: "台積電",
            ticker: "2330",
            exchange: "TWSE",
            has_market_prices: true,
            has_financial_metrics: true,
        },
        {
            company_id: 9,
            name: "國巨股份有限公司",
            short_name: "國巨",
            ticker: "2327",
            exchange: "TWSE",
            has_market_prices: true,
            has_financial_metrics: true,
        },
    ],
};

let trackedCompanies = [];
let pipelineStarted = false;
let pipelineStatusChecks = 0;
let newsRequestCount = 0;
let marketPriceRequestCompanyIds = [];
let financialRequestCompanyIds = [];


function createPersonalizedBriefPayload() {
    const hasWatchlist = trackedCompanies.length > 0;

    return {
        brief: {
            ...dailyBriefPayload.brief,
            article_count: hasWatchlist ? 1 : 0,
            watchlist_count: trackedCompanies.length,
            watched_companies: trackedCompanies,
            summary: hasWatchlist
                ? `目前追蹤 ${trackedCompanies.length} 家公司，找到 1 篇近期相關新聞。`
                : "尚未加入追蹤公司，請先搜尋公司並加入追蹤。",
            highlights: hasWatchlist
                ? dailyBriefPayload.brief.highlights
                : [],
        },
    };
}


test.beforeEach(async ({ page }) => {
    trackedCompanies = [];
    pipelineStarted = false;
    pipelineStatusChecks = 0;
    newsRequestCount = 0;
    marketPriceRequestCompanyIds = [];
    financialRequestCompanyIds = [];
    await page.route("**/api/news", (route) => route.fulfill({
        contentType: "application/json",
        body: JSON.stringify({
            count: newsRecords.length,
            news: newsRecords,
        }),
    }).then(() => {
        newsRequestCount += 1;
    }));
    await page.route("**/api/analytics", (route) => route.fulfill({
        contentType: "application/json",
        body: JSON.stringify(analyticsPayload),
    }));
    await page.route("**/api/source-health", (route) => route.fulfill({
        contentType: "application/json",
        body: JSON.stringify(sourceHealthPayload),
    }));
    await page.route("**/api/pipeline-runs", (route) => route.fulfill({
        contentType: "application/json",
        body: JSON.stringify(pipelineRunsPayload),
    }));
    await page.route("**/api/pipeline/status", (route) => {
        let status = "idle";

        if (pipelineStarted) {
            pipelineStatusChecks += 1;
            status = pipelineStatusChecks === 1 ? "running" : "success";
        }

        return route.fulfill({
            contentType: "application/json",
            body: JSON.stringify({
                pipeline: {
                    status,
                    started_at: pipelineStarted
                        ? "2026-08-12T04:00:00+00:00"
                        : null,
                    finished_at: status === "success"
                        ? "2026-08-12T04:01:00+00:00"
                        : null,
                    exit_code: status === "success" ? 0 : null,
                },
            }),
        });
    });
    await page.route("**/api/pipeline/run", (route) => {
        pipelineStarted = true;
        pipelineStatusChecks = 0;

        return route.fulfill({
            status: 202,
            contentType: "application/json",
            body: JSON.stringify({
                pipeline: {
                    status: "running",
                    started_at: "2026-08-12T04:00:00+00:00",
                    finished_at: null,
                    exit_code: null,
                },
            }),
        });
    });
    await page.route("**/api/daily-briefs/latest", (route) => route.fulfill({
        contentType: "application/json",
        body: JSON.stringify(dailyBriefPayload),
    }));
    await page.route("**/api/market-companies", (route) => route.fulfill({
        contentType: "application/json",
        body: JSON.stringify(marketCompaniesPayload),
    }));
    await page.route(/\/api\/companies\/\d+\/market-prices$/, (route) => {
        const urlParts = route.request().url().split("/");
        marketPriceRequestCompanyIds.push(Number(urlParts.at(-2)));
        return route.fulfill({
            contentType: "application/json",
            body: JSON.stringify({
                prices: [{
                    trade_date: "2026-08-13",
                    close_price: 885,
                    price_change: 5,
                    fetched_at: "2026-08-14T07:06:13+00:00",
                }],
                market_status: {
                    status: "pending_or_closed",
                    latest_trade_date: "2026-08-13",
                    expected_trade_date: "2026-08-14",
                },
            }),
        });
    });
    await page.route(/\/api\/companies\/\d+\/financial-metrics$/, (route) => {
        const urlParts = route.request().url().split("/");
        financialRequestCompanyIds.push(Number(urlParts.at(-2)));
        return route.fulfill({
            contentType: "application/json",
            body: JSON.stringify({ metrics: [] }),
        });
    });
    await page.route("**/api/event-market-observations", (route) => route.fulfill({
        contentType: "application/json",
        body: JSON.stringify({
            analysis_type: "observational",
            methodology: "固定測試方法",
            limitations: ["測試資料不代表因果。"],
            observations: [],
            readiness: {
                candidate_count: 1,
                price_date_count: 1,
                earliest_trade_date: "2026-08-11",
                latest_trade_date: "2026-08-11",
                observation_count: 0,
            },
        }),
    }));
    await page.route(/\/api\/watchlist(?:\/\d+)?$/, async (route) => {
        const method = route.request().method();

        if (method === "GET") {
            await route.fulfill({
                contentType: "application/json",
                body: JSON.stringify({ items: trackedCompanies }),
            });
            return;
        }

        const companyId = Number(route.request().url().split("/").pop());
        const company = marketCompaniesPayload.companies.find(
            (record) => record.company_id === companyId,
        );

        if (method === "POST") {
            if (company && !trackedCompanies.some(
                (record) => record.company_id === companyId,
            )) {
                trackedCompanies.push(company);
            }
        } else if (method === "DELETE") {
            trackedCompanies = trackedCompanies.filter(
                (record) => record.company_id !== companyId,
            );
        }

        await route.fulfill({
            contentType: "application/json",
            body: JSON.stringify({ company_id: companyId }),
        });
    });
    await page.route("**/api/personalized-brief", (route) => route.fulfill({
        contentType: "application/json",
        body: JSON.stringify(createPersonalizedBriefPayload()),
    }));
    await page.route("https://cdn.jsdelivr.net/**", (route) => route.fulfill({
        contentType: "application/javascript",
        body: `
            window.analyticsChartCreateCount = 0;
            window.analyticsChartDestroyCount = 0;
            window.Chart = class {
                constructor() {
                    window.analyticsChartCreateCount += 1;
                }

                destroy() {
                    window.analyticsChartDestroyCount += 1;
                }
            };
        `,
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
    await expect(page.locator("#source-health-grid")).toContainText(
        "新聞列表篇數",
    );
    await expect(page.locator(".pipeline-run-card")).toHaveCount(1);
    await expect(page.locator("#pipeline-runs-list")).toContainText("最近一次執行");
    await expect(page.locator("#pipeline-runs-list")).toContainText("JSON 格式錯誤");
    await expect(page.locator(".pipeline-step-pending")).toHaveCount(2);
    await expect(page.locator("#daily-brief-content")).toContainText(
        "本期共收錄 12 篇新聞",
    );
    await expect(page.locator("#daily-brief-content")).toContainText(
        "台積電焦點測試新聞",
    );
    await expect(page.locator("#daily-brief-message")).toHaveText(
        "收錄 12 篇新聞",
    );
    await expect(page.locator("#personalized-brief-result")).toContainText(
        "尚未加入追蹤公司",
    );
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


test("runs Pipeline and refreshes Dashboard data", async ({ page }) => {
    const runButton = page.locator("#pipeline-run-button");

    await expect(runButton).toBeEnabled();
    await runButton.click();

    await expect(page.locator("#pipeline-control-message")).toContainText(
        "背景執行",
    );
    await expect(runButton).toBeDisabled();
    await expect(page.locator("#pipeline-control-message")).toHaveText(
        "資料更新完成，Dashboard 已重新載入。",
        { timeout: 5000 },
    );
    await expect.poll(() => newsRequestCount).toBeGreaterThanOrEqual(2);
    await expect.poll(() => page.evaluate(
        () => window.analyticsChartDestroyCount,
    )).toBeGreaterThanOrEqual(3);
});


test("adds and removes a company from the local watchlist", async ({ page }) => {
    await page.locator("#market-company-search").fill("台積電");
    await page.getByRole("button", { name: "瀏覽 2330 台積電" }).click();
    await expect(page.locator("#watchlist-toggle")).toHaveText("加入追蹤");

    await page.locator("#watchlist-toggle").click();

    await expect(page.locator("#watchlist-toggle")).toHaveText("移除追蹤");
    await expect(page.locator("#watchlist-items")).toContainText("2330 台積電");
    await expect(page.locator("#personalized-brief-result")).toContainText(
        "找到 1 篇近期相關新聞",
    );

    await page.locator("#watchlist-toggle").click();

    await expect(page.locator("#watchlist-toggle")).toHaveText("加入追蹤");
    await expect(page.locator("#watchlist-items")).toContainText("尚未追蹤公司");
});


test("searches market data and switches between watchlist companies", async ({ page }) => {
    const marketSearch = page.locator("#market-company-search");
    const shortcuts = page.locator("#market-watchlist-shortcuts");

    await marketSearch.fill("國巨");
    await expect(page.locator("#market-company-search-results")).toBeVisible();
    await page.getByRole("button", { name: "瀏覽 2327 國巨" }).click();

    await expect(marketSearch).toHaveValue("2327 國巨");
    await expect(page.locator("#market-company-search-message")).toHaveText(
        "目前顯示 2327 國巨",
    );
    await expect(page.locator("#company-market-message")).toContainText(
        "2026-08-14 行情尚未發布或當日休市",
    );
    await expect.poll(() => marketPriceRequestCompanyIds).toContain(9);
    await expect.poll(() => financialRequestCompanyIds).toContain(9);

    await page.locator("#watchlist-toggle").click();
    await expect(shortcuts).toContainText("2327 國巨");

    await page.locator("#watchlist-company-search").fill("台積電");
    await page.getByRole("button", { name: "加入 2330 台積電" }).click();
    await expect(shortcuts.locator(".market-watchlist-button")).toHaveCount(2);

    const tsmcShortcut = page.getByRole("button", {
        name: "瀏覽追蹤公司 2330 台積電",
    });
    await tsmcShortcut.click();

    await expect(marketSearch).toHaveValue("2330 台積電");
    await expect(tsmcShortcut).toHaveAttribute("aria-pressed", "true");
    await expect.poll(() => marketPriceRequestCompanyIds).toContain(8);
    await expect.poll(() => financialRequestCompanyIds).toContain(8);

    const yageoShortcut = page.getByRole("button", {
        name: "瀏覽追蹤公司 2327 國巨",
    });
    await yageoShortcut.click();
    await expect(marketSearch).toHaveValue("2327 國巨");
    await expect(yageoShortcut).toHaveAttribute("aria-pressed", "true");
});


test("searches for a company and manages it from the watchlist", async ({ page }) => {
    const searchInput = page.locator("#watchlist-company-search");

    await searchInput.fill("國巨");
    await expect(page.locator("#watchlist-search-results")).toBeVisible();
    await expect(page.locator("#watchlist-search-results li")).toHaveCount(1);

    await page.getByRole("button", { name: "加入 2327 國巨" }).click();

    await expect(page.locator("#watchlist-items")).toContainText("2327 國巨");
    await expect(page.locator("#watchlist-search-message")).toHaveText(
        "已加入 2327 國巨",
    );

    await page.getByRole("button", { name: "移除 2327 國巨" }).click();

    await expect(page.locator("#watchlist-items")).toContainText("尚未追蹤公司");
    await expect(page.locator("#watchlist-search-message")).toHaveText(
        "已移除 2327 國巨",
    );
});
