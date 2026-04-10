from __future__ import annotations

from typing import Any

from pymongo.database import Database


class MongoAnalytics:
    COLLECTION = "deliveries"

    def __init__(self, db: Database) -> None:
        self.db = db
        self.col = db[self.COLLECTION]

    # ── Travail 1 : verification de l'import ─────────────────

    def count_deliveries(self) -> int:
        return self.col.count_documents({})

    def base_deliveries(self) -> list[dict[str, Any]]:
        return list(self.col.find({"command_id": {"$in": ["c1", "c2", "c3", "c4"]}}))

    # ── Travail 2 : historique d'un livreur ───────────────────

    def driver_history(self, driver_id: str) -> list[dict[str, Any]]:
        return list(self.col.find({"driver_id": driver_id}))

    def driver_stats(self, driver_id: str) -> dict[str, Any] | None:
        pipeline = [
            {"$match": {"driver_id": driver_id}},
            {"$group": {
                "_id": None,
                "nombre_livraisons": {"$sum": 1},
                "montant_total": {"$sum": "$amount"},
            }},
        ]
        results = list(self.col.aggregate(pipeline))
        return results[0] if results else None

    # ── Travail 3 : performance par region ────────────────────

    def performance_by_region(self) -> list[dict[str, Any]]:
        pipeline = [
            {"$group": {
                "_id": "$region",
                "nombre_livraisons": {"$sum": 1},
                "revenu_total": {"$sum": "$amount"},
                "duree_moyenne": {"$avg": "$duration_minutes"},
                "rating_moyen": {"$avg": "$rating"},
            }},
            {"$sort": {"revenu_total": -1}},
            {"$project": {
                "_id": 0,
                "region": "$_id",
                "nombre_livraisons": 1,
                "revenu_total": 1,
                "duree_moyenne": {"$round": ["$duree_moyenne", 1]},
                "rating_moyen": {"$round": ["$rating_moyen", 2]},
            }},
        ]
        return list(self.col.aggregate(pipeline))

    # ── Travail 4 : top livreurs ──────────────────────────────

    def top_drivers(self, limit: int = 2) -> list[dict[str, Any]]:
        pipeline = [
            {"$group": {
                "_id": {"driver_id": "$driver_id", "driver_name": "$driver_name"},
                "nombre_livraisons": {"$sum": 1},
                "revenu_total": {"$sum": "$amount"},
                "duree_moyenne": {"$avg": "$duration_minutes"},
                "rating_moyen": {"$avg": "$rating"},
            }},
            {"$sort": {"revenu_total": -1}},
            {"$limit": limit},
            {"$project": {
                "_id": 0,
                "driver_id": "$_id.driver_id",
                "driver_name": "$_id.driver_name",
                "nombre_livraisons": 1,
                "revenu_total": 1,
                "duree_moyenne": {"$round": ["$duree_moyenne", 1]},
                "rating_moyen": {"$round": ["$rating_moyen", 2]},
            }},
        ]
        return list(self.col.aggregate(pipeline))

    # ── Travail 5 : indexation strategique ────────────────────

    def create_indexes(self) -> list[str]:
        idx1 = self.col.create_index("driver_id", name="idx_driver_id")
        idx2 = self.col.create_index(
            [("region", 1), ("delivery_time", 1)],
            name="idx_region_delivery_time",
        )
        return [idx1, idx2]

    def list_indexes(self) -> dict[str, Any]:
        return self.col.index_information()

    def explain_driver_query(self, driver_id: str) -> dict[str, Any]:
        return self.col.find({"driver_id": driver_id}).explain()
