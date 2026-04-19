import pandas as pd
import os

INPUT_PATH = "data/raw/tabular/listings.csv"
OUTPUT_PATH = "data/processed/filtered_elysee.csv"

# Colonnes utiles selon hypothèses métier
COLS_TO_KEEP = [
    "id",
    "neighbourhood_cleansed",          # filtre géographique

    "price",                           # hypothèse économique
    "property_type",                   # hypothèse économique
    "room_type",                       # hypothèse économique
    "availability_365",                # hypothèse économique
    "calculated_host_listings_count",  # hypothèse économique

    "host_response_time",              # hypothèse sociale
    "host_response_rate",              # hypothèse sociale

    "picture_url"                      # lien image (transform)
]


def main():
    # Chargement
    df = pd.read_csv(INPUT_PATH)

    # Sélection des colonnes
    df = df[COLS_TO_KEEP]

    # Filtrage quartier Élysée
    df = df[df["neighbourhood_cleansed"] == "Élysée"]

    # Nettoyage prix (€ → float)
    df["price"] = df["price"].replace(r"[\$,]", "", regex=True).astype(float)

    # Nettoyage taux réponse (% → float)
    df["host_response_rate"] = df["host_response_rate"].str.replace("%", "", regex=False)
    df["host_response_rate"] = pd.to_numeric(df["host_response_rate"], errors="coerce")

    # Création dossier si besoin
    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)

    # Sauvegarde
    df.to_csv(OUTPUT_PATH, index=False)

    print("✅ filtered_elysee.csv généré")


if __name__ == "__main__":
    main()