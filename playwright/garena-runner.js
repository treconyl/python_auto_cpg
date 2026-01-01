import fs from "node:fs";
import path from "node:path";
import { chromium } from "@playwright/test";
import "dotenv/config";

const username = process.env.GARENA_USERNAME;
const accountId = process.env.GARENA_ACCOUNT_ID || username;
const password = process.env.GARENA_PASSWORD;
const newPassword = process.env.GARENA_NEW_PASSWORD || "Password#2025";
const headless = process.env.PLAYWRIGHT_HEADLESS === "true";

if (!username || !password) {
    console.error(
        "Thiếu GARENA_USERNAME hoặc GARENA_PASSWORD trong môi trường."
    );
    process.exit(1);
}

if (!passwordMeetsPolicy(newPassword)) {
    console.error(
        "[Garena] Mật khẩu mới không hợp lệ. Yêu cầu 8-16 ký tự và bao gồm chữ hoa, chữ thường, chữ số và ký tự đặc biệt."
    );
    process.exit(1);
}

const loginInputSelector =
    'input[placeholder="Tài khoản Garena, Email hoặc số điện thoại"]';
const passwordInputSelector = 'input[placeholder="Mật khẩu"]';
const oldPasswordSelector = "#J-form-curpwd";
const newPasswordSelector = "#J-form-newpwd";
const confirmPasswordSelector = 'input[placeholder="Xác nhận Mật khẩu mới"]';
const submitButtonRole = { name: /thay/i };

const randomInt = (min, max) =>
    Math.floor(Math.random() * (max - min + 1)) + min;
const humanPause = (min = 350, max = 1100) =>
    new Promise((resolve) => setTimeout(resolve, randomInt(min, max)));

function createSeededRandom(seedString) {
    let seed = 0;
    for (const ch of seedString) {
        seed = (seed * 31 + ch.charCodeAt(0)) >>> 0;
    }

    return function random() {
        seed ^= seed << 13;
        seed ^= seed >>> 17;
        seed ^= seed << 5;
        return (seed >>> 0) / 0xffffffff;
    };
}

function pickRandom(rand, arr) {
    return arr[Math.floor(rand() * arr.length)];
}

function generateRealisticBrowserProfile(seedString = `${Date.now()}`) {
    const rand = createSeededRandom(seedString);

    const windowsProfiles = [
        {
            osName: "Windows 10",
            osToken: "Windows NT 10.0; Win64; x64",
            platform: "Win32",
            hardwareConcurrency: 4,
            maxTouchPoints: 0,
        },
        {
            osName: "Windows 11",
            osToken: "Windows NT 10.0; Win64; x64",
            platform: "Win32",
            hardwareConcurrency: 8,
            maxTouchPoints: 0,
        },
        {
            osName: "Windows 10 (laptop)",
            osToken: "Windows NT 10.0; Win64; x64",
            platform: "Win32",
            hardwareConcurrency: 4,
            maxTouchPoints: 0,
        },
    ];

    const chromeVersions = [
        "122.0.0.0",
        "123.0.0.0",
        "124.0.0.0",
        "125.0.0.0",
        "126.0.0.0",
    ];

    const viewports = [
        { width: 1366, height: 768 },
        { width: 1536, height: 864 },
        { width: 1600, height: 900 },
        { width: 1920, height: 1080 },
        { width: 1440, height: 900 },
    ];

    const locales = ["vi-VN", "vi-VN", "vi-VN", "en-US", "en-GB"];
    const timezones = ["Asia/Ho_Chi_Minh", "Asia/Bangkok", "Asia/Singapore"];

    const profileBase = pickRandom(rand, windowsProfiles);
    const viewport = pickRandom(rand, viewports);
    const chromeVersion = pickRandom(rand, chromeVersions);
    const locale = pickRandom(rand, locales);
    const timezoneId = pickRandom(rand, timezones);
    const deviceScaleFactor = rand() < 0.7 ? 1 : 1.25;

    const userAgent = [
        "Mozilla/5.0",
        `(${profileBase.osToken})`,
        "AppleWebKit/537.36 (KHTML, like Gecko)",
        `Chrome/${chromeVersion}`,
        "Safari/537.36",
    ].join(" ");

    const navigatorOverrides = {
        platform: profileBase.platform,
        language: locale,
        languages: [locale, "en-US"],
        hardwareConcurrency: profileBase.hardwareConcurrency,
        maxTouchPoints: profileBase.maxTouchPoints,
        deviceMemory: rand() < 0.5 ? 8 : 16,
    };

    const screen = {
        width: viewport.width,
        height: viewport.height,
        availWidth: viewport.width,
        availHeight: viewport.height - 40,
        colorDepth: 24,
        pixelDepth: 24,
    };

    return {
        contextOptions: {
            userAgent,
            viewport,
            deviceScaleFactor,
            locale,
            timezoneId,
        },
        navigatorOverrides,
        screen,
        meta: {
            seedString,
            osName: profileBase.osName,
            chromeVersion,
        },
    };
}

