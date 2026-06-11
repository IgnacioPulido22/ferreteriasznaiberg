"""
Scraper Fedar Distribuidora -> products.json
Asigna imagenes de seguers (A, RS, I) a los productos correspondientes.
El proveedor vende gaveteros surtidos, una imagen por tipo de seguer.
"""
import json
import time
from io import BytesIO
from pathlib import Path

import requests
from PIL import Image

PRODUCTS_PATH = "products.json"
OUTPUT_DIR = Path("imagenes_productos")
BASE_URL = "https://www.fedardistribuidora.com.ar/uploads/"
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120"}
SLEEP = 1.0

# Imagen principal de cada tipo de seguer (foto del gavetero)
SEGUER_IMGS = {
    "SEGUERS A":  BASE_URL + "68 SEGUER A (1).jpg",
    "SEGUERS RS": BASE_URL + "70 SEGUER RS (1).jpg",
    "SEGUERS I":  BASE_URL + "69 SEGUER I (1) (1) (1) (1).jpg",
}


def download_image(url, dest_path):
    r = requests.get(url, headers=HEADERS, timeout=20)
    r.raise_for_status()
    img = Image.open(BytesIO(r.content)).convert("RGBA")
    img.save(dest_path, "PNG", optimize=True)


def get_tipo(name):
    n = name.upper()
    for tipo in SEGUER_IMGS:
        if tipo in n:
            return tipo
    return None


def main():
    OUTPUT_DIR.mkdir(exist_ok=True)

    with open(PRODUCTS_PATH, encoding="utf-8") as f:
        all_products = json.load(f)

    prod_by_id = {p["id"]: p for p in all_products}

    # Agrupar seguers sin imagen por tipo
    tipo_to_ids: dict[str, list[int]] = {}
    for p in all_products:
        tipo = get_tipo(p["name"])
        if tipo:
            tipo_to_ids.setdefault(tipo, []).append(p["id"])

    if not tipo_to_ids:
        print("No se encontraron seguers en el catalogo.")
        return

    print("=== Seguers encontrados ===")
    total = 0
    for tipo, ids in tipo_to_ids.items():
        already = sum(1 for pid in ids if prod_by_id[pid].get("img"))
        sin_img = len(ids) - already
        print(f"  {tipo}: {len(ids)} productos ({sin_img} sin imagen)")
        total += sin_img

    print(f"Total a actualizar: {total}\n")

    # Descargar imagen por tipo y asignar a TODOS (reemplazar si ya tiene)
    updated = 0
    for tipo, ids in tipo_to_ids.items():
        img_url = SEGUER_IMGS[tipo]
        print(f"Descargando: {img_url}")
        try:
            r = requests.get(img_url, headers=HEADERS, timeout=20)
            r.raise_for_status()
            raw = r.content
            time.sleep(SLEEP)
        except Exception as e:
            print(f"  [ERROR descarga] {e}")
            continue

        for pid in ids:
            dest = OUTPUT_DIR / f"prod_{pid}.png"
            try:
                img = Image.open(BytesIO(raw)).convert("RGBA")
                img.save(dest, "PNG", optimize=True)
                prod_by_id[pid]["img"] = f"imagenes_productos/prod_{pid}.png"
                updated += 1
                print(f"  [OK] id={pid}  {prod_by_id[pid]['name']}")
            except Exception as e:
                print(f"  [ERROR] id={pid}: {e}")

    with open(PRODUCTS_PATH, "w", encoding="utf-8") as f:
        json.dump(all_products, f, ensure_ascii=False, indent=4)

    print(f"\nListo: {updated} productos actualizados en products.json.")


if __name__ == "__main__":
    main()
