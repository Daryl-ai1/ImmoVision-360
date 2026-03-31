# ImmoVision 360 — Data Lake (Bronze Layer)

## 1. Titre et Contexte

Ce projet s’inscrit dans la mission de création du Data Lake pour ImmoVision 360.
L’objectif est de construire une architecture de stockage permettant d’ingérer, organiser et préparer des données hétérogènes (tabulaires, images et textes) en vue d’analyses futures en Data Science, Computer Vision et NLP.

Les données utilisées proviennent de la plateforme InsideAirbnb (Open Data) et comprennent :

* listings.csv : informations sur les logements
* reviews.csv : commentaires des utilisateurs
* picture_url : liens vers les images des logements

Le Data Lake Bronze doit contenir les données brutes organisées de manière structurée pour les futures phases Silver et Gold.

---

## 2. Structure du Répertoire

Voici l’arborescence du projet et l’organisation du Data Lake :

```
ImmoVision360_DataLake/
│
├── data/
│   └── raw/
│       ├── tabular/
│       │   ├── listings.csv
│       │   └── reviews.csv
│       │
│       ├── images/
│       │   └── (images téléchargées .jpg)
│       │
│       └── texts/
│           └── (fichiers texte des commentaires .txt)
│
├── scripts/
│   ├── 00_data.ipynb
│   ├── 01_ingestion_images.py
│   ├── 02_ingestion_textes.py
│   └── 03_sanity_check.py
│
├── README.md
└── .gitignore
```

Cette architecture correspond à la couche **Bronze** du Data Lake, où les données sont stockées dans leur format brut mais organisées par type.

---

## 3. Notice d’Exécution (Pipeline d’Ingestion)

### Étape 1 — Créer un environnement virtuel

```
python -m venv myenv
myenv\scripts\activate
```

### Étape 2 — Installer les dépendances

```
pip install pandas requests pillow tqdm
```

### Étape 3 — Ingestion des images

```
python scripts/01_ingestion_images.py
```

Ce script :

* Lit le fichier listings.csv
* Filtre les annonces du quartier Élysée
* Télécharge les images depuis les URLs
* Redimensionne les images en 320x320 pixels
* Sauvegarde les images dans data/raw/images/
* Vérifie l’idempotence (ne retélécharge pas les images existantes)
* Gère les erreurs réseau (timeout, 404, etc.)

### Étape 4 — Ingestion des textes

```
python scripts/02_ingestion_textes.py
```

Ce script :

* Charge listings.csv pour récupérer les annonces du quartier Élysée
* Charge reviews.csv
* Filtre les commentaires correspondant aux annonces sélectionnées
* Nettoie le texte (suppression HTML)
* Regroupe les commentaires par listing_id
* Crée un fichier texte par annonce dans data/raw/texts/

### Étape 5 — Sanity Check du Data Lake

```
python scripts/03_sanity_check.py
```

Ce script vérifie :

* Le nombre d’images téléchargées
* Le nombre de fichiers texte générés
* Le nombre d’IDs communs entre images et textes
* Le taux de réussite du pipeline d’ingestion

---

## 4. Audit des Données (Résultats du Sanity Check)

Exemple de résultats obtenus après ingestion :

* Nombre de listings (quartier Élysée) : XXXX
* Nombre d’images téléchargées : XXXX
* Nombre de fichiers textes générés : XXXX
* Nombre d’IDs communs images/textes : XXXX
* Nombre d’erreurs images : XXXX
* Nombre d’erreurs textes : XXXX

Taux de réussite ingestion images :

```
Images téléchargées =  1,777
Erreurs =  848
```
Taux de réussite ingestion images : 67.7 %

```
nombres de fichiers texte = 1,965
Erreurs =  660

Taux de réussite ingestion textes : 74.8 %
```

Taux de réussite ingestion Image + Texte = 51.3 %


Ces métriques permettent de mesurer la qualité et la complétude du Data Lake Bronze.

---

## 5. Analyse des Pertes de Données

 Le fichier listings.csv contient 2 625 annonces dans le périmètre du quartier Élysée. Cependant, seulement 1 777 images ont pu être téléchargées. Cette déperdition s’explique par plusieurs raisons techniques : certains liens d’images présents dans le dataset sont expirés ou invalides (erreurs HTTP 404), certains serveurs bloquent les requêtes automatisées (anti-bot), et certaines requêtes ont échoué à cause de timeouts réseau ou d’erreurs serveurs (HTTP 500).
Concernant les données textuelles, certaines annonces ne possèdent tout simplement aucun commentaire dans reviews.csv, ce qui explique l’absence de fichier texte pour ces annonces. Ces pertes sont normales dans un pipeline d’ingestion de données réelles et ont été prises en compte dans l’audit du Data Lake.