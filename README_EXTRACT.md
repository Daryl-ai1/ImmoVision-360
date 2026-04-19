1. Objectif de l’extraction

L’étape d’extraction consiste à sélectionner, à partir du fichier listings.csv, uniquement les données pertinentes pour répondre aux problématiques métier du projet ImmoVision 360.

Le dataset initial contient plus de 70 colonnes. Conserver l’ensemble de ces variables serait contre-productif : cela alourdirait les traitements, complexifierait l’analyse et introduirait du bruit.

L’objectif est donc de réduire la dimension des données en ne conservant que les variables utiles pour tester les hypothèses définies.

2. Réduction des données

Une sélection de colonnes a été effectuée afin de passer d’un dataset large (70+ colonnes) à un dataset ciblé (~10 colonnes).

Cette réduction permet :

d’améliorer les performances (temps de calcul, mémoire)
de simplifier les analyses
de se concentrer uniquement sur les variables explicatives

Les colonnes sélectionnées sont directement liées aux hypothèses métier du projet.

3. Hypothèse économique : concentration des biens

Question :
Le marché Airbnb correspond-il à une économie de partage ou à une industrialisation du logement ?

Colonnes utilisées :

price : prix par nuit
property_type : type de bien
room_type : type de location
availability_365 : disponibilité annuelle
calculated_host_listings_count : nombre de biens par hôte

Justification :

La variable calculated_host_listings_count est centrale : elle permet d’identifier les hôtes possédant plusieurs logements, indicateur d’une activité professionnelle.

Associée à availability_365, elle permet de détecter si les logements sont exploités en continu, ce qui est typique d’une logique commerciale.

Les variables price, property_type et room_type permettent d’analyser la structuration du marché (positionnement, standardisation, segmentation).

4. Hypothèse sociale : déshumanisation de l’accueil

Question :
Le lien social entre hôte et voyageur est-il remplacé par des processus automatisés ?

Colonnes utilisées :

host_response_time : délai de réponse
host_response_rate : taux de réponse

Justification :

Ces variables permettent d’évaluer le comportement des hôtes.

Un taux de réponse très élevé combiné à un temps de réponse très rapide peut indiquer une gestion professionnalisée (agences ou multi-propriétaires), contrairement à un hôte individuel dont la gestion est souvent moins standardisée.

Ces indicateurs seront complétés en phase Transform par une analyse des commentaires (NLP).

5. Hypothèse visuelle : standardisation des logements

Question :
Les logements présentent-ils une homogénéisation visuelle typique d’une logique de produit ?

Colonnes utilisées :

picture_url

Justification :

Le fichier CSV ne contient pas directement d’information exploitable sur l’aspect visuel.

La colonne picture_url permet d’accéder aux images des logements, qui seront analysées en phase Transform pour extraire des caractéristiques (features) visuelles.

6. Filtrage géographique

Seules les annonces situées dans le quartier de l’Élysée ont été conservées via la colonne :

neighbourhood_cleansed

Ce filtrage permet de :

concentrer l’analyse sur une zone précise
assurer la cohérence des comparaisons
répondre à la problématique locale (Ville de Paris)
7. Colonnes supprimées

Les autres colonnes du dataset ont été volontairement exclues pour plusieurs raisons :

Redondance : certaines variables contiennent des informations similaires
Non-pertinence métier : elles ne contribuent pas aux hypothèses étudiées
Complexité inutile : certaines données (ex : texte long, JSON d’équipements) ne sont pas utiles à ce stade
Performance : réduction du volume de données à traiter

Exemples de colonnes exclues :

descriptions longues (description, neighborhood_overview)
données techniques (scrape_id, last_scraped)
informations non exploitées (license, calendar_updated)
détails complexes (amenities en JSON)
8. Conclusion

L’extraction permet de transformer un dataset brut volumineux en un dataset ciblé, cohérent avec les objectifs analytiques du projet.

Cette étape est essentielle car elle conditionne la qualité :

des transformations futures (phase Silver)
des analyses Data Science (phase Gold)

Le dataset obtenu (filtered_elysee.csv) constitue ainsi une base propre, structurée et orientée métier pour la suite du pipeline.