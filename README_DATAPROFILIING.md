# README_DATAPROFILING.md

## 🎯 Objectif

Avant de lancer le pipeline de transformation (05_transform.py), une phase de **data profiling** a été réalisée sur le fichier :

```
data/processed/filtered_elysee.csv
```

L’objectif est de :

* comprendre la structure des données
* détecter les anomalies
* définir des règles de nettoyage pertinentes
* éviter toute transformation “à l’aveugle”

---

## 📊 1. Structure du dataset

Le dataset filtré contient uniquement les colonnes utiles aux hypothèses métier :

* Économique : price, availability_365, calculated_host_listings_count, etc.
* Sociale : host_response_rate, reviews_per_month, etc.
* Géographique : neighbourhood, latitude, longitude
* Technique : id, picture_url

---

## ⚠️ 2. Données manquantes (NaN)

Analyse réalisée avec :

```python
df.isna().sum()
```

### Observations :

* `host_response_rate` : présence de valeurs manquantes
* `host_response_time` : partiellement vide
* `reviews_per_month` : NaN fréquents (logements récents sans avis)
* `price` : généralement bien rempli (critique)

### Interprétation :

* Les NaN ne sont pas forcément des erreurs :

  * `reviews_per_month = NaN` → logement neuf → logique
  * `host_response_rate = NaN` → hôte inactif ou peu sollicité

---

## 📈 3. Statistiques descriptives

Analyse réalisée avec :

```python
df.describe()
```

### Points clés :

* `price` :

  * min potentiellement très bas (voire 0)
  * max élevé → possible outlier
* `availability_365` :

  * valeurs entre 0 et 365 (logique)
* `calculated_host_listings_count` :

  * forte dispersion → présence d’acteurs professionnels

---

## 🚨 4. Valeurs aberrantes (Outliers)

### Cas détectés :

* prix = 0 → incohérent → probablement erreur
* prix très élevés (> 5000) → biens atypiques ou erreurs
* availability_365 = 0 → logement jamais disponible

### Risques :

* biais dans les modèles
* mauvaise interprétation économique

---

## 🔄 5. Formats & types de données

### Problèmes identifiés :

* `price` : souvent stocké comme string (ex: "$120.00")
* `host_response_rate` : format string avec `%`
* certaines colonnes numériques mal typées

### Actions nécessaires :

* conversion en float
* nettoyage des symboles ($, %, etc.)

---

## 🧠 6. Décisions de traitement

### 🔹 Suppression (drop)

* supprimer lignes avec :

  * `price` manquant
  * `id` manquant

👉 données critiques

---

### 🔹 Imputation logique

* `reviews_per_month` → remplacer NaN par **0**

  * justification : logement sans avis

---

### 🔹 Imputation statistique

* `host_response_rate` → médiane

  * évite biais extrêmes

---

### 🔹 Nettoyage / transformation

* `price` → convertir en float
* `host_response_rate` → convertir en ratio (0–1)

---

### 🔹 Gestion des outliers

* cap des valeurs extrêmes :

  * price > seuil (ex: 1000 ou percentile 99)
  * éviter influence disproportionnée

---

## ✅ Conclusion

Cette phase de data profiling a permis de :

* identifier les anomalies
* comprendre la logique métier derrière les données
* définir des règles de transformation cohérentes

👉 Le script **05_transform.py** appliquera ces décisions de manière automatisée et reproductible.

---

## 🚀 Prochaine étape

Transformation intelligente des données :

* images → features visuelles
* textes → analyse NLP
* création de variables enrichies

---
