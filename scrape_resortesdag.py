"""
Reemplaza TODAS las imagenes de resortes usando Resortes DAG como proveedor.
Mapeo por tipo de resorte -> imagen de la categoria correspondiente.
"""
import json
import time
from io import BytesIO
from pathlib import Path

import requests
from PIL import Image

PRODUCTS_PATH = "products.json"
OUTPUT_DIR = Path("imagenes_productos")
BASE_URL = "https://www.resortesdag.com.ar/"
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120"}
SLEEP = 1.0

# Imagenes de cada categoria de DAG
IMG_TRACCION   = "imagenes/media_66bbae6a7053a.jpg"   # Resortes de traccion
IMG_COMPRESION = "imagenes/media_66bba91625c20.jpg"   # Resortes de compresion
IMG_TORSION    = "imagenes/media_66bba7af1afa1.jpg"   # Resortes de torsion

# Mapeo: palabra clave en nombre del producto -> imagen
TIPO_TO_IMG = {
    # Traccion / expansion
    "TRACCION":   IMG_TRACCION,
    "VAIVEN":     IMG_TRACCION,   # vaiven = traccion alternada
    "MOSQUITERO": IMG_TRACCION,
    # Compresion
    "COMPRESION": IMG_COMPRESION,
    "CONICOS":    IMG_COMPRESION,  # conicos son tipo compresion
    "BANO":       IMG_COMPRESION,
    "CAMA":       IMG_COMPRESION,
    "COCINA":     IMG_COMPRESION,
    "MULTIUSO":   IMG_COMPRESION,
    # Torsion
    "TIJERA":     IMG_TORSION,    # resortes de tijera = torsion
    "EMBRAGUE":   IMG_TORSION,    # embrague = torsion
}

# Imagen por defecto para resortes sin tipo reconocido
IMG_DEFAULT = IMG_COMPRESION


def download_image(url, dest_path):
    r = requests.get(url, headers=HEADERS, timeout=20)
    r.raise_for_status()
    img = Image.open(BytesIO(r.content)).convert("RGBA")
    img.save(dest_path, "PNG", optimize=True)


def get_img_for_resorte(name):
    name_upper = name.upper()
    for tipo, img_path in TIPO_TO_IMG.items():
        if tipo in name_upper:
            return img_path
    return IMG_DEFAULT


def main():
    OUTPUT_DIR.mkdir(exist_ok=True)

    with open(PRODUCTS_PATH, encoding="utf-8") as f:
        products = json.load(f)

    prod_by_id = {p["id"]: p for p in products}

    # Recolectar todos los resortes (con o sin imagen previa)
    img_to_ids: dict[str, list[int]] = {}
    for p in products:
        if "RESORTE" not in p["name"].upper():
            continue
        img_path = get_img_for_resorte(p["name"])
        img_to_ids.setdefault(img_path, []).append(p["id"])

    if not img_to_ids:
        print("No se encontraron resortes.")
        return

    total = sum(len(ids) for ids in img_to_ids.values())
    print("=== Resumen ===")
    for img_path, ids in img_to_ids.items():
        label = img_path.split("/")[-1]
        print(f"  {label:40s} -> {len(ids)} productos")
    print(f"Total: {total} resortes\n")

    # Descargar cada imagen una vez y aplicar a todos los productos de ese tipo
    updated = 0
    for img_path, ids in img_to_ids.items():
        full_url = BASE_URL + img_path
        print(f"Descargando: {full_url}")
        try:
            r = requests.get(full_url, headers=HEADERS, timeout=20)
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
                print(f"  [OK] id={pid} {prod_by_id[pid]['name'][:70]}")
            except Exception as e:
                print(f"  [ERROR] id={pid}: {e}")

    with open(PRODUCTS_PATH, "w", encoding="utf-8") as f:
        json.dump(products, f, ensure_ascii=False, indent=4)

    print(f"\nListo: {updated}/{total} resortes actualizados en products.json.")


if __name__ == "__main__":
    main()
