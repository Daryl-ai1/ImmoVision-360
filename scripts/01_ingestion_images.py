"""
scripts/01_ingestion_images.py
==============================
Phase 1 — Ingestion du Data Lake (version optimisée)
- Téléchargement parallèle : 10 workers simultanés (ThreadPoolExecutor)
- Barre de progression tqdm en temps réel
- Logs détaillés par image (OK / SKIP / ERREUR)
- Idempotence, redimensionnement 320×320, gestion des exceptions

Arborescence du projet :
    IMMO.../
    ├── data/
    │   └── raw/
    │       ├── images/              ← sortie (créé automatiquement)
    │       └── tabular/
    │           └── listings.csv     ← source
    ├── myenv/
    └── scripts/
        └── 01_ingestion_images.py

Lancement :
    python scripts/01_ingestion_images.py

Dépendances :
    pip install requests pandas Pillow tqdm
"""

import time
import threading
import requests
import pandas as pd
from PIL import Image
from io import BytesIO
from pathlib import Path
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor, as_completed

# ══════════════════════════════════════════════════════════════
#  RÉSOLUTION DE LA RACINE DU PROJET
# ══════════════════════════════════════════════════════════════

ROOT = Path(__file__).resolve().parent.parent

# ══════════════════════════════════════════════════════════════
#  CONFIGURATION
# ══════════════════════════════════════════════════════════════

CSV_PATH    = ROOT / "data" / "raw" / "tabular" / "listings.csv"
OUTPUT_DIR  = ROOT / "data" / "raw" / "images"
TARGET_SIZE = (320, 320)
TIMEOUT_SEC = 10
MAX_WORKERS = 10          # ← téléchargements simultanés

FILTER_COLUMN = "neighbourhood_cleansed"
FILTER_VALUE  = "Élysée"

COL_ID  = "id"
COL_URL = "picture_url"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Referer": "https://www.airbnb.com/",
}

# ── Verrou pour protéger les écritures console (multi-thread) ──
_print_lock = threading.Lock()

# ══════════════════════════════════════════════════════════════


def safe_print(progress_bar: tqdm, message: str) -> None:
    """
    Affiche un message sans écraser la barre tqdm.
    Le verrou évite les collisions entre threads concurrents.
    """
    with _print_lock:
        progress_bar.write(message)


def load_and_filter_csv(csv_path: Path) -> pd.DataFrame:
    """Étape 1 & 2 — Lecture et filtrage du catalogue."""

    print(f"\n{'─'*58}")
    print("  ÉTAPE 1 — Lecture du catalogue")
    print(f"{'─'*58}")
    print(f"  Chemin : {csv_path}")

    if not csv_path.exists():
        print(f"\n[ERREUR FATALE] Fichier introuvable : {csv_path}")
        print("[CONSEIL] Vérifiez que listings.csv est bien dans data/raw/tabular/")
        raise FileNotFoundError(f"Fichier manquant : {csv_path}")

    df = pd.read_csv(csv_path, low_memory=False)
    print(f"[OK] CSV chargé — {len(df):,} lignes au total")

    # Validation des colonnes obligatoires
    missing = [c for c in [COL_ID, COL_URL] if c not in df.columns]
    if missing:
        raise ValueError(
            f"Colonnes manquantes : {missing}\n"
            f"Colonnes disponibles : {list(df.columns)}"
        )

    # Filtre géographique
    if FILTER_COLUMN in df.columns:
        df = df[df[FILTER_COLUMN].str.strip() == FILTER_VALUE].copy()
        print(f"[OK] Filtre — '{FILTER_VALUE}' : {len(df):,} lignes conservées")
    else:
        print(f"[ATTENTION] Colonne '{FILTER_COLUMN}' absente — aucun filtre appliqué")

    # Suppression des lignes sans URL
    avant = len(df)
    df = df.dropna(subset=[COL_URL])
    if len(df) < avant:
        print(f"[INFO] {avant - len(df)} ligne(s) sans URL supprimée(s)")

    print(f"[OK] {len(df):,} appartements à traiter\n")
    return df.reset_index(drop=True)


