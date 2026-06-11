/**
 * Scraper Ovnisa -> products.json
 * Usa Playwright para renderizar la SPA y extraer productos de O-rings.
 * Matchea contra los productos de mi catalogo y descarga las imagenes.
 */

const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');
const https = require('https');
const http = require('http');

const PRODUCTS_PATH = 'products.json';
const OUTPUT_DIR = 'imagenes_productos';
const BASE_URL = 'https://www.ovnisa.com';
const ORING_URL = `${BASE_URL}/productos?categoria=sellos-hidraulicos&tipoProducto=sellos-o-rings`;

// ── Normalizar texto para comparacion ────────────────────────────────────────
function normalize(str) {
  return str
    .toLowerCase()
    .normalize('NFD').replace(/[̀-ͯ]/g, '')
    .replace(/[^a-z0-9\s.,x]/g, ' ')
    .replace(/\s+/g, ' ')
    .trim();
}

// ── Extraer dimensiones de un nombre de producto ──────────────────────────────
// Formatos posibles: "2,84 X 8,08" / "NBR 70 10x2" / "30 x 3.5"
function parseDims(name) {
  const n = normalize(name).replace(/,/g, '.');
  const m = n.match(/(\d+(?:\.\d+)?)\s*x\s*(\d+(?:\.\d+)?)/i);
  if (!m) return null;
  return { d1: parseFloat(m[1]), d2: parseFloat(m[2]) };
}

// ── Descargar imagen ──────────────────────────────────────────────────────────
function downloadImage(url, destPath) {
  return new Promise((resolve, reject) => {
    const proto = url.startsWith('https') ? https : http;
    const file = fs.createWriteStream(destPath);
    proto.get(url, { headers: { 'User-Agent': 'Mozilla/5.0' } }, res => {
      if (res.statusCode === 301 || res.statusCode === 302) {
        file.close();
        fs.unlinkSync(destPath);
        return downloadImage(res.headers.location, destPath).then(resolve).catch(reject);
      }
      if (res.statusCode !== 200) {
        file.close();
        return reject(new Error(`HTTP ${res.statusCode}`));
      }
      res.pipe(file);
      file.on('finish', () => { file.close(); resolve(); });
    }).on('error', err => { file.close(); reject(err); });
  });
}

// ── Score de similitud entre dos nombres ─────────────────────────────────────
function scoreNames(a, b) {
  const da = parseDims(a);
  const db = parseDims(b);
  if (da && db) {
    // Match exacto de dimensiones (tolerancia 0.1mm)
    const match1 = Math.abs(da.d1 - db.d1) < 0.15 && Math.abs(da.d2 - db.d2) < 0.15;
    const match2 = Math.abs(da.d1 - db.d2) < 0.15 && Math.abs(da.d2 - db.d1) < 0.15;
    if (match1 || match2) return 1.0;
    // Match aproximado
    const match3 = Math.abs(da.d1 - db.d1) < 0.5 && Math.abs(da.d2 - db.d2) < 0.5;
    if (match3) return 0.8;
    return 0;
  }
  // Si no hay dimensiones, comparar palabras clave
  const wa = new Set(normalize(a).split(' ').filter(w => w.length > 2));
  const wb = new Set(normalize(b).split(' ').filter(w => w.length > 2));
  const inter = [...wa].filter(w => wb.has(w)).length;
  if (!inter) return 0;
  return inter / Math.max(wa.size, wb.size);
}

// ─────────────────────────────────────────────────────────────────────────────

