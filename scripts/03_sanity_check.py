"""
scripts/03_sanity_check.py
==========================
Phase 1 — Contrôle Qualité du Data Lake
Vérifie la cohérence entre le catalogue CSV et les fichiers physiques.

Arborescence du projet :
    IMMO.../
    ├── data/
    │   └── raw/
    │       ├── images/              ← vérifié par ce script
    │       ├── texts/               ← vérifié par ce script
    │       └── tabular/
    │           ├── listings.csv     ← source de vérité
    │           └── reviews.csv      ← source de vérité
    ├── myenv/
    └── scripts/
        ├── 01_ingestion_images.py
        ├── 02_ingestion_textes.py
        └── 03_sanity_check.py       ← CE fichier

Lancement :
    python scripts/03_sanity_check.py
    python scripts/03_sanity_check.py --orphelins 20   # affiche 20 orphelins max

Dépendances :
    pip install pandas
"""

import argparse
import pandas as pd
from pathlib import Path
from datetime import datetime

# ══════════════════════════════════════════════════════════════
#  RÉSOLUTION DE LA RACINE DU PROJET
# ══════════════════════════════════════════════════════════════

ROOT = Path(__file__).resolve().parent.parent

# ══════════════════════════════════════════════════════════════
#  CONFIGURATION
# ══════════════════════════════════════════════════════════════

LISTINGS_CSV = ROOT / "data" / "raw" / "tabular" / "listings.csv"
REVIEWS_CSV  = ROOT / "data" / "raw" / "tabular" / "reviews.csv"
IMAGES_DIR   = ROOT / "data" / "raw" / "images"
TEXTS_DIR    = ROOT / "data" / "raw" / "texts"

# Filtre géographique (doit correspondre à 01_ingestion_images.py)
FILTER_COLUMN = "neighbourhood_cleansed"
FILTER_VALUE  = "Élysée"

COL_ID         = "id"
COL_LISTING_ID = "listing_id" 

# Nombre max d'orphelins affichés par défaut
DEFAULT_ORPHELINS = 10

# ══════════════════════════════════════════════════════════════


def separateur(car="─", largeur=60):
    return car * largeur


def titre(texte, car="═", largeur=60):
    print(separateur(car, largeur))
    print(f"  {texte}")
    print(separateur(car, largeur))


# ─────────────────────────────────────────────────────────────
#  BLOC 1 — COMPTAGE THÉORIQUE (CSV)
# ─────────────────────────────────────────────────────────────

