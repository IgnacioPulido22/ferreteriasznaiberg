"""
Scraper Resortecnica -> products.json

Asigna imagenes del catalogo de Resortecnica a los productos correspondientes:
- Resortes: segun tipo (traccion, compresion, conicos, etc.)
- Carbones electricos: imagen generica de set de carbones
"""
import json
import time
from io import BytesIO
from pathlib import Path

import requests
from PIL import Image

PRODUCTS_PATH = "products.json"
OUTPUT_DIR = Path("imagenes_productos")
BASE_URL = "https://www.resortecnica.com.ar/"
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120"}
SLEEP = 1.2

# Imagen segun tipo de resorte (por palabras en el nombre del producto)
RESORTE_TYPE_TO_IMG = {
    "TRACCION":   "img/pics/tablero-resortes.jpg",
    "CONICOS":    "img/pics/tablero-resortes.jpg",
    "COMPRESION": "img/pics/tablero-resortes.jpg",
    "BANO":       "img/pics/tablero-resortes.jpg",
    "VAIVEN":     "img/pics/tablero-resortes.jpg",
    "MULTIUSO":   "img/pics/tablero-resortes.jpg",
    "TIJERA":     "img/pics/tablero-resortes.jpg",
    "MOSQUITERO": "img/pics/tablero-resortes.jpg",
    "COCINA":     "img/pics/tablero-resortes2.jpg",
    "EMBRAGUE":   "img/pics/tablero-resortes-auto2.jpg",
    "CAMA":       "img/pics/productos-resortes-gimnasia.jpg",
}

# Imagen para carbones electricos (los que NO tienen imagen ya)
CARBON_IMG = "img/pics/set-CAR1.png"

# Palabras que identifican carbones electricos (excluyendo "acero carbono" de herramientas)
CARBON_KEYWORDS = [
    "carbon no ",
    "carbon n.",
    "juego de 2 carbones",
    "carbones amoladora",
    "carbones taladro",
    "carbones bordeadora",
    "carbones motor",
]


def download_image(img_url, dest_path):
    r = requests.get(img_url, headers=HEADERS, timeout=20)
    r.raise_for_status()
    img = Image.open(BytesIO(r.content)).convert("RGBA")
    img.save(dest_path, "PNG", optimize=True)


def is_carbon_electrico(name):
    n = name.lower()
    # Excluir "acero carbono" que son herramientas
    if "acero carbono" in n:
        return False
    for kw in CARBON_KEYWORDS:
        if kw in n:
            return True
    return False


def main():
    OUTPUT_DIR.mkdir(exist_ok=True)

    with open(PRODUCTS_PATH, encoding="utf-8") as f:
        products = json.load(f)

    prod_by_id = {p["id"]: p for p in products}

    # --- Resortes ---
    # Agrupar por tipo (imagen destino)
    resorte_img_to_ids: dict[str, list[int]] = {}
    for p in products:
        name_upper = p["name"].upper()
        if "RESORTE" not in name_upper:
            continue
        if p.get("img"):  # ya tiene imagen
            continue
        for tipo, img_path in RESORTE_TYPE_TO_IMG.items():
            if tipo in name_upper:
                resorte_img_to_ids.setdefault(img_path, []).append(p["id"])
                break
        else:
            # Resorte sin tipo reconocido -> imagen generica
            resorte_img_to_ids.setdefault("img/pics/tablero-resortes.jpg", []).append(p["id"])

    # --- Carbones ---
    carbon_ids = [
        p["id"] for p in products
        if not p.get("img") and is_carbon_electrico(p["name"])
    ]
    if carbon_ids:
        resorte_img_to_ids[CARBON_IMG] = carbon_ids

    if not resorte_img_to_ids:
        print("No hay productos para actualizar.")
        return

    print("=== Resumen de asignaciones ===")
    total_to_update = 0
    for img_path, ids in resorte_img_to_ids.items():
        print(f"  {img_path.split('/')[-1]:45s}  -> {len(ids)} productos")
        total_to_update += len(ids)
    print(f"Total: {total_to_update} productos\n")

    # Descargar cada imagen una sola vez y asignar a todos sus productos
    updated = 0
    # Imagen unica por URL para no descargar dos veces la misma
    img_cache: dict[str, bytes] = {}

    for img_path, ids in resorte_img_to_ids.items():
        full_url = BASE_URL + img_path
        print(f"\nDescargando: {full_url}")

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

    print(f"\nListo: {updated}/{total_to_update} productos actualizados en products.json.")


if __name__ == "__main__":
    main()
