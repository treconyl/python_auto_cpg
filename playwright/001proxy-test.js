import { chromium } from "@playwright/test";

const email = process.env.PROXY_EMAIL || "user@gmail.com";
const password = process.env.PROXY_PASSWORD || "password";

const waitForAny = async (page, selectors, options = {}) => {
    for (const selector of selectors) {
        const locator = page.locator(selector);
        try {
            await locator.first().waitFor({ timeout: 5000, ...options });
            return locator.first();
        } catch {
            // try next selector
        }
    }
    return null;
};

async function run() {
    const browser = await chromium.launch({ headless: false });
    const context = await browser.newContext();
    const page = await context.newPage();

    await page.goto("https://001proxy.com/", {
        waitUntil: "load",
        timeout: 60000,
    });

    const loginTrigger = await waitForAny(page, [
        'text="Khu vực khách hàng"',
        'text="Đăng nhập"',
        'a:has-text("Đăng nhập")',
        'a:has-text("Khu vực khách hàng")',
        'button:has-text("Đăng nhập")',
        'button:has-text("Khu vực khách hàng")',
    ]);

    if (loginTrigger) {
        await loginTrigger.click();
    }

    const emailInput = await waitForAny(page, [
        'input[placeholder="Nhập email của bạn"]',
        'input[placeholder="Email"]',
        'input[type="email"]',
        'input[name="email"]',
    ]);

    const passwordInput = await waitForAny(page, [
        'input[placeholder="Nhập mật khẩu"]',
        'input[type="password"]',
        'input[name="password"]',
    ]);

    if (!emailInput || !passwordInput) {
        throw new Error("Khong tim thay form dang nhap.");
    }

    await emailInput.fill(email);
    await passwordInput.fill(password);

    await page.waitForTimeout(3000);
    await context.close();
    await browser.close();
}

run().catch((error) => {
    console.error("[001Proxy Test] Loi:", error);
    process.exit(1);
});
