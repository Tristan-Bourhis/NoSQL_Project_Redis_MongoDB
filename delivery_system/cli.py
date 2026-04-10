from __future__ import annotations

import argparse

from config import get_redis

from .service import DeliveryService


def _build_service() -> DeliveryService:
    return DeliveryService(get_redis())


def _check_required_data(svc: DeliveryService, order_id: str, driver_id: str) -> bool:
    r = svc.redis
    if not r.exists(f"order:{order_id}") or not r.exists(f"driver:{driver_id}"):
        print("Donnees manquantes. Lancez : make generate")
        return False
    return True


def cmd_assign(args: argparse.Namespace) -> None:
    svc = _build_service()
    res = svc.assign_order(args.order, args.driver)
    print(f"assign {args.order} -> {args.driver} : {res.message}")
    if res.ok:
        print(f"  order  : {svc.order_snapshot(args.order)}")
        print(f"  driver : {svc.driver_snapshot(args.driver)}")


def cmd_report(_: argparse.Namespace) -> None:
    svc = _build_service()
    pending = svc.list_orders("en_attente")
    assigned = svc.list_orders("assignee")
    best = svc.best_rated_driver()

    print(f"En attente : {len(pending)} -> {pending}")
    print(f"Assignees  : {len(assigned)} -> {assigned}")
    if best:
        print(f"Meilleur rating : {best['id']} ({best['name']}) {best['rating']}")
    else:
        print("Meilleur rating : N/A")


def cmd_complete(args: argparse.Namespace) -> None:
    svc = _build_service()
    res = svc.complete_delivery(args.order, args.driver)
    print(f"complete {args.order} par {args.driver} : {res.message}")
    if res.ok:
        print(f"  order  : {svc.order_snapshot(args.order)}")
        print(f"  driver : {svc.driver_snapshot(args.driver)}")


def cmd_dashboard(_: argparse.Namespace) -> None:
    svc = _build_service()
    counts = svc.count_orders_by_status()
    in_progress = svc.deliveries_in_progress_per_driver()
    top = svc.top_rated_drivers(limit=2)

    print(f"Statuts : en_attente={counts['en_attente']}, "
          f"assignee={counts['assignee']}, livree={counts['livree']}")

    print("En cours par livreur :")
    for row in in_progress:
        print(f"  {row['id']} ({row['name']}) -> {row['in_progress']}")

    print("Top 2 :")
    for i, d in enumerate(top, 1):
        print(f"  #{i} {d['id']} ({d['name']}) rating {d['rating']}")


def cmd_demo(args: argparse.Namespace) -> None:
    svc = _build_service()
    if not _check_required_data(svc, args.order, args.driver):
        return

    status = svc.redis.hget(f"order:{args.order}", "status")
    assigned = svc.redis.hget(f"order:{args.order}", "driver_id")

    if status == "en_attente":
        res = svc.assign_order(args.order, args.driver)
        print(f"Pre-affectation : {res.message}")
    elif status == "assignee" and assigned == args.driver:
        print("Pre-affectation : deja en place")
    else:
        print(f"Pre-affectation : etat inattendu (status={status}, driver={assigned})")

    cmd_report(args)

    res = svc.complete_delivery(args.order, args.driver)
    print(f"\nComplete {args.order}/{args.driver} : {res.message}")
    print(f"  order  : {svc.order_snapshot(args.order)}")
    print(f"  driver : {svc.driver_snapshot(args.driver)}")
    print()
    cmd_dashboard(args)


def cmd_drivers_by_region(args: argparse.Namespace) -> None:
    svc = _build_service()
    drivers = svc.get_drivers_by_region(args.region)
    print(f"Livreurs dans {args.region} : {len(drivers)}")
    for d in drivers:
        regions = svc.get_driver_regions(d["id"])
        print(f"  {d['id']} ({d['name']}) rating {d['rating']} - {', '.join(regions)}")


def cmd_cache_refresh(_: argparse.Namespace) -> None:
    svc = _build_service()
    data = svc.refresh_cache()
    print("Cache rafraichi (TTL=30s)")
    print("Top 5 :")
    for i, d in enumerate(data["top5_drivers"], 1):
        print(f"  #{i} {d['id']} ({d['name']}) rating {d['rating']}")
    for region, orders in data["pending_by_region"].items():
        print(f"En attente {region} : {len(orders)} -> {orders}")


def cmd_cache_show(_: argparse.Namespace) -> None:
    svc = _build_service()
    top5 = svc.get_cached_top5_drivers()
    ttls = svc.get_cache_ttl()

    ttl = ttls.get("cache:top5_drivers", -2)
    if top5 is None:
        print("Top 5 : expire")
    else:
        print(f"Top 5 (TTL={ttl}s) :")
        for i, d in enumerate(top5, 1):
            print(f"  #{i} {d['id']} ({d['name']}) rating {d['rating']}")

    for region in svc.REGIONS:
        orders = svc.get_cached_pending_orders(region)
        key = f"cache:pending_orders:{region}"
        ttl = ttls.get(key, -2)
        if orders is None:
            print(f"En attente {region} : expire")
        else:
            print(f"En attente {region} (TTL={ttl}s) : {len(orders)} -> {orders}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="delivery-cli",
        description="Operations Redis pour le systeme de livraison",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("assign", help="Affecter une commande a un livreur")
    p.add_argument("--order", default="c1")
    p.add_argument("--driver", default="d3")
    p.set_defaults(func=cmd_assign)

    sub.add_parser("report", help="Commandes en attente et assignees").set_defaults(func=cmd_report)

    p = sub.add_parser("complete", help="Terminer une livraison")
    p.add_argument("--order", default="c1")
    p.add_argument("--driver", default="d3")
    p.set_defaults(func=cmd_complete)

    sub.add_parser("dashboard", help="Etat global du systeme").set_defaults(func=cmd_dashboard)

    p = sub.add_parser("demo", help="Scenario complet")
    p.add_argument("--order", default="c1")
    p.add_argument("--driver", default="d3")
    p.set_defaults(func=cmd_demo)

    p = sub.add_parser("drivers-by-region", help="Livreurs par region")
    p.add_argument("--region", default="Paris")
    p.set_defaults(func=cmd_drivers_by_region)

    sub.add_parser("cache-refresh", help="Rafraichir le cache (TTL 30s)").set_defaults(func=cmd_cache_refresh)
    sub.add_parser("cache-show", help="Afficher le cache").set_defaults(func=cmd_cache_show)

    return parser


def main() -> None:
    args = build_parser().parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
