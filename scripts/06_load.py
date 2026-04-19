import os
import pandas as pd
from sqlalchemy import create_engine
from dotenv import load_dotenv

# ================================
# CONFIG SECURISÉE (.env)
# ================================

load_dotenv()

DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME")

# ================================
# PATH DATA
# ================================

INPUT_PATH = "data/processed/transformed_elysee.csv"

# ================================
# LOAD DATA
# ================================

def main():
    print("Chargement des données Silver...")

    df = pd.read_csv(INPUT_PATH)

    print(f"Nombre de lignes : {len(df)}")

    # ================================
    # CONNECTION POSTGRESQL
    # ================================

    engine = create_engine(
        f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    )

    # ================================
    # LOAD INTO DATA WAREHOUSE
    # ================================

    df.to_sql(
        "elysee_listings_silver",
        engine,
        if_exists="replace",
        index=False
    )

    print("Chargement terminé dans PostgreSQL.")

# ================================
# EXECUTION
# ================================

if __name__ == "__main__":
    main()