async function humanMouseMove(page) {
    const steps = randomInt(5, 15);
    for (let i = 0; i < steps; i++) {
        await page.mouse.move(randomInt(0, 1200), randomInt(0, 600), {
            steps: randomInt(2, 5),
        });
        await humanPause(80, 180);
    }
}

async function humanScroll(page, distance = 600) {
    const parts = randomInt(2, 4);
    const chunk = Math.ceil(distance / parts);
    for (let i = 0; i < parts; i++) {
        await page.mouse.wheel(0, chunk + randomInt(-40, 40));
        await humanPause(120, 240);
    }
}

async function humanType(page, selector, text, options = { allowTypos: true }) {
    await page.click(selector);
    await humanPause(180, 420);

    for (let i = 0; i < text.length; i++) {
        const char = text[i];

        if (options.allowTypos && i > 1 && randomInt(1, 18) === 1) {
            await page.keyboard.press("Backspace");
            await humanPause(70, 180);
        }

        await page.keyboard.type(char, { delay: randomInt(90, 230) });
    }
}

async function typeExact(page, selector, text) {
    const input = page.locator(selector);
    await input.click();
    const currentValue = await input.inputValue();
    if (currentValue) {
        await page.keyboard.press("End");
        for (let i = 0; i < currentValue.length; i++) {
            await page.keyboard.press("Backspace");
            await humanPause(60, 140);
        }
    }
    await humanPause(120, 240);
    await page.keyboard.type(text, { delay: randomInt(90, 230) });
}

async function humanHover(page, locator) {
    const box = await locator.boundingBox();
    if (!box) {
        return;
    }

    const offsetX = randomInt(
        Math.floor(box.width * 0.2),
        Math.floor(box.width * 0.8)
    );
    const offsetY = randomInt(
        Math.floor(box.height * 0.2),
        Math.floor(box.height * 0.8)
    );

    await page.mouse.move(box.x + offsetX, box.y + offsetY, {
        steps: randomInt(3, 6),
    });
    await humanPause(200, 520);
}

async function ensureAccountSafe(page) {
    await failIfDanger(page);
}

async function failIfDanger(page) {
    const dangerSelectors = ["text=Tài khoản của bạn đang gặp nguy hiểm"];

    for (const selector of dangerSelectors) {
        const warning = page.locator(selector).first();
        if (await warning.isVisible({ timeout: 300 })) {
            throw new Error(
                "[Garena] Garena báo tài khoản nguy hiểm, dừng lại."
            );
        }
    }

    const regexWarning = page.locator("text=/nguy\\s*h(i|í)ểm/i").first();
    if (await regexWarning.isVisible({ timeout: 300 })) {
        throw new Error("[Garena] Garena báo tài khoản nguy hiểm, dừng lại.");
    }
}

/**
 * ====== HELPER FLOW CHO ACCOUNT CENTER ======
 */

async function clickTopTab(page, label) {
    const tab = page.locator(`text=${label}`).first();
    if (await tab.isVisible()) {
        await humanHover(page, tab);
        await tab.click();
        await humanPause(800, 1500);
    }
}

async function openSecuritySubMenu(page, label) {
    const item = page.locator(`text=${label}`).first();
    if (await item.isVisible()) {
        await humanHover(page, item);
        await item.click();
        await humanPause(900, 1600);
    }
}

