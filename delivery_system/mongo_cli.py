from __future__ import annotations

import argparse

from config import get_mongo_db

from .mongo_service import MongoAnalytics


def _build_analytics() -> MongoAnalytics:
    return MongoAnalytics(get_mongo_db())


def _separator(title: str) -> None:
    w = 60
    print(f"\n{'=' * w}")
    print(f" {title} ".center(w))
    print(f"{'=' * w}")


def cmd_import(_: argparse.Namespace) -> None:
    a = _build_analytics()
    _separator("Import de l'historique")
    print(f"Total : {a.count_deliveries()} livraisons")
    print("\nBase :")
    for d in a.base_deliveries():
        print(f"  {d['command_id']} | {d['client']} | {d['driver_id']} | "
              f"{d['duration_minutes']}min | {d['amount']}E | {d['rating']} | {d['review']}")


def cmd_history(args: argparse.Namespace) -> None:
    a = _build_analytics()
    _separator(f"Historique du livreur {args.driver}")
    deliveries = a.driver_history(args.driver)
    print(f"{len(deliveries)} livraisons\n")
    for d in deliveries:
        print(f"  {d['command_id']} | {d['client']} | {d['duration_minutes']}min | "
              f"{d['amount']}E | {d['rating']}")
    stats = a.driver_stats(args.driver)
    if stats:
        print(f"\nTotal : {stats['nb_livraisons']} livraisons, {stats['montant_total']}E")


def cmd_regions(_: argparse.Namespace) -> None:
    a = _build_analytics()
    _separator("Performance par region")
    header = f"  {'Region':<12} {'Nb':>4} {'Revenu':>8} {'Duree':>8} {'Rating':>8}"
    print(header)
    print("  " + "-" * (len(header) - 2))
    for r in a.performance_by_region():
        print(f"  {r['region']:<12} {r['nb_livraisons']:>4} "
              f"{r['revenu_total']:>7}E {r['duree_moy']:>6.1f}m {r['rating_moy']:>7.2f}")


def cmd_top(args: argparse.Namespace) -> None:
    a = _build_analytics()
    _separator(f"Top {args.limit} livreurs")
    for i, r in enumerate(a.top_drivers(args.limit), 1):
        print(f"  #{i} {r['driver_name']} ({r['driver_id']}) : "
              f"{r['nb_livraisons']} livr, {r['revenu_total']}E, "
              f"{r['duree_moy']}min moy, rating {r['rating_moy']}")


def cmd_indexes(_: argparse.Namespace) -> None:
    a = _build_analytics()
    _separator("Indexation strategique")
    for name in a.create_indexes():
        print(f"  index cree : {name}")
    print("\nIndex actuels :")
    for name, info in a.list_indexes().items():
        print(f"  {name} : {info['key']}")

    explain = a.explain_driver_query("d1")
    plan = explain.get("queryPlanner", {}).get("winningPlan", {})
    print(f"\nexplain find(driver_id='d1') : stage={plan.get('stage', '?')}", end="")
    if "inputStage" in plan:
        print(f", index={plan['inputStage'].get('indexName', '-')}")
    else:
        print()

    print("\nidx_driver_id : IXSCAN au lieu de COLLSCAN, O(log n) au lieu de O(n)")
    print("idx_region_delivery_time : filtre region + tri par date sans sort en memoire")


def cmd_all(args: argparse.Namespace) -> None:
    cmd_import(args)
    cmd_history(args)
    cmd_regions(args)
    cmd_top(args)
    cmd_indexes(args)
    print()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="mongo-cli",
        description="Analyses MongoDB pour le systeme de livraison",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("import", help="Verifier l'import").set_defaults(func=cmd_import)

    h = sub.add_parser("history", help="Historique d'un livreur")
    h.add_argument("--driver", default="d1")
    h.set_defaults(func=cmd_history)

    sub.add_parser("regions", help="Performance par region").set_defaults(func=cmd_regions)

    t = sub.add_parser("top", help="Top livreurs par revenu")
    t.add_argument("--limit", type=int, default=2)
    t.set_defaults(func=cmd_top)

    sub.add_parser("indexes", help="Creer et afficher les index").set_defaults(func=cmd_indexes)

    a = sub.add_parser("all", help="Executer tous les travaux")
    a.add_argument("--driver", default="d1")
    a.add_argument("--limit", type=int, default=2)
    a.set_defaults(func=cmd_all)

    return parser


def main() -> None:
    args = build_parser().parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
