# Systeme de livraison - Redis & MongoDB

Projet NoSQL utilisant Redis (temps reel) et MongoDB (historique/analyses) pour gerer un systeme de livraison.

## Prerequis

- Docker et Docker Compose
- [uv](https://docs.astral.sh/uv/) (gestionnaire de paquets Python)

## Mise en route

### 1. Lancer les bases de donnees

```bash
make up
```

Verifier que les conteneurs tournent :

```bash
docker ps
```

Vous devez voir `delivery_redis` (port 6380) et `delivery_mongo` (port 27018).

### 2. Charger les donnees initiales

```bash
make generate
```

Ce script :
- genere 20 livreurs (4 de base + 16 generes)
- genere 20 commandes (4 de base + 16 generees)
- genere 34 livraisons historiques (4 de base + 30 generees)
- charge tout dans Redis et MongoDB

## Commandes metier Redis

Le projet expose une CLI modulaire :

```bash
python -m delivery_system.cli --help
```

Exemples :

```bash
python -m delivery_system.cli assign --order c1 --driver d3
python -m delivery_system.cli report
python -m delivery_system.cli complete --order c1 --driver d3
python -m delivery_system.cli dashboard
python -m delivery_system.cli demo --order c1 --driver d3
```

## Analyses MongoDB

Le projet expose une CLI dediee aux analyses MongoDB :

```bash
uv run --with redis --with pymongo --with faker -m delivery_system.mongo_cli --help
```

Exemples :

```bash
make mongo                                        # Executer tous les travaux
uv run -m delivery_system.mongo_cli import        # Verifier l'import
uv run -m delivery_system.mongo_cli history       # Historique du livreur d1
uv run -m delivery_system.mongo_cli history --driver d3
uv run -m delivery_system.mongo_cli regions       # Performance par region
uv run -m delivery_system.mongo_cli top           # Top 2 livreurs
uv run -m delivery_system.mongo_cli top --limit 5
uv run -m delivery_system.mongo_cli indexes       # Creer et afficher les index
```

## Structures avancees (Partie 3)

### Livreurs multi-regions

Un livreur peut operer dans plusieurs regions. La structure Redis utilise des Sets :
- `driver:{id}:regions` : regions du livreur
- `region:{name}:drivers` : index inverse (livreurs par region)

```bash
make drivers-by-region                             # Livreurs operant a Paris
$(UV) -m delivery_system.cli drivers-by-region --region Banlieue
```

### Cache avec expiration (TTL 30s)

Deux caches sont maintenus avec une expiration automatique de 30 secondes :
- `cache:top5_drivers` : top 5 livreurs par rating (JSON)
- `cache:pending_orders:{region}` : commandes en attente par region (JSON)

```bash
make cache-refresh    # Construire/rafraichir le cache
make cache-show       # Afficher le cache avec TTL restant
```

## Commandes Make disponibles

```bash
make help
```

| Commande          | Description |
|-------------------|-------------|
| `make up`         | Demarrer Redis + MongoDB (Docker) |
| `make down`       | Arreter les conteneurs |
| `make restart`    | Redemarrer les conteneurs |
| `make logs`       | Voir les logs Docker |
| `make generate`   | Generer et charger les donnees |
| `make assign`     | Affecter `c1` a `d3` atomiquement |
| `make report`     | Afficher commandes en attente vs assignees |
| `make complete`   | Simuler la fin de livraison de `c1` par `d3` |
| `make dashboard`  | Afficher le dashboard global |
| `make demo`       | Executer le scenario complet des travaux Redis |
| `make mongo`      | Executer tous les travaux MongoDB |
| `make drivers-by-region` | Livreurs operant a Paris (multi-regions) |
| `make cache-refresh` | Rafraichir le cache Redis (TTL 30s) |
| `make cache-show` | Afficher le contenu du cache |

## Structure du projet

```text
.
|-- delivery_system/
|   |-- __init__.py
|   |-- cli.py             # CLI Redis (assign, report, complete, dashboard, demo, drivers-by-region, cache-*)
|   |-- service.py         # Operations Redis transactionnelles
|   |-- mongo_cli.py       # CLI MongoDB (import, history, regions, top, indexes)
|   `-- mongo_service.py   # Requetes et agregations MongoDB
|-- docker-compose.yml
|-- Makefile
|-- config.py
|-- generate_data.py
`-- requirements.txt
```
