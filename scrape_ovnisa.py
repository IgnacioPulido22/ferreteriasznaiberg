"""
Scraper Ovnisa -> products.json
Asigna la imagen de O-ring NBR de Ovnisa a todos los productos de mi catalogo
que tienen nombre de solo dimensiones (ej: "2,84 X 8,08").
"""
import json
import re
import time
from io import BytesIO
from pathlib import Path

import requests
from PIL import Image

PRODUCTS_PATH = "products.json"
OUTPUT_DIR = Path("imagenes_productos")
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120"}
SLEEP = 0.3

# URL de la imagen NBR de Ovnisa (Cloudinary, formato medium)
NBR_IMG_URL = "https://res.cloudinary.com/dgme1hx1c/image/upload/v1719838913/medium_ORING_NBR_01_copia_c047579401.jpg"

# Patron: nombre compuesto SOLO por "D1 X D2" (con comas o puntos decimales)
DIM_ONLY = re.compile(r"^\s*\d+[,.]?\d*\s*[xX]\s*\d+[,.]?\d*\s*$")


def is_dim_oring(name):
    return bool(DIM_ONLY.match(name))


def download_image(url, dest_path):
    r = requests.get(url, headers=HEADERS, timeout=20)
    r.raise_for_status()
    img = Image.open(BytesIO(r.content)).convert("RGBA")
    img.save(dest_path, "PNG", optimize=True)


def main():
    OUTPUT_DIR.mkdir(exist_ok=True)

    with open(PRODUCTS_PATH, encoding="utf-8") as f:
        all_products = json.load(f)

    prod_by_id = {p["id"]: p for p in all_products}

    # Identificar O-rings por dimension sin imagen
    targets = [
        p for p in all_products
        if not p.get("img") and is_dim_oring(p["name"])
    ]

    print(f"O-rings por dimension sin imagen: {len(targets)}")
    for p in targets:
        print(f"  id={p['id']}  {p['name']}")

    if not targets:
        print("Nada para actualizar.")
        return

    print(f"\nDescargando imagen NBR de Ovnisa...")
    r = requests.get(NBR_IMG_URL, headers=HEADERS, timeout=20)
    r.raise_for_status()
    raw = r.content
    print(f"  Descargada ({len(raw)//1024} KB)")

    print(f"\nAsignando a {len(targets)} productos...")
    updated = 0
    for p in targets:
        dest = OUTPUT_DIR / f"prod_{p['id']}.png"
        try:
            img = Image.open(BytesIO(raw)).convert("RGBA")
            img.save(dest, "PNG", optimize=True)
            prod_by_id[p["id"]]["img"] = f"imagenes_productos/prod_{p['id']}.png"
            updated += 1
            print(f"  [OK] id={p['id']}  {p['name']}")
        except Exception as e:
            print(f"  [ERROR] id={p['id']}: {e}")

    with open(PRODUCTS_PATH, "w", encoding="utf-8") as f:
        json.dump(all_products, f, ensure_ascii=False, indent=4)

    print(f"\nListo: {updated}/{len(targets)} productos actualizados.")


if __name__ == "__main__":
    main()
