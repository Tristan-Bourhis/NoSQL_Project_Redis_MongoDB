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
- Genere 20 livreurs (4 de base + 16 generes)
- Genere 20 commandes (4 de base + 16 generees)
- Genere 34 livraisons historiques (4 de base + 30 generees)
- Charge tout dans Redis et MongoDB

### Arret des services

```bash
make down
```

Pour supprimer aussi les volumes de donnees :

```bash
docker compose down -v
```

## Commandes disponibles

```bash
make help
```

| Commande       | Description                          |
|----------------|--------------------------------------|
| `make up`      | Demarrer Redis + MongoDB (Docker)    |
| `make down`    | Arreter les conteneurs               |
| `make restart` | Redemarrer les conteneurs            |
| `make logs`    | Voir les logs Docker                 |
| `make generate`| Generer et charger les donnees       |

## Structure du projet

```
.
├── docker-compose.yml       # Redis (6380) + MongoDB (27018) via Docker
├── Makefile                 # Commandes via uv
├── config.py                # Connexions centralisees
├── generate_data.py         # Generateur de donnees
└── requirements.txt         # Dependances Python
```
