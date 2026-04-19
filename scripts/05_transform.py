import os
import time
import pandas as pd
import numpy as np
import PIL.Image
from dotenv import load_dotenv
import google.generativeai as genai
import google.api_core.exceptions as exceptions

# ================================
# CONFIGURATION API
# ================================

load_dotenv()
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

model = genai.GenerativeModel("gemini-2.5-flash")

# ================================
# PATHS
# ================================

INPUT_PATH = "data/processed/filtered_elysee.csv"
OUTPUT_PATH = "data/processed/transformed_elysee.csv"

IMAGES_PATH = "data/raw/images"
TEXTS_PATH = "data/raw/texts"

# ================================
# PROMPTS
# ================================

IMAGE_PROMPT = """
Analyse cette image et classe-la strictement dans UNE catégorie :

- Appartement industrialisé (standardisé, style hôtel, froid)
- Appartement personnel (vivant, décoré, humain)
- Autre

Réponds uniquement par la catégorie.
"""

TEXT_PROMPT = """
Analyse ce texte de commentaires Airbnb.

Classe dans UNE catégorie :

- Hôtélisé (process industriel, boîte à clés, peu humain)
- Voisinage naturel (interaction humaine, conseils locaux)

Réponds uniquement par la catégorie.
"""

# ================================
# IA CALL AVEC GESTION D'ERREURS
# ================================

def call_gemini(content, is_image=True):
    try:
        if is_image:
            response = model.generate_content([IMAGE_PROMPT, content])
        else:
            response = model.generate_content(TEXT_PROMPT + "\n\n" + content)

        return response.text.strip()

    except exceptions.ResourceExhausted:
        time.sleep(60)
        return "Error"

    except Exception:
        return "Error"

# ================================
# MAPPING FEATURES
# ================================

def map_image(label):
    if label == "Appartement industrialisé":
        return 1
    elif label == "Appartement personnel":
        return 0
    else:
        return -1


def map_text(label):
    if label == "Hôtélisé":
        return 1
    elif label == "Voisinage naturel":
        return 0
    else:
        return -1

# ================================
# PIPELINE PRINCIPAL
# ================================

def main():
    df = pd.read_csv(INPUT_PATH)

    image_scores = []
    text_scores = []

    for i, row in df.iterrows():

        # IMAGE FEATURE
        img_path = os.path.join(IMAGES_PATH, f"{row['id']}.jpg")

        if os.path.exists(img_path):
            try:
                img = PIL.Image.open(img_path)
                label = call_gemini(img, is_image=True)
                image_scores.append(map_image(label))
            except:
                image_scores.append(-1)
        else:
            image_scores.append(-1)

        # TEXT FEATURE
        txt_path = os.path.join(TEXTS_PATH, f"{row['id']}.txt")

        if os.path.exists(txt_path):
            try:
                with open(txt_path, "r", encoding="utf-8") as f:
                    text = f.read()

                label = call_gemini(text, is_image=False)
                text_scores.append(map_text(label))

            except:
                text_scores.append(-1)
        else:
            text_scores.append(-1)

        # CHECKPOINT
        if i % 50 == 0:
            temp = df.copy()
            temp["Standardization_Score"] = image_scores + [-1] * (len(df) - len(image_scores))
            temp["Neighborhood_Impact"] = text_scores + [-1] * (len(df) - len(text_scores))
            temp.to_csv(OUTPUT_PATH, index=False)

    # FINAL SAVE
    df["Standardization_Score"] = image_scores
    df["Neighborhood_Impact"] = text_scores

    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    df.to_csv(OUTPUT_PATH, index=False)

    print("Transformation terminee")

# ================================
# EXECUTION
# ================================

if __name__ == "__main__":
    main()