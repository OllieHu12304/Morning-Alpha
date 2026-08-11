const { defineConfig } = require("@playwright/test");


module.exports = defineConfig({
    testDir: "./tests",
    testMatch: "dashboard.spec.js",
    use: {
        baseURL: "http://127.0.0.1:5050",
        trace: "retain-on-failure",
    },
    webServer: {
        command: "./.venv/bin/python src/api.py",
        url: "http://127.0.0.1:5050/api/health",
        reuseExistingServer: !process.env.CI,
        timeout: 120000,
    },
});