def check_listings_csv(max_orphelins: int) -> dict:
    """
    Étape 1 : Lit listings.csv, applique le filtre géographique,
    extrait les IDs attendus.
    Étape 3 : Jointure physique — vérifie chaque ID sur le disque.
    """
    print(f"\n{separateur()}")
    print("  BLOC 1 — Analyse des IMAGES (listings.csv ↔ /images/)")
    print(separateur())

    result = {
        "csv_ok": False,
        "ids_attendus": set(),
        "nb_attendu": 0,
        "nb_physique": 0,
        "nb_presents": 0,
        "nb_orphelins": 0,
        "orphelins": [],
        "fantomes": [],      # .jpg présents sur disque mais absents du CSV
    }

    # ── Lecture du CSV ────────────────────────────────────────
    if not LISTINGS_CSV.exists():
        print(f"[ERREUR] listings.csv introuvable : {LISTINGS_CSV}")
        return result

    try:
        df = pd.read_csv(LISTINGS_CSV, low_memory=False, usecols=lambda c: c in [
            COL_ID, FILTER_COLUMN
        ])
    except Exception as e:
        print(f"[ERREUR] Lecture impossible : {e}")
        return result

    result["csv_ok"] = True
    nb_total_csv = len(df)
    print(f"  [OK] listings.csv chargé — {nb_total_csv:,} annonces au total")

    # ── Application du filtre géographique ───────────────────
    if FILTER_COLUMN in df.columns:
        df = df[df[FILTER_COLUMN].str.strip() == FILTER_VALUE].copy()
        print(f"  [OK] Filtre '{FILTER_VALUE}' appliqué — {len(df):,} annonces ciblées")
    else:
        print(f"  [ATTENTION] Colonne '{FILTER_COLUMN}' absente — tous les IDs pris en compte")

    # ── Extraction des IDs attendus ───────────────────────────
    ids_attendus = set(df[COL_ID].dropna().astype(int).tolist())
    result["ids_attendus"] = ids_attendus
    result["nb_attendu"]   = len(ids_attendus)

    # ── Comptage physique du dossier /images/ ─────────────────
    if not IMAGES_DIR.exists():
        print(f"  [ERREUR] Dossier images introuvable : {IMAGES_DIR}")
        return result

    jpg_sur_disque = {int(f.stem) for f in IMAGES_DIR.glob("*.jpg") if f.stem.isdigit()}
    result["nb_physique"] = len(jpg_sur_disque)

    # ── Jointure physique (test ultime) ───────────────────────
    presents  = ids_attendus & jpg_sur_disque      # dans CSV ET sur disque ✅
    orphelins = ids_attendus - jpg_sur_disque      # dans CSV mais PAS sur disque ❌
    fantomes  = jpg_sur_disque - ids_attendus      # sur disque mais PAS dans CSV 👻

    result["nb_presents"]  = len(presents)
    result["nb_orphelins"] = len(orphelins)
    result["orphelins"]    = sorted(orphelins)[:max_orphelins]
    result["fantomes"]     = sorted(fantomes)[:max_orphelins]

    return result


# ─────────────────────────────────────────────────────────────
#  BLOC 2 — CONTRÔLE DES TEXTES (reviews.csv ↔ /texts/)
# ─────────────────────────────────────────────────────────────

def check_reviews_csv(max_orphelins: int) -> dict:
    """
    Vérifie la cohérence entre reviews.csv et les fichiers .txt générés.
    """
    print(f"\n{separateur()}")
    print("  BLOC 2 — Analyse des TEXTES (reviews.csv ↔ /texts/)")
    print(separateur())

    result = {
        "csv_ok": False,
        "nb_listing_ids_csv": 0,
        "nb_txt_disque": 0,
        "nb_presents": 0,
        "nb_orphelins": 0,
        "orphelins": [],
    }

    if not REVIEWS_CSV.exists():
        print(f"  [ATTENTION] reviews.csv introuvable : {REVIEWS_CSV}")
        print("  [INFO] Bloc textes ignoré.")
        return result

    try:
        df = pd.read_csv(REVIEWS_CSV, low_memory=False, usecols=[COL_LISTING_ID])
    except Exception as e:
        print(f"  [ERREUR] Lecture reviews.csv impossible : {e}")
        return result

    result["csv_ok"] = True
    ids_reviews = set(df[COL_LISTING_ID].dropna().astype(int).tolist())
    result["nb_listing_ids_csv"] = len(ids_reviews)
    print(f"  [OK] reviews.csv chargé — {len(df):,} avis / {len(ids_reviews):,} annonces distinctes")

    if not TEXTS_DIR.exists():
        print(f"  [ERREUR] Dossier texts introuvable : {TEXTS_DIR}")
        return result

    txt_sur_disque = {int(f.stem) for f in TEXTS_DIR.glob("*.txt") if f.stem.isdigit()}
    result["nb_txt_disque"] = len(txt_sur_disque)

    presents  = ids_reviews & txt_sur_disque
    orphelins = ids_reviews - txt_sur_disque

    result["nb_presents"]  = len(presents)
    result["nb_orphelins"] = len(orphelins)
    result["orphelins"]    = sorted(orphelins)[:max_orphelins]

    return result


# ─────────────────────────────────────────────────────────────
#  BLOC 3 — JOINTURE CROISÉE images ↔ textes
# ─────────────────────────────────────────────────────────────

