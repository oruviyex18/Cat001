const { chromium } = require('playwright');
const path = require('path');

const shot = (page, name) => page.screenshot({ path: path.join(__dirname, `chat_${name}.png`) });

async function loginAs(page, username, password) {
  await page.goto('http://localhost:4200/auth/login');
  await page.waitForLoadState('networkidle');
  await page.locator('input[formcontrolname="username"]').fill(username);
  await page.locator('input[formcontrolname="password"]').fill(password);
  await page.locator('button[type="submit"]').click();
  await page.waitForURL('**/cats', { timeout: 8000 });
}

async function typeMessage(page, text) {
  // Click the textarea, clear it, then type char-by-char to trigger Angular ngModel
  const ta = page.locator('textarea[placeholder*="Enter"], textarea[placeholder*="send"], textarea');
  await ta.click();
  await ta.fill('');           // clear first
  await ta.pressSequentially(text, { delay: 40 });
}

(async () => {
  const browser = await chromium.launch({ headless: false, slowMo: 150 });

  const ctx1 = await browser.newContext({ viewport: { width: 700, height: 750 } });
  const ctx2 = await browser.newContext({ viewport: { width: 700, height: 750 } });
  const page1 = await ctx1.newPage();
  const page2 = await ctx2.newPage();

  // Login both users
  await Promise.all([
    loginAs(page1, 'testbreeder', 'Test1234!'),
    loginAs(page2, 'breeder2',    'Test1234!'),
  ]);

  // Navigate to chat
  await Promise.all([
    page1.locator('button:has-text("Chat")').click().then(() => page1.waitForURL('**/messages**')),
    page2.locator('button:has-text("Chat")').click().then(() => page2.waitForURL('**/messages**')),
  ]);
  await Promise.all([page1.waitForLoadState('networkidle'), page2.waitForLoadState('networkidle')]);

  // Wait for WebSocket "Connected" status on both
  await Promise.all([
    page1.getByText('Connected').waitFor({ timeout: 8000 }),
    page2.getByText('Connected').waitFor({ timeout: 8000 }),
  ]);

  await shot(page1, '01_user1_connected');
  await shot(page2, '01_user2_connected');

  // testbreeder types and sends
  await typeMessage(page1, 'Hey breeder2! Nice to meet you');
  await shot(page1, '02_user1_typing');
  await page1.locator('button.send-btn').click();
  await page1.waitForTimeout(1000);

  await shot(page1, '03_user1_sent');
  await shot(page2, '03_user2_received');

  // breeder2 replies
  await typeMessage(page2, 'Hi testbreeder! Great to be here');
  await page2.locator('button.send-btn').click();
  await page2.waitForTimeout(1000);

  await shot(page1, '04_user1_sees_reply');
  await shot(page2, '04_user2_replied');

  // one more from testbreeder
  await typeMessage(page1, 'WebSocket chat is working perfectly!');
  await page1.locator('button.send-btn').click();
  await page1.waitForTimeout(1200);

  await shot(page1, '05_final_user1');
  await shot(page2, '05_final_user2');

  await browser.close();
  console.log('Done.');
})().catch(err => { console.error(err.message); process.exit(1); });