async function randomHomeInteractions(page) {
    if (randomInt(1, 3) === 1) {
        await humanScroll(page, randomInt(220, 420));
    }
    if (randomInt(1, 3) === 1) {
        const moreLinks = page.locator("text=Xem thêm");
        const count = await moreLinks.count();
        if (count > 0) {
            const idx = randomInt(0, count - 1);
            const link = moreLinks.nth(idx);
            await humanHover(page, link);
            await link.click({ timeout: 4000 });
            await humanPause(900, 1600);
            if (randomInt(1, 3) === 1) {
                await humanScroll(page, randomInt(180, 360));
            }
        }
    }
    await humanMouseMove(page);
}

async function randomFaqInteractions(page) {
    if (randomInt(1, 2) === 1) {
        await humanScroll(page, randomInt(260, 520));
    }
    await humanPause(800, 1500);

    if (randomInt(1, 3) === 1) {
        const questions = page.locator("text=Q:");
        const count = await questions.count();
        if (count > 0) {
            const idx = randomInt(0, count - 1);
            const q = questions.nth(idx);
            await humanHover(page, q);
            await q.click({ timeout: 3000 }).catch(() => {});
            await humanPause(700, 1300);
        }
    }

    if (randomInt(1, 3) === 1) {
        await humanScroll(page, randomInt(200, 420));
    }
    await humanMouseMove(page);
}

async function randomPhoneFormInteractions(page) {
    await openSecuritySubMenu(page, "Đăng ký Số điện thoại");
    if (randomInt(1, 2) === 1) {
        await humanScroll(page, randomInt(220, 420));
    }

    const phoneInput = page
        .locator('input[placeholder="Số điện thoại"]')
        .first();
    if (await phoneInput.isVisible()) {
        await humanHover(page, phoneInput);
        await phoneInput.click({ timeout: 2000 });
        await humanPause(600, 1200);
        await page.mouse.click(randomInt(40, 160), randomInt(120, 260), {
            steps: 2,
        });
        await humanPause(500, 900);
    }

    if (randomInt(1, 3) === 1) {
        await humanScroll(page, randomInt(200, 380));
    }
    await humanMouseMove(page);
}

async function randomChangeEmailInteractions(page) {
    await openSecuritySubMenu(page, "Thay đổi Email");
    if (randomInt(1, 2) === 1) {
        await humanScroll(page, randomInt(220, 420));
    }

    const emailInput = page
        .locator('input[placeholder="Địa chỉ Email mới"]')
        .first();
    if (await emailInput.isVisible()) {
        await humanHover(page, emailInput);
        await emailInput.click({ timeout: 2000 });
        await humanPause(600, 1200);
        if (randomInt(1, 2) === 1) {
            await page.keyboard.type("test", { delay: randomInt(80, 160) });
            await humanPause(400, 800);
            for (let i = 0; i < 4; i++) {
                await page.keyboard.press("Backspace");
                await humanPause(60, 120);
            }
        }
    }

    if (randomInt(1, 3) === 1) {
        await humanScroll(page, randomInt(200, 400));
    }
    await humanMouseMove(page);
}

async function randomCitizenIdInteractions(page) {
    await openSecuritySubMenu(page, "Xác nhận căn cước công dân");
    if (randomInt(1, 2) === 1) {
        await humanScroll(page, randomInt(220, 420));
    }

    const nameInput = page.locator('input[placeholder="Tên"]').first();
    if ((await nameInput.isVisible()) && randomInt(1, 2) === 1) {
        await humanHover(page, nameInput);
        await nameInput.click({ timeout: 2000 });
        await humanPause(600, 1200);
        await page.mouse.click(randomInt(60, 180), randomInt(140, 260), {
            steps: 2,
        });
        await humanPause(500, 900);
    }

    if (randomInt(1, 3) === 1) {
        await humanScroll(page, randomInt(200, 380));
    }
    await humanMouseMove(page);
}

