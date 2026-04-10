from __future__ import annotations

import argparse

from config import get_mongo_db

from .mongo_service import MongoAnalytics


def _build_analytics() -> MongoAnalytics:
    return MongoAnalytics(get_mongo_db())


def _separator(title: str) -> None:
    width = 60
    print(f"\n{'=' * width}")
    print(f" {title} ".center(width))
    print(f"{'=' * width}")


# ── Commandes ─────────────────────────────────────────────────


def cmd_import(_: argparse.Namespace) -> None:
    analytics = _build_analytics()
    _separator("Import de l'historique")

    total = analytics.count_deliveries()
    print(f"Nombre total de livraisons dans la collection : {total}")

    print("\nLes 4 livraisons de base :")
    for doc in analytics.base_deliveries():
        print(
            f"  {doc['command_id']} | {doc['client']:10s} | "
            f"livreur {doc['driver_id']} ({doc['driver_name']}) | "
            f"{doc['duration_minutes']} min | {doc['amount']}E | "
            f"rating {doc['rating']} | \"{doc['review']}\""
        )


def cmd_history(args: argparse.Namespace) -> None:
    analytics = _build_analytics()
    _separator(f"Historique du livreur {args.driver}")

    deliveries = analytics.driver_history(args.driver)
    print(f"Nombre de livraisons de {args.driver} : {len(deliveries)}\n")
    for doc in deliveries:
        print(
            f"  {doc['command_id']} | {doc['client']:10s} | "
            f"{doc['duration_minutes']} min | {doc['amount']}E | "
            f"rating {doc['rating']}"
        )

    stats = analytics.driver_stats(args.driver)
    if stats:
        print(f"\n  => Nombre total  : {stats['nombre_livraisons']}")
        print(f"  => Montant total : {stats['montant_total']}E")


def cmd_regions(_: argparse.Namespace) -> None:
    analytics = _build_analytics()
    _separator("Performance par region")

    header = (
        f"  {'Region':<12} {'Livraisons':>10} {'Revenu':>10}"
        f" {'Duree moy.':>12} {'Rating moy.':>12}"
    )
    print(header)
    print("  " + "-" * (len(header) - 2))
    for r in analytics.performance_by_region():
        print(
            f"  {r['region']:<12} {r['nombre_livraisons']:>10} "
            f"{r['revenu_total']:>9}E {r['duree_moyenne']:>10.1f} min"
            f" {r['rating_moyen']:>11.2f}"
        )


def cmd_top(args: argparse.Namespace) -> None:
    analytics = _build_analytics()
    _separator(f"Top {args.limit} livreurs")

    for i, r in enumerate(analytics.top_drivers(args.limit), 1):
        print(f"\n  #{i} {r['driver_name']} ({r['driver_id']})")
        print(f"      Livraisons : {r['nombre_livraisons']}")
        print(f"      Revenu     : {r['revenu_total']}E")
        print(f"      Duree moy. : {r['duree_moyenne']} min")
        print(f"      Rating moy.: {r['rating_moyen']}")


def cmd_indexes(_: argparse.Namespace) -> None:
    analytics = _build_analytics()
    _separator("Indexation strategique")

    created = analytics.create_indexes()
    for name in created:
        print(f"Index cree : {name}")

    print("\nIndex actuels de la collection 'deliveries' :")
    for name, info in analytics.list_indexes().items():
        print(f"  - {name} : {info['key']}")

    print("\n--- Verification avec explain() ---")
    explain = analytics.explain_driver_query("d1")
    plan = explain.get("queryPlanner", {}).get("winningPlan", {})
    print("  Requete : find({driver_id: 'd1'})")
    print(f"  Plan gagnant : {plan.get('stage', '?')}")
    if "inputStage" in plan:
        print(f"  Index utilise : {plan['inputStage'].get('indexName', 'aucun')}")

    print(
        "\n--- Pourquoi ces index ameliorent les performances ---\n"
        "  1) idx_driver_id :\n"
        "     Sans index, MongoDB effectue un COLLSCAN (parcours complet\n"
        "     de la collection). Avec l'index, il fait un IXSCAN cible :\n"
        "     seuls les documents du livreur demande sont lus.\n"
        "     Complexite : O(log n) au lieu de O(n).\n"
        "\n"
        "  2) idx_region_delivery_time :\n"
        "     Cet index compose couvre les requetes filtrant par region\n"
        "     puis triant ou filtrant par date. MongoDB parcourt l'index\n"
        "     de maniere ordonnee sans tri supplementaire en memoire.\n"
        "     Utile pour : analyses regionales sur une periode donnee."
    )


def cmd_all(args: argparse.Namespace) -> None:
    cmd_import(args)
    cmd_history(args)
    cmd_regions(args)
    cmd_top(args)
    cmd_indexes(args)
    print()


# ── Parser ────────────────────────────────────────────────────


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="mongo-cli",
        description="Analyses MongoDB pour le systeme de livraison",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    import_parser = subparsers.add_parser("import", help="Verifier l'import de l'historique")
    import_parser.set_defaults(func=cmd_import)

    history_parser = subparsers.add_parser("history", help="Historique d'un livreur")
    history_parser.add_argument("--driver", default="d1", help="ID livreur (defaut: d1)")
    history_parser.set_defaults(func=cmd_history)

    regions_parser = subparsers.add_parser("regions", help="Performance par region")
    regions_parser.set_defaults(func=cmd_regions)

    top_parser = subparsers.add_parser("top", help="Top livreurs par revenu")
    top_parser.add_argument("--limit", type=int, default=2, help="Nombre de livreurs (defaut: 2)")
    top_parser.set_defaults(func=cmd_top)

    indexes_parser = subparsers.add_parser("indexes", help="Creer et afficher les index")
    indexes_parser.set_defaults(func=cmd_indexes)

    all_parser = subparsers.add_parser("all", help="Executer tous les travaux")
    all_parser.add_argument("--driver", default="d1", help="ID livreur (defaut: d1)")
    all_parser.add_argument("--limit", type=int, default=2, help="Nombre de top livreurs (defaut: 2)")
    all_parser.set_defaults(func=cmd_all)

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
