const puppeteer = require('c:/Yashwanth/semproj/frontend/node_modules/puppeteer-core');
const fs = require('fs');
const path = require('path');

const CHROME_PATH = 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe';
const SCREENSHOTS_DIR = 'C:\\Yashwanth\\semproj\\screenshots';
const SAMPLE_IMAGE_PATH = 'C:\\Yashwanth\\semproj\\data\\samples\\fire\\sample_fire_000.jpg';
const DETECTION_ID = '5b9826de-6456-4053-9931-4c4dc3d82b56';

if (!fs.existsSync(SCREENSHOTS_DIR)) {
  fs.mkdirSync(SCREENSHOTS_DIR, { recursive: true });
}

async function run() {
  console.log('[*] Launching headless Chrome from:', CHROME_PATH);
  const browser = await puppeteer.launch({
    executablePath: CHROME_PATH,
    headless: 'new',
    args: [
      '--no-sandbox',
      '--disable-setuid-sandbox',
      '--disable-dev-shm-usage',
      '--window-size=1920,1080'
    ],
    defaultViewport: {
      width: 1920,
      height: 1080,
      deviceScaleFactor: 2
    }
  });

  const page = await browser.newPage();

  // 1. Live Monitoring - Feed selector & Grad-CAM Overlay
  console.log('\n[1/6] Capturing 1_live_monitoring.png ...');
  await page.goto('http://localhost:5180/monitoring', { waitUntil: 'networkidle0', timeout: 30000 });
  await new Promise(r => setTimeout(r, 1500));

  // Upload sample fire image
  const fileInput = await page.$('input[type="file"]');
  if (fileInput && fs.existsSync(SAMPLE_IMAGE_PATH)) {
    console.log('[*] Uploading sample fire image for Grad-CAM generation...');
    await fileInput.uploadFile(SAMPLE_IMAGE_PATH);
    await new Promise(r => setTimeout(r, 1000));

    // Click "Run Explainable Inference" button
    const buttons = await page.$$('button');
    let inferenceClicked = false;
    for (const b of buttons) {
      const text = await page.evaluate(el => el.textContent, b);
      if (text && (text.includes('Run Explainable Inference') || text.includes('Run Inference'))) {
        await b.click();
        inferenceClicked = true;
        console.log('[*] Clicked Run Explainable Inference button. Awaiting prediction...');
        break;
      }
    }

    if (inferenceClicked) {
      // Wait for inference response and UI update
      await page.waitForSelector('.badge', { timeout: 10000 }).catch(() => {});
      await new Promise(r => setTimeout(r, 2000));

      // Click Grad-CAM Overlay view mode button
      const overlayButtons = await page.$$('button');
      for (const b of overlayButtons) {
        const text = await page.evaluate(el => el.textContent, b);
        if (text && text.includes('Grad-CAM Overlay')) {
          await b.click();
          console.log('[*] Switched to Grad-CAM Overlay view mode.');
          break;
        }
      }
      await new Promise(r => setTimeout(r, 1500));
    }
  }
  await page.screenshot({ path: path.join(SCREENSHOTS_DIR, '1_live_monitoring.png'), fullPage: false });
  console.log('[OK] Saved screenshots/1_live_monitoring.png');

  // 2. Detection Details & XAI Inspector - Heatmap Toggle and Probability
  console.log('\n[2/6] Capturing 2_detection_detail_xai.png ...');
  await page.goto(`http://localhost:5180/detections/${DETECTION_ID}`, { waitUntil: 'networkidle0', timeout: 30000 });
  await new Promise(r => setTimeout(r, 2000));
  await page.screenshot({ path: path.join(SCREENSHOTS_DIR, '2_detection_detail_xai.png'), fullPage: false });
  console.log('[OK] Saved screenshots/2_detection_detail_xai.png');

  // 3. Incident Triage Console - Severity Badges, Acknowledgement & Close Action
  console.log('\n[3/6] Capturing 3_incident_triage_console.png ...');
  await page.goto('http://localhost:5180/alerts', { waitUntil: 'networkidle0', timeout: 30000 });
  await new Promise(r => setTimeout(r, 2000));
  await page.screenshot({ path: path.join(SCREENSHOTS_DIR, '3_incident_triage_console.png'), fullPage: false });
  console.log('[OK] Saved screenshots/3_incident_triage_console.png');

  // 4. Analysis & Benchmarks - Benchmark Matrix, Class Distribution & Suppression Chart
  console.log('\n[4/6] Capturing 4_analytics_benchmarks.png ...');
  await page.goto('http://localhost:5180/analytics', { waitUntil: 'networkidle0', timeout: 30000 });
  await new Promise(r => setTimeout(r, 2500));
  await page.screenshot({ path: path.join(SCREENSHOTS_DIR, '4_analytics_benchmarks.png'), fullPage: false });
  console.log('[OK] Saved screenshots/4_analytics_benchmarks.png');

  // 5. Overview Dashboard - KPI Cards, Warning Banner & 7-Day Trend
  console.log('\n[5/6] Capturing 5_overview_dashboard.png ...');
  await page.goto('http://localhost:5180/', { waitUntil: 'networkidle0', timeout: 30000 });
  await new Promise(r => setTimeout(r, 2500));
  await page.screenshot({ path: path.join(SCREENSHOTS_DIR, '5_overview_dashboard.png'), fullPage: false });
  console.log('[OK] Saved screenshots/5_overview_dashboard.png');

  // 6. System Diagnostics - API, Database, Hardware Device & Worker Threads
  console.log('\n[6/6] Capturing 6_system_diagnostics.png ...');
  await page.goto('http://localhost:5180/system', { waitUntil: 'networkidle0', timeout: 30000 });
  await new Promise(r => setTimeout(r, 2000));
  await page.screenshot({ path: path.join(SCREENSHOTS_DIR, '6_system_diagnostics.png'), fullPage: false });
  console.log('[OK] Saved screenshots/6_system_diagnostics.png');

  await browser.close();
  console.log('\n====================================================================');
  console.log('[OK] All 6 project report screenshots captured successfully!');
  console.log('====================================================================');
}

run().catch(err => {
  console.error('[!] Error capturing screenshots:', err);
  process.exit(1);
});
