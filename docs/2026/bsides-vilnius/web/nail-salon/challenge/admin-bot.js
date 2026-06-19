const crypto = require('crypto');
const chromium = require('@sparticuz/chromium');
const puppeteer = require('puppeteer-core');

function generateToken() {
    const dict =
        'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789';
    const shuffled = [...dict].sort(() => Math.random() - 0.5).join('');
    return shuffled.substring(0, 32).split('').sort().join('');
}

const ADMIN_TOKEN = generateToken();

function renderReviewHTML(css, token) {
    const safeCss = css.replace(/<\/style/gi, '<\\/style');
    const nonce = crypto.randomBytes(16).toString('base64');
    return `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta http-equiv="Content-Security-Policy"
        content="default-src 'self'; object-src 'none'; img-src 'self'; style-src 'self' 'nonce-${nonce}'; font-src 'self' *;">
  <title>Design Review</title>
  <style nonce="${nonce}">
    *,*::before,*::after{box-sizing:border-box;margin:0;padding:0}
    body{font-family:'Courier New',monospace;background:#fff5fa;color:#2a0018;display:flex;justify-content:center;padding:48px 20px}
    .d-none{display:none!important}
    .review-container{max-width:480px;width:100%}
    h1{font-size:16px;color:#c0005a;text-transform:uppercase;letter-spacing:3px;text-align:center;margin-bottom:28px}
    .review-card{background:#fff;border:3px solid #2a0018;box-shadow:6px 6px 0 #c0005a;padding:28px;text-align:center}
    .nail-row{display:flex;justify-content:center;gap:10px;margin-bottom:20px}
    .nail{width:28px;height:40px;border-radius:50% 50% 50% 50%/30% 30% 70% 70%;border:2px solid #2a0018}
    .nail.pink{background:#ff6eb4}.nail.red{background:#c0005a}.nail.purple{background:#c084fc}
    .nail.mint{background:#34d399}.nail.blue{background:#60a5fa}
    .card-label{font-size:11px;color:#c0005a;text-transform:uppercase;letter-spacing:1px}
  </style>
  <style nonce="${nonce}">${safeCss}</style>
</head>
<body>
  <div class="review-container">
    <h1>Design Review</h1>
    <div class="review-card">
      <div class="nail-row">
        <div class="nail pink"></div>
        <div class="nail red"></div>
        <div class="nail purple"></div>
        <div class="nail mint"></div>
        <div class="nail blue"></div>
      </div>
      <p class="card-label">Web Design Submission</p>
    </div>
    <p id="adminToken" class="d-none">${token}</p>
  </div>
</body>
</html>`;
}

exports.handler = async (event) => {
    for (const record of event.Records) {
        const { css } = JSON.parse(record.body);
        const html = renderReviewHTML(css, ADMIN_TOKEN);

        console.log(`Admin is reviewing styled submission: ${css}`);

        let browser;
        try {
            browser = await puppeteer.launch({
                args: chromium.args,
                defaultViewport: chromium.defaultViewport,
                executablePath: await chromium.executablePath(),
                headless: chromium.headless,
            });

            const page = await browser.newPage();
            await page.setContent(html, { waitUntil: 'networkidle2' });
            await new Promise((r) => setTimeout(r, 7000));

            console.log('Admin finished reviewing submission');
        } catch (err) {
            console.error('Bot error:', err.message);
        } finally {
            if (browser) await browser.close();
        }
    }
};
