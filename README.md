# Olist — analyse des livraisons

Pipeline de données utilisant Python, des fichiers CSV locaux et PostgreSQL.
Objectif : préparer des données fiables pour mesurer les retards de livraison par État brésilien.

## Architecture
CSV locaux → validation Python → tables PostgreSQL → vue analytique → requêtes SQL.
Trois tables relationnelles : customers, orders, order_items.
La vue delivery_analysis contient une ligne par commande. Ce projet utilise un modèle relationnel
et une vue analytique, pas un entrepôt en étoile complet.

## Données

Les trois CSV d’origine sont inclus directement dans `data/` :

- `olist_customers_dataset.csv` : clients
- `olist_orders_dataset.csv` : commandes
- `olist_order_items_dataset.csv` : articles par commande

Source : [Brazilian E-Commerce Public Dataset by Olist](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce).
Les CSV sont reproduits sans modification sous [CC BY-NC-SA 4.0](https://creativecommons.org/licenses/by-nc-sa/4.0/).
Aucun téléchargement ni appel API n’est nécessaire pour exécuter le projet.

## Démarrage sur Windows
Prérequis : Python 3.12 ou 3.13, Docker Desktop lancé avec les conteneurs Linux.
Ouvrir ce dossier dans VS Code, puis exécuter dans PowerShell :

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
Copy-Item .env.example .env
```

Modifier PGPASSWORD dans .env avant le premier démarrage. Ce fichier reste local.
Le port local utilisé est 5433 pour éviter le PostgreSQL déjà installé sur 5432.

```powershell
docker compose up -d --wait
.\.venv\Scripts\python.exe pipeline.py --validate-only
.\.venv\Scripts\python.exe pipeline.py
Get-Content sql/analysis.sql | docker compose exec -T db psql -U olist -d olist
```

Si tu modifies PGUSER ou PGDATABASE, adapter aussi la dernière commande.
Pour arrêter : docker compose stop. Les données restent dans le volume Docker.

## Lire le code

`pipeline.py` utilise des fonctions simples, sans classes. Commencer par `main()` :
elle lit les trois fichiers, vérifie les liens entre les tables, puis appelle
`load_postgres()` si le chargement est demandé.

## Contrôles et comportement
- Colonnes obligatoires, clés uniques, montants valides non négatifs.
- Dates au format attendu, clés étrangères cohérentes.
- Une date de livraison absente est autorisée (commande non livrée ou donnée manquante).
- Une anomalie bloquante arrête le chargement ; elle est affichée avec son fichier et sa ligne si applicable.
- Relancer remplace les trois tables de données dans une transaction : pas de cumul de doublons.
- Un échec de chargement annule toutes les modifications de cette transaction.
- Les fichiers sont chargés en mémoire : adapté au dataset Olist, pas aux volumes massifs.

## Indicateurs
- Taux de retard parmi les commandes livrées dont la date de livraison est connue.
- Délai moyen de livraison, comparaison par État.
- Valeur des articles des commandes livrées par mois (hors transport, pas du revenu net).
Une livraison le jour promis ne compte pas comme en retard.
Les montants des articles sont agrégés avant jointure pour éviter les doubles comptages.

## Tests
```powershell
.\.venv\Scripts\python.exe -m tests.test_pipeline
```

Les tests couvrent les montants invalides, doublons, références orphelines et dates absentes.
## Résultats sur les données Olist

Sur 99 441 commandes, 96 470 ont le statut livré et une date de livraison renseignée.
Parmi ces livraisons, 6 534 dépassent la date promise, soit **6,77 %**.
Le délai moyen est de 12,50 jours et la médiane de 10 jours.

| État | Livraisons analysables | Retards | Taux |
| --- | ---: | ---: | ---: |
| São Paulo | 40 494 | 1 820 | 4,49 % |
| Rio de Janeiro | 12 350 | 1 495 | 12,11 % |
| Alagoas | 397 | 85 | 21,41 % |

São Paulo concentre le plus de retards en nombre parmi ces trois États.
Alagoas affiche le taux le plus élevé de cette sélection, sur un effectif plus faible.
Ces résultats descriptifs ont été recalculés en Python à partir des CSV d’origine,
selon les règles de la vue SQL. Ils ne permettent pas d’attribuer les retards à une cause.

## Provenance et limites
Implémentation originale préparée avec assistance IA pour Ayoub Joubair.
Source des données : Olist.
Pas d'Airflow, pas de cloud et pas d'API : priorité à un pipeline local compréhensible.
Avant de présenter le projet en entretien, exécuter le pipeline et savoir expliquer ses contrôles,
le grain de la vue et le calcul des indicateurs.