async function scrapeOvnisa() {
  console.log('Iniciando Playwright...');
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage();
  await page.setViewportSize({ width: 1280, height: 900 });

  console.log(`Navegando a: ${ORING_URL}`);
  await page.goto(ORING_URL, { waitUntil: 'networkidle', timeout: 30000 });
  await page.waitForTimeout(3000);

  // Intentar hacer scroll para cargar todos los productos (lazy loading)
  let prevHeight = 0;
  for (let i = 0; i < 10; i++) {
    await page.evaluate(() => window.scrollTo(0, document.body.scrollHeight));
    await page.waitForTimeout(1000);
    const h = await page.evaluate(() => document.body.scrollHeight);
    if (h === prevHeight) break;
    prevHeight = h;
  }

  console.log('Extrayendo productos...');
  const products = await page.evaluate(() => {
    const results = [];
    // Buscar cards de producto (probar varios selectores comunes)
    const selectors = [
      '.product-card', '.producto', '.card', '[class*="product"]',
      '[class*="Product"]', 'article', '.item', '[class*="item"]'
    ];
    let cards = [];
    for (const sel of selectors) {
      cards = document.querySelectorAll(sel);
      if (cards.length > 2) break;
    }
    cards.forEach(card => {
      const img = card.querySelector('img');
      const nameEl = card.querySelector('h2, h3, h4, [class*="name"], [class*="title"], p');
      if (img && nameEl) {
        results.push({
          name: nameEl.textContent.trim(),
          img: img.src || img.dataset.src || '',
        });
      }
    });

    // Si no encontramos nada, intentar directamente con todos los imgs con alt
    if (results.length === 0) {
      document.querySelectorAll('img[alt]').forEach(img => {
        if (img.alt && img.alt.length > 3 && img.src && !img.src.includes('logo') && !img.src.includes('icon')) {
          results.push({ name: img.alt.trim(), img: img.src });
        }
      });
    }
    return results;
  });

  console.log(`Productos encontrados en Ovnisa: ${products.length}`);
  products.forEach((p, i) => console.log(`  [${i+1}] ${p.name} | ${p.img}`));

  // Guardar HTML para debug si no encontramos nada
  if (products.length === 0) {
    const html = await page.content();
    fs.writeFileSync('ovnisa_debug.html', html);
    console.log('Pagina guardada en ovnisa_debug.html para revision');
  }

  await browser.close();
  return products;
}

async function main() {
  if (!fs.existsSync(OUTPUT_DIR)) fs.mkdirSync(OUTPUT_DIR);

  const ovnisaProducts = await scrapeOvnisa();
  if (ovnisaProducts.length === 0) {
    console.log('\nNo se encontraron productos. Revisa ovnisa_debug.html');
    return;
  }

  const allProducts = JSON.parse(fs.readFileSync(PRODUCTS_PATH, 'utf-8'));

  // Filtrar productos sin imagen (o-rings y similares)
  const myProducts = allProducts.filter(p => !p.img);

  console.log(`\nMis productos sin imagen: ${myProducts.length}`);
  console.log('Buscando coincidencias...\n');

  const toUpdate = []; // { myProd, ovnisaProd, score }

  for (const myP of myProducts) {
    let best = null, bestScore = 0;
    for (const op of ovnisaProducts) {
      const s = scoreNames(myP.name, op.name);
      if (s > bestScore) { bestScore = s; best = op; }
    }
    if (bestScore >= 0.7 && best) {
      toUpdate.push({ myProd: myP, ovnisaProd: best, score: bestScore });
    }
  }

  console.log(`Matches encontrados: ${toUpdate.length}`);
  toUpdate.forEach(({ myProd, ovnisaProd, score }) => {
    const tag = score === 1.0 ? 'EXACTO' : score >= 0.8 ? 'BUENO' : 'OK';
    console.log(`  [${tag}] (${score.toFixed(2)}) "${myProd.name}" <- "${ovnisaProd.name}"`);
  });

  if (toUpdate.length === 0) {
    console.log('Sin matches. Abortando.');
    return;
  }

  // Agrupar por imagen origen (no descargar la misma URL dos veces)
  const imgCache = new Map(); // imgUrl -> destPath of first download

  console.log('\nDescargando imagenes...');
  let updated = 0;
  const prodById = Object.fromEntries(allProducts.map(p => [p.id, p]));

  for (const { myProd, ovnisaProd } of toUpdate) {
    const imgUrl = ovnisaProd.img;
    const dest = path.join(OUTPUT_DIR, `prod_${myProd.id}.png`);

    try {
      if (imgCache.has(imgUrl)) {
        // Copiar desde cache en lugar de re-descargar
        fs.copyFileSync(imgCache.get(imgUrl), dest);
      } else {
        await downloadImage(imgUrl, dest);
        imgCache.set(imgUrl, dest);
        await new Promise(r => setTimeout(r, 500));
      }
      prodById[myProd.id].img = `imagenes_productos/prod_${myProd.id}.png`;
      updated++;
      console.log(`  [OK] id=${myProd.id} ${myProd.name}`);
    } catch (e) {
      console.log(`  [ERROR] id=${myProd.id}: ${e.message}`);
    }
  }

  fs.writeFileSync(PRODUCTS_PATH, JSON.stringify(allProducts, null, 4), 'utf-8');
  console.log(`\nListo: ${updated} productos actualizados en products.json.`);
}

main().catch(console.error);