async function wanderAccountCenter(page) {
    const flows = [
        async () => {
            await clickTopTab(page, "Trang chủ");
            await randomHomeInteractions(page);
            if (randomInt(1, 2) === 1) {
                await clickTopTab(page, "Bảo mật");
                if (randomInt(1, 2) === 1) {
                    await humanScroll(page, randomInt(200, 360));
                }
            }
        },
        async () => {
            await clickTopTab(page, "Bảo mật");
            await randomPhoneFormInteractions(page);
        },
        async () => {
            await clickTopTab(page, "Bảo mật");
            await randomChangeEmailInteractions(page);
        },
        async () => {
            await clickTopTab(page, "Bảo mật");
            await randomCitizenIdInteractions(page);
        },
        async () => {
            await clickTopTab(page, "FAQ");
            await randomFaqInteractions(page);
            if (randomInt(1, 2) === 1) {
                await clickTopTab(page, "Bảo mật");
                if (randomInt(1, 2) === 1) {
                    await humanScroll(page, randomInt(200, 360));
                }
            }
        },
    ];

    try {
        const runCount = randomInt(1, 3);
        for (let i = 0; i < runCount; i++) {
            const flow = flows[randomInt(0, flows.length - 1)];
            await flow();
            await humanPause(700, 1400);
        }
    } catch (error) {
        console.warn("[Garena] Bỏ qua bước đi dạo Account Center:", error);
    }
}

async function run() {
    const tempProfileDir = path.join(
        process.cwd(),
        "storage",
        "playwright-temp",
        `${Date.now()}-${Math.random().toString(16).slice(2)}`
    );
    fs.mkdirSync(tempProfileDir, { recursive: true });

    const seedString =
        process.env.PLAYWRIGHT_PROXY_KEY_ID || accountId || username;
    const profile = generateRealisticBrowserProfile(seedString);

    let browser = null;
    let context = null;
    let page = null;

    try {
        browser = await chromium.launch({ headless });
        context = await browser.newContext({
            ...profile.contextOptions,
        });

        page = await context.newPage();
        await page.addInitScript(
            (navOverrides, screenInfo) => {
                Object.defineProperty(navigator, "webdriver", {
                    get: () => undefined,
                });

                if (!window.chrome) {
                    window.chrome = { runtime: {} };
                }

                Object.defineProperty(navigator, "platform", {
                    get: () => navOverrides.platform,
                });
                Object.defineProperty(navigator, "language", {
                    get: () => navOverrides.language,
                });
                Object.defineProperty(navigator, "languages", {
                    get: () => navOverrides.languages,
                });
                Object.defineProperty(navigator, "hardwareConcurrency", {
                    get: () => navOverrides.hardwareConcurrency,
                });
                Object.defineProperty(navigator, "maxTouchPoints", {
                    get: () => navOverrides.maxTouchPoints,
                });
                try {
                    Object.defineProperty(navigator, "deviceMemory", {
                        get: () => navOverrides.deviceMemory,
                    });
                } catch {
                    // ignore
                }

                Object.assign(window.screen, {
                    width: screenInfo.width,
                    height: screenInfo.height,
                    availWidth: screenInfo.availWidth,
                    availHeight: screenInfo.availHeight,
                    colorDepth: screenInfo.colorDepth,
                    pixelDepth: screenInfo.pixelDepth,
                });
            },
            profile.navigatorOverrides,
            profile.screen
        );

        console.log("[Profile] Using browser profile:", profile.meta);

        console.log("[Garena] B1: Mở https://account.garena.com");
        await page.goto("https://account.garena.com", {
            waitUntil: "load",
            timeout: 60000,
        });
        await humanPause(1000, 2000);

        await page.waitForURL(
            /https:\/\/sso\.garena\.com\/universal\/login.*/i,
            {
                timeout: 20000,
            }
        );
        await page.evaluate(() => window.scrollTo(0, 120));
        await humanMouseMove(page);
        await humanPause();

        console.log("[Garena] B2: Điền form đăng nhập");
        await humanType(page, loginInputSelector, username);
        await humanPause(400, 800);
        await humanType(page, passwordInputSelector, password);
        await humanPause(800, 1500);

        console.log("[Garena] B3: Nhấn Đăng Nhập");
        await page.locator('button:has-text("Đăng Nhập Ngay")').click();
        await humanPause(1000, 2000);
        await failIfDanger(page);
        await page.waitForTimeout(1500);
        await failIfDanger(page);
        await retryLoginIfNeeded(page, username, password);

        console.log("[Garena] B4: Chờ Account Center tải xong");
        await page.waitForSelector("text=Trang chủ", { timeout: 30000 });
        await humanPause(600, 1200);
        await ensureAccountSafe(page);
        await humanScroll(page, 400);
        console.log("[Garena] B4.5: Đi dạo như người dùng thật");
        await wanderAccountCenter(page);

        console.log("[Garena] B5: Mở form đổi mật khẩu từ trang chủ");
        const changePasswordButton = page
            .locator("text=Thay đổi Mật khẩu")
            .first();
        await changePasswordButton.click();
        await humanPause(1000, 1800);
        await page.waitForSelector(oldPasswordSelector, { timeout: 20000 });

        console.log("[Garena] B6: Điền form đổi mật khẩu");
        await typeExact(page, oldPasswordSelector, password);
        await humanPause(700, 1200);
        await typeExact(page, newPasswordSelector, newPassword);
        await humanPause(650, 1100);
        await typeExact(page, confirmPasswordSelector, newPassword);
        await humanPause(1200, 2000);

        console.log("[Garena] B7: Nhấn THAY ĐỔI (submit)");
        const submitButton = page.getByRole("button", submitButtonRole);
        await submitButton.waitFor({ timeout: 15000 });
        await submitButton.scrollIntoViewIfNeeded();
        await humanMouseMove(page);
        const box = await submitButton.boundingBox();
        if (box) {
            const offsetX = randomInt(
                Math.floor(box.width * 0.2),
                Math.floor(box.width * 0.8)
            );
            const offsetY = randomInt(
                Math.floor(box.height * 0.3),
                Math.floor(box.height * 0.8)
            );
            await page.mouse.move(box.x + offsetX, box.y + offsetY, {
                steps: randomInt(4, 8),
            });
            await humanPause(1000, 1800);
        } else {
            await humanPause(800, 1400);
        }
        await submitButton.click();
        await humanPause(2200, 3600);

        const successMessage = "Bạn đã đổi mật khẩu thành công.";
        const verificationSelectors = [
            "text=Xác minh thiết bị",
            "text=Device Verification",
            "text=Thiết bị",
        ];

        try {
            await page.waitForSelector(`text=${successMessage}`, {
                timeout: 10000,
            });
            console.log(`[Garena] ${successMessage}`);
        } catch (_) {
            for (const selector of verificationSelectors) {
                try {
                    if (await page.locator(selector).first().isVisible()) {
                        throw new Error(
                            "[Garena] Garena yêu cầu xác minh thiết bị sau khi đổi mật khẩu. Vui lòng hoàn tất bước xác minh thủ công."
                        );
                    }
                } catch {
                    // selector not found, ignore
                }
            }

            throw new Error(
                "[Garena] Không thấy thông báo đổi mật khẩu thành công. Vui lòng kiểm tra lại trang Garena."
            );
        }

        console.log("[Garena] Kết thúc, đợi thêm trước khi đóng.");
        await page.waitForTimeout(5000);
    } finally {
        if (context) {
            await context.close().catch(() => {});
        }
        if (browser) {
            await browser.close().catch(() => {});
        }
        fs.rmSync(tempProfileDir, { recursive: true, force: true });
    }
}