def process_one(row: pd.Series, progress_bar: tqdm, counters: dict) -> None:
    """
    Traite UN appartement : vérifie l'idempotence, télécharge,
    redimensionne et sauvegarde. Met à jour la barre et les compteurs.
    Appelée en parallèle par le ThreadPoolExecutor.
    """
    apartment_id = str(row[COL_ID]).strip()
    picture_url  = str(row[COL_URL]).strip()
    image_path   = OUTPUT_DIR / f"{apartment_id}.jpg"

    # ── Idempotence ──────────────────────────────────────────
    if image_path.exists():
        safe_print(progress_bar, f"  [SKIP]   {apartment_id}.jpg — déjà présent")
        with _print_lock:
            counters["skipped"] += 1
        progress_bar.update(1)
        return

    # ── Téléchargement + redimensionnement ───────────────────
    try:
        response = requests.get(picture_url, headers=HEADERS, timeout=TIMEOUT_SEC)
        response.raise_for_status()

        img = Image.open(BytesIO(response.content)).convert("RGB")
        img = img.resize(TARGET_SIZE, Image.LANCZOS)
        img.save(image_path, format="JPEG", quality=85, optimize=True)

        safe_print(progress_bar, f"  [OK]     {apartment_id}.jpg — {TARGET_SIZE[0]}×{TARGET_SIZE[1]}px")
        with _print_lock:
            counters["downloaded"] += 1

    except requests.exceptions.Timeout:
        safe_print(progress_bar, f"  [ERREUR] Timeout pour l'ID {apartment_id} — requête trop longue")
        with _print_lock:
            counters["errors"] += 1

    except requests.exceptions.HTTPError as e:
        code = e.response.status_code if e.response is not None else "?"
        labels = {404: "introuvable", 403: "accès refusé", 410: "supprimé"}
        detail = labels.get(code, "erreur serveur")
        safe_print(progress_bar, f"  [ERREUR] Lien mort pour l'ID {apartment_id} — HTTP {code} ({detail})")
        with _print_lock:
            counters["errors"] += 1

    except requests.exceptions.ConnectionError:
        safe_print(progress_bar, f"  [ERREUR] Connexion impossible pour l'ID {apartment_id}")
        with _print_lock:
            counters["errors"] += 1

    except Exception as e:
        safe_print(progress_bar, f"  [ERREUR] Inattendue ID {apartment_id} : {type(e).__name__} — {e}")
        with _print_lock:
            counters["errors"] += 1

    finally:
        # La barre avance dans TOUS les cas (succès, skip ou erreur)
        progress_bar.update(1)


def run_ingestion() -> None:
    """Boucle principale — orchestre le téléchargement parallèle."""

    print("=" * 58)
    print("   INGESTION DES IMAGES — DATA LAKE  (Phase 1)")
    print(f"   Mode : {MAX_WORKERS} téléchargements en parallèle")
    print("=" * 58)
    print(f"  Racine projet : {ROOT}")

    # ── Chargement + filtrage ────────────────────────────────
    df = load_and_filter_csv(CSV_PATH)
    if df.empty:
        print("[ARRÊT] Aucune donnée à traiter après filtrage.")
        return

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    total = len(df)

    # ── Compteurs partagés entre threads ─────────────────────
    counters = {"downloaded": 0, "skipped": 0, "errors": 0}

    print(f"{'─'*58}")
    print(f"  ÉTAPE 2 — Téléchargement parallèle ({total:,} appartements)")
    print(f"  Sortie : {OUTPUT_DIR}")
    print(f"{'─'*58}\n")

    # ── Barre de progression tqdm ────────────────────────────
    start_time = time.time()

    with tqdm(
        total=total,
        desc="  Progression",
        unit="img",
        colour="green",
        dynamic_ncols=True,
        bar_format=(
            "  {desc}: {percentage:3.0f}%|{bar}| "
            "{n_fmt}/{total_fmt} images "
            "[{elapsed}<{remaining}, {rate_fmt}]"
        ),
    ) as progress_bar:

        # ── ThreadPoolExecutor : 10 workers en parallèle ─────
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            futures = [
                executor.submit(process_one, row, progress_bar, counters)
                for _, row in df.iterrows()
            ]
            # Attendre la fin de tous les futures
            for future in as_completed(futures):
                # Remonte les exceptions non interceptées (sécurité)
                future.result()

    elapsed = time.time() - start_time

    # ── Rapport final ────────────────────────────────────────
    print(f"\n{'═'*58}")
    print("   RAPPORT FINAL D'INGESTION")
    print(f"{'═'*58}")
    print(f"  Appartements ciblés   : {total:>6,}")
    print(f"  Images téléchargées   : {counters['downloaded']:>6,}  ✅")
    print(f"  Images déjà présentes : {counters['skipped']:>6,}  ⏭")
    print(f"  Erreurs / liens morts : {counters['errors']:>6,}  ❌")
    if total > 0:
        taux = (counters["downloaded"] + counters["skipped"]) / total * 100
        print(f"  Taux de succès        :  {taux:>5.1f} %")
    print(f"  Durée totale          :  {elapsed:>5.1f} s")
    if elapsed > 0 and counters["downloaded"] > 0:
        vitesse = counters["downloaded"] / elapsed
        print(f"  Vitesse moyenne       :  {vitesse:>5.1f} img/s")
    print(f"{'─'*58}")
    print(f"  Dossier images : {OUTPUT_DIR}")
    print(f"{'═'*58}\n")


# ── Point d'entrée ───────────────────────────────────────────
if __name__ == "__main__":
    run_ingestion()