def check_cross_join() -> dict:
    """
    Vérifie combien d'annonces ont À LA FOIS leur .jpg ET leur .txt.
    C'est ce chiffre qui représente les annonces 100% prêtes pour la Phase 2.
    """
    print(f"\n{separateur()}")
    print("  BLOC 3 — Jointure croisée IMAGES ↔ TEXTES")
    print(separateur())

    result = {"nb_complets": 0, "nb_image_seule": 0, "nb_texte_seul": 0}

    if not IMAGES_DIR.exists() or not TEXTS_DIR.exists():
        print("  [ATTENTION] Un ou deux dossiers manquants — jointure impossible")
        return result

    ids_jpg = {int(f.stem) for f in IMAGES_DIR.glob("*.jpg") if f.stem.isdigit()}
    ids_txt = {int(f.stem) for f in TEXTS_DIR.glob("*.txt")  if f.stem.isdigit()}

    complets      = ids_jpg & ids_txt
    image_seule   = ids_jpg - ids_txt
    texte_seul    = ids_txt - ids_jpg

    result["nb_complets"]    = len(complets)
    result["nb_image_seule"] = len(image_seule)
    result["nb_texte_seul"]  = len(texte_seul)

    print(f"  IDs avec .jpg ET .txt  : {len(complets):>6,}  ✅ (prêts Phase 2)")
    print(f"  IDs avec .jpg seulement: {len(image_seule):>6,}  ⚠️  (texte manquant)")
    print(f"  IDs avec .txt seulement: {len(texte_seul):>6,}  ⚠️  (image manquante)")

    return result


# ─────────────────────────────────────────────────────────────
#  RAPPORT FINAL
# ─────────────────────────────────────────────────────────────

