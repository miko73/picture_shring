"""
Najde obrázky (v aktuálním adresáři, v zadaném adresáři, nebo přímo zadané
soubory - lze i více najednou), vytvoří vedle nich subfolder 'small'
a uloží do něj zmenšené verze tak, aby každý soubor byl pod 0,5 MB.
"""

import sys
from collections import defaultdict
from pathlib import Path
from PIL import Image

MAX_BYTES = 500 * 1024  # 0,5 MB
SUPPORTED = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.webp'}
OUTPUT_DIR = 'small'


def compress_to_target(img: Image.Image, dest_path: Path, start_quality: int = 85) -> int:
    """Uloží obrázek jako JPEG se snižující se kvalitou, dokud soubor nepodleze MAX_BYTES.
    Vrátí finální kvalitu."""
    save_path = dest_path.with_suffix('.jpg')
    rgb = img.convert('RGB') if img.mode in ('RGBA', 'P', 'LA') else img

    for quality in range(start_quality, 4, -5):
        rgb.save(save_path, 'JPEG', quality=quality, optimize=True)
        if save_path.stat().st_size <= MAX_BYTES:
            return quality

    # Poslední pokus s quality=5
    rgb.save(save_path, 'JPEG', quality=5, optimize=True)
    return 5


def gather_images(paths):
    """Rozbalí zadané cesty (adresáře i jednotlivé soubory) na obrázky
    seskupené podle nadřazeného adresáře (tam se pak vytvoří 'small')."""
    groups = defaultdict(list)
    for raw in paths:
        p = Path(raw).resolve()
        if p.is_dir():
            for f in p.iterdir():
                if f.is_file() and f.suffix.lower() in SUPPORTED:
                    groups[p].append(f)
        elif p.is_file() and p.suffix.lower() in SUPPORTED:
            groups[p.parent].append(p)
    return groups


def main():
    args = sys.argv[1:] or ['.']
    groups = gather_images(args)

    if not groups:
        print('Žádné obrázky nenalezeny.')
        return

    for base_dir, image_files in groups.items():
        out_dir = base_dir / OUTPUT_DIR
        out_dir.mkdir(exist_ok=True)

        print(f'Nalezeno {len(image_files)} obrázků → výstup: {out_dir}')
        print()

        for src in sorted(image_files):
            dest = out_dir / src.name
            orig_kb = src.stat().st_size / 1024

            with Image.open(src) as img:
                final_quality = compress_to_target(img, dest)

            result_path = dest.with_suffix('.jpg')
            result_kb = result_path.stat().st_size / 1024
            status = 'OK' if result_kb <= MAX_BYTES / 1024 else 'PŘESAHUJE'

            print(f'  {src.name:40s}  {orig_kb:7.1f} kB → {result_kb:7.1f} kB  (q={final_quality})  [{status}]')

        print()

    print('Hotovo.')


if __name__ == '__main__':
    main()
