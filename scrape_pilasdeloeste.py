"""
Scraper Pilas del Oeste -> products.json
1. Extrae productos del JSON-LD de la pagina (sin JS dinamico)
2. Matching por palabras clave contra productos de pilas en el catalogo
3. Descarga imagenes y actualiza products.json
"""
import json
import re
import time
import unicodedata
from io import BytesIO
from pathlib import Path

import requests
from bs4 import BeautifulSoup
from PIL import Image

PRODUCTS_PATH = "products.json"
OUTPUT_DIR = Path("imagenes_productos")
BASE = "https://www.pilasdeloesteshop.com.ar"
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120"}
SLEEP = 0.8
SCORE_AUTO = 0.45
SCORE_SHOW = 0.30

# Palabras a ignorar en el matching
SKIP_WORDS = {
    "pila", "pilas", "bateria", "baterias", "pack", "blister", "caja",
    "unidad", "unidades", "x", "de", "la", "el", "los", "las", "al",
    "del", "y", "e", "o", "u", "a", "en", "por", "con", "para",
    "extra", "advanced", "max", "alcalina", "alcalinas", "litio", "zinc",
    "carbon", "recargable", "recargables", "distribuidora", "oficial",
    "precio", "tipo", "boton", "auditiva", "audifonos", "audifono",
    "bp", "pr", "mah", "mla", "mlu", "v", "w",
}


def normalize(text):
    text = unicodedata.normalize("NFKD", text)
    text = "".join(c for c in text if not unicodedata.combining(c))
    return text.lower()


def keywords(text):
    text = normalize(text)
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    return {w for w in text.split() if w not in SKIP_WORDS and len(w) > 1}


def kw_score(dist_kw, my_kw):
    if not dist_kw or not my_kw:
        return 0
    common = dist_kw & my_kw
    if not common:
        return 0
    jaccard = len(common) / len(dist_kw | my_kw)
    recall = len(common) / len(dist_kw)
    return (jaccard + recall) / 2


def is_pila_product(name):
    """Filtra solo productos de pilas/baterias reales del catalogo."""
    name_up = name.upper()
    return any(w in name_up for w in [
        "PILA ", "PILAS ", "BATERIA ", "BATERIAS ",
        "ENERGIZER", "DURACELL", "RAYOVAC", "MAXELL", "NIELSEN", "VINNIC",
        "CR2032", "CR2016", "CR1620", "CR123", "A23", "A27",
        "ALCALIN", "RECARGABLE",
    ]) and not any(w in name_up for w in [
        "DISCO ", "AEROSOL", "TERMINAL", "LINTERNA", "GATILLO", "DESTAPA",
        "LAMPARA", "CABLE ", "CONECTOR", "CARGADOR"
    ])


def fetch_catalog():
    """Extrae todos los productos del JSON-LD de la pagina del distribuidor."""
    r = requests.get(BASE + "/pilas/", headers=HEADERS, timeout=20)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")

    products = []
    for script in soup.find_all("script", type="application/ld+json"):
        try:
            data = json.loads(script.string or "")
        except Exception:
            continue
        if data.get("@type") == "Product":
            name = data.get("name", "").strip()
            img = data.get("image", "")
            if name and img:
                # Convertir thumbnail a mayor resolucion si es posible
                img_hd = re.sub(r"-480-0\.(webp|jpg|png)$", r"-1200-0.\1", img)
                products.append((name, img_hd, img))

    return products


def download_image(img_url, fallback_url, dest_path):
    for url in [img_url, fallback_url]:
        try:
            r = requests.get(url, headers=HEADERS, timeout=20)
            r.raise_for_status()
            img = Image.open(BytesIO(r.content)).convert("RGBA")
            img.save(dest_path, "PNG", optimize=True)
            return True
        except Exception:
            continue
    return False


def main():
    with open(PRODUCTS_PATH, encoding="utf-8") as f:
        products = json.load(f)

    # Filtrar mis productos de pilas
    my_pilas = [p for p in products if is_pila_product(p.get("name", ""))]
    print(f"Mis productos de pilas: {len(my_pilas)}")
    for p in my_pilas:
        img_status = "OK" if p.get("img") else "--"
        print(f"  [{img_status}] id={p['id']} {p['name']}")

    # Scraping del distribuidor
    print(f"\nScrapeando {BASE}/pilas/ ...")
    dist_catalog = fetch_catalog()
    print(f"Productos encontrados en distribuidor: {len(dist_catalog)}")
    for name, _, _ in dist_catalog:
        print(f"  {name}")

    # Matching
    print("\n--- MATCHING ---")
    my_kw_index = [(p, keywords(p["name"])) for p in my_pilas]
    to_apply = {}    # pid -> (dist_name, img_url, fallback_url, score)
    uncertain = []

    for dist_name, img_hd, img_thumb in dist_catalog:
        d_kw = keywords(dist_name)
        best_prod, best_score = None, 0
        for p, my_kw in my_kw_index:
            s = kw_score(d_kw, my_kw)
            if s > best_score:
                best_score = s
                best_prod = p

        if best_prod is None:
            continue

        pid = best_prod["id"]
        if best_score >= SCORE_AUTO:
            if pid not in to_apply or best_score > to_apply[pid][3]:
                to_apply[pid] = (dist_name, img_hd, img_thumb, best_score)
                print(f"[AUTO {best_score:.2f}] '{dist_name[:60]}' -> '{best_prod['name'][:50]}'")
        elif best_score >= SCORE_SHOW:
            uncertain.append((dist_name, best_prod, img_hd, img_thumb, best_score))

    print(f"\nMatches automaticos: {len(to_apply)}")

    if uncertain:
        print(f"\n--- {len(uncertain)} MATCHES DUDOSOS ---")
        for dname, my_prod, _, _, sc in uncertain:
            print(f"  Distribuidor: {dname[:70]}")
            print(f"  Mio:          {my_prod['name'][:70]}  (score={sc:.2f})")
            print()

    # Descargar e inyectar
    print(f"\nDescargando {len(to_apply)} imagenes...")
    prod_by_id = {p["id"]: p for p in products}
    updated = 0

    for pid, (dist_name, img_hd, img_thumb, sc) in sorted(to_apply.items()):
        dest = OUTPUT_DIR / f"prod_{pid}.png"
        ok = download_image(img_hd, img_thumb, dest)
        if ok:
            prod_by_id[pid]["img"] = f"imagenes_productos/prod_{pid}.png"
            updated += 1
            print(f"[OK] id={pid} {prod_by_id[pid]['name'][:65]}")
        else:
            print(f"[ERROR] id={pid} no se pudo descargar la imagen")
        time.sleep(SLEEP * 0.5)

    with open(PRODUCTS_PATH, "w", encoding="utf-8") as f:
        json.dump(products, f, ensure_ascii=False, indent=4)

    print(f"\nListo: {updated} productos actualizados en products.json.")


if __name__ == "__main__":
    main()