def print_rapport(images: dict, textes: dict, cross: dict, max_orphelins: int):
    """Affiche le rapport de sanity check complet et structuré."""

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    print(f"\n\n{'═'*60}")
    print(f"  RAPPORT DE SANITY CHECK — DATA LAKE")
    print(f"  Généré le : {now}")
    print(f"{'═'*60}")

    # ── Section Images ────────────────────────────────────────
    print(f"\n  {'▌ IMAGES':}")
    print(f"  {'─'*56}")

    if not images["csv_ok"]:
        print("  ❌ listings.csv inaccessible — vérification impossible")
    else:
        nb_att  = images["nb_attendu"]
        nb_phy  = images["nb_physique"]
        nb_pres = images["nb_presents"]
        nb_orp  = images["nb_orphelins"]
        taux    = (nb_pres / nb_att * 100) if nb_att > 0 else 0.0

        print(f"  Total annonces dans le CSV (filtre '{FILTER_VALUE}') : {nb_att:>6,}")
        print(f"  Total fichiers .jpg sur le disque                    : {nb_phy:>6,}")
        print(f"  IDs CSV trouvés physiquement                         : {nb_pres:>6,}  ✅")
        print(f"  IDs CSV manquants sur le disque (orphelins)          : {nb_orp:>6,}  ❌")
        print(f"  {'─'*56}")

        # Barre de progression textuelle
        filled = int(taux / 2)
        bar = "█" * filled + "░" * (50 - filled)
        print(f"  Taux de complétion : [{bar}] {taux:.1f} %")

        # Statut global
        if taux == 100.0:
            print(f"\n  ✅ PARFAIT — Toutes les images sont présentes.")
        elif taux >= 90.0:
            print(f"\n  ⚠️  ACCEPTABLE — {nb_orp} image(s) manquante(s). Relancez 01_ingestion_images.py.")
        else:
            print(f"\n  ❌ INCOMPLET — {nb_orp} image(s) manquante(s). Ingestion à relancer.")

        # Liste des orphelins
        if images["orphelins"]:
            affichés = len(images["orphelins"])
            print(f"\n  🔍 Premiers orphelins ({affichés} affichés sur {nb_orp}) :")
            for oid in images["orphelins"]:
                print(f"     • ID {oid} → {IMAGES_DIR / f'{oid}.jpg'} ABSENT")
            if nb_orp > max_orphelins:
                print(f"     ... et {nb_orp - max_orphelins} autres.")

        # Fichiers fantômes (sur disque mais pas dans le CSV)
        if images["fantomes"]:
            print(f"\n  👻 Fichiers fantômes ({len(images['fantomes'])} affichés) :")
            print("     (présents sur disque mais absents du CSV — peuvent être supprimés)")
            for fid in images["fantomes"]:
                print(f"     • {fid}.jpg")

    # ── Section Textes ────────────────────────────────────────
    print(f"\n  {'▌ TEXTES':}")
    print(f"  {'─'*56}")

    if not textes["csv_ok"]:
        print("  ⚠️  reviews.csv inaccessible — section textes ignorée")
    else:
        nb_ids  = textes["nb_listing_ids_csv"]
        nb_txt  = textes["nb_txt_disque"]
        nb_pres = textes["nb_presents"]
        nb_orp  = textes["nb_orphelins"]
        taux    = (nb_pres / nb_ids * 100) if nb_ids > 0 else 0.0

        print(f"  Annonces distinctes dans reviews.csv : {nb_ids:>6,}")
        print(f"  Fichiers .txt sur le disque          : {nb_txt:>6,}")
        print(f"  IDs avec fichier .txt présent        : {nb_pres:>6,}  ✅")
        print(f"  IDs sans fichier .txt (orphelins)    : {nb_orp:>6,}  ❌")
        print(f"  {'─'*56}")

        filled = int(taux / 2)
        bar = "█" * filled + "░" * (50 - filled)
        print(f"  Taux de complétion : [{bar}] {taux:.1f} %")

        if textes["orphelins"]:
            print(f"\n  🔍 Premiers orphelins textes ({len(textes['orphelins'])} affichés) :")
            for oid in textes["orphelins"]:
                print(f"     • ID {oid} → {TEXTS_DIR / f'{oid}.txt'} ABSENT")

    # ── Section Jointure croisée ──────────────────────────────
    print(f"\n  {'▌ JOINTURE PHASE 2 (image + texte)':}")
    print(f"  {'─'*56}")
    print(f"  Annonces 100% complètes (.jpg + .txt) : {cross['nb_complets']:>6,}  ✅")
    print(f"  Image sans texte                       : {cross['nb_image_seule']:>6,}  ⚠️")
    print(f"  Texte sans image                       : {cross['nb_texte_seul']:>6,}  ⚠️")

    total_dispo = cross["nb_complets"]
    if total_dispo > 0:
        print(f"\n  ✅ {total_dispo:,} annonce(s) prête(s) pour la Phase 2 (NLP + Vision).")
    else:
        print(f"\n  ❌ Aucune annonce complète. Relancez les scripts 01 et 02.")

    print(f"\n{'═'*60}\n")


# ─────────────────────────────────────────────────────────────
#  POINT D'ENTRÉE
# ─────────────────────────────────────────────────────────────

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Sanity Check — contrôle qualité du Data Lake"
    )
    parser.add_argument(
        "--orphelins",
        type=int,
        default=DEFAULT_ORPHELINS,
        metavar="N",
        help=f"Nombre max d'IDs orphelins à afficher (défaut : {DEFAULT_ORPHELINS})",
    )
    return parser.parse_args()


def run_sanity_check(max_orphelins: int = DEFAULT_ORPHELINS) -> None:

    print("=" * 60)
    print("   SANITY CHECK — DATA LAKE  (Phase 1)")
    print("=" * 60)
    print(f"  Racine projet : {ROOT}")

    images = check_listings_csv(max_orphelins)
    textes = check_reviews_csv(max_orphelins)
    cross  = check_cross_join()

    print_rapport(images, textes, cross, max_orphelins)


if __name__ == "__main__":
    args = parse_args()
    run_sanity_check(max_orphelins=args.orphelins)
