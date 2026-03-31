import os
import pandas as pd
import re

# Chemins
LISTINGS_PATH = "data/raw/tabular/listings.csv"
REVIEWS_PATH = "data/raw/tabular/reviews.csv"
TEXTS_FOLDER = "data/raw/texts/"

# Création dossier texts
os.makedirs(TEXTS_FOLDER, exist_ok=True)

# Lecture listings
listings = pd.read_csv(LISTINGS_PATH)

# Filtrer quartier Elysée
elysee_listings = listings[listings["neighbourhood_cleansed"].str.contains("lys", case=False, na=False)]

# Liste des IDs
elysee_ids = set(elysee_listings["id"])

print("Nombre d'annonces Elysée :", len(elysee_ids))

# Lecture reviews
reviews = pd.read_csv(REVIEWS_PATH)

# Filtrer reviews
reviews_elysee = reviews[reviews["listing_id"].isin(elysee_ids)]

print("Nombre de reviews Elysée :", len(reviews_elysee))

# Nettoyage HTML
def clean_text(text):
    text = str(text)
    text = re.sub(r'<.*?>', '', text)  # enlever HTML
    text = text.replace("\n", " ")
    return text

reviews_elysee["comments"] = reviews_elysee["comments"].apply(clean_text)

# Grouper par listing_id
grouped = reviews_elysee.groupby("listing_id")["comments"].apply(list)

# Écriture fichiers txt
for listing_id, comments in grouped.items():
    file_path = os.path.join(TEXTS_FOLDER, f"{listing_id}.txt")

    # Idempotence
    if os.path.exists(file_path):
        print(f"Fichier déjà existant : {listing_id}")
        continue

    try:
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(f"Commentaires pour l'annonce {listing_id}:\n\n")

            for comment in comments:
                f.write(f"- {comment}\n")

        print(f"Fichier créé : {listing_id}.txt")

    except Exception as e:
        print(f"Erreur pour {listing_id} : {e}")