run().catch((error) => {
    console.error("[Garena Playwright] Lỗi:", error);
    if (
        typeof error?.message === "string" &&
        error.message.includes("nguy hiểm")
    ) {
        console.error("[Garena] Đăng nhập báo tài khoản nguy hiểm, dừng ngay.");
    }
    process.exit(1);
});

async function retryLoginIfNeeded(page, username, password) {
    const loginSuccessSelector = "text=Trang chủ";
    try {
        await page.waitForSelector(loginSuccessSelector, { timeout: 8000 });
        return;
    } catch (_) {
        console.log("[Garena] Login không thành công, gõ lại chính xác.");
    }

    await failIfDanger(page);
    await typeExact(page, loginInputSelector, username);
    await humanPause(200, 400);
    await typeExact(page, passwordInputSelector, password);
    await humanPause(200, 400);
    await page.locator('button:has-text("Đăng Nhập Ngay")').click();
    await page.waitForSelector(loginSuccessSelector, { timeout: 15000 });
}

function passwordMeetsPolicy(value) {
    if (!value || value.length < 8 || value.length > 16) {
        return false;
    }

    const hasUpper = /[A-Z]/.test(value);
    const hasLower = /[a-z]/.test(value);
    const hasDigit = /\d/.test(value);
    const hasSpecial = /[^A-Za-z0-9]/.test(value);

    return hasUpper && hasLower && hasDigit && hasSpecial;
}
