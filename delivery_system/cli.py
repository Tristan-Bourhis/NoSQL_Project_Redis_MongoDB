from __future__ import annotations

import argparse

from config import get_redis

from .service import DeliveryService


def _build_service() -> DeliveryService:
    return DeliveryService(get_redis())


def _check_required_data(service: DeliveryService, order_id: str, driver_id: str) -> bool:
    redis_client = service.redis
    if not redis_client.exists(f"order:{order_id}") or not redis_client.exists(f"driver:{driver_id}"):
        print("Donnees Redis manquantes. Lancez d'abord : python generate_data.py")
        return False
    return True


def cmd_assign(args: argparse.Namespace) -> None:
    service = _build_service()
    result = service.assign_order(args.order, args.driver)
    print(f"Affectation {args.order} -> {args.driver} : ok={result.ok}, message={result.message}")
    if result.ok:
        print(f"order:{args.order} -> {service.order_snapshot(args.order)}")
        print(f"driver:{args.driver} -> {service.driver_snapshot(args.driver)}")


def cmd_report(_: argparse.Namespace) -> None:
    service = _build_service()
    pending = service.list_orders("en_attente")
    assigned = service.list_orders("assignee")
    best = service.best_rated_driver()

    print("=== Commandes affectees vs en attente ===")
    print(f"Commandes en attente : {len(pending)} -> {pending}")
    print(f"Commandes assignees : {len(assigned)} -> {assigned}")
    if best is None:
        print("Livreur avec rating maximal : N/A")
    else:
        print(
            "Livreur avec rating maximal : "
            f"{best['id']} ({best['name']}) - rating {best['rating']}"
        )


def cmd_complete(args: argparse.Namespace) -> None:
    service = _build_service()
    result = service.complete_delivery(args.order, args.driver)
    print(f"Fin de livraison {args.order} par {args.driver} : ok={result.ok}, message={result.message}")
    if result.ok:
        print(f"order:{args.order} -> {service.order_snapshot(args.order)}")
        print(f"driver:{args.driver} -> {service.driver_snapshot(args.driver)}")


def cmd_dashboard(_: argparse.Namespace) -> None:
    service = _build_service()
    counts = service.count_orders_by_status()
    in_progress = service.deliveries_in_progress_per_driver()
    top_two = service.top_rated_drivers(limit=2)

    print("=== Dashboard temps reel ===")
    print(
        "Commandes par statut : "
        f"en_attente={counts['en_attente']}, assignee={counts['assignee']}, livree={counts['livree']}"
    )

    print("Livraisons en cours par livreur :")
    if not in_progress:
        print("  Aucun livreur trouve.")
    else:
        for row in in_progress:
            print(f"  {row['id']} ({row['name']}) -> {row['in_progress']}")

    print("Top 2 livreurs :")
    if not top_two:
        print("  Aucun livreur trouve.")
    else:
        for rank, driver in enumerate(top_two, start=1):
            print(f"  #{rank} {driver['id']} ({driver['name']}) - rating {driver['rating']}")


def cmd_demo(args: argparse.Namespace) -> None:
    service = _build_service()

    if not _check_required_data(service, args.order, args.driver):
        return

    status = service.redis.hget(f"order:{args.order}", "status")
    assigned_driver = service.redis.hget(f"order:{args.order}", "driver_id")

    if status == "en_attente":
        assign_result = service.assign_order(args.order, args.driver)
        print(
            "Pre-affectation : "
            f"ok={assign_result.ok}, message={assign_result.message}"
        )
    elif status == "assignee" and assigned_driver == args.driver:
        print("Pre-affectation : deja en place.")
    else:
        print(
            "Pre-affectation : etat inattendu "
            f"(status={status}, driver_id={assigned_driver})"
        )

    cmd_report(args)

    complete_result = service.complete_delivery(args.order, args.driver)
    print(
        f"\nSimulation livraison {args.order}/{args.driver} : "
        f"ok={complete_result.ok}, message={complete_result.message}"
    )
    print(f"order:{args.order} -> {service.order_snapshot(args.order)}")
    print(f"driver:{args.driver} -> {service.driver_snapshot(args.driver)}")

    print()
    cmd_dashboard(args)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="delivery-cli",
        description="Operations Redis pour le systeme de livraison",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    assign_parser = subparsers.add_parser("assign", help="Affecter une commande a un livreur")
    assign_parser.add_argument("--order", default="c1", help="ID commande (defaut: c1)")
    assign_parser.add_argument("--driver", default="d3", help="ID livreur (defaut: d3)")
    assign_parser.set_defaults(func=cmd_assign)

    report_parser = subparsers.add_parser("report", help="Lister commandes en attente et assignees")
    report_parser.set_defaults(func=cmd_report)

    complete_parser = subparsers.add_parser("complete", help="Terminer une livraison")
    complete_parser.add_argument("--order", default="c1", help="ID commande (defaut: c1)")
    complete_parser.add_argument("--driver", default="d3", help="ID livreur (defaut: d3)")
    complete_parser.set_defaults(func=cmd_complete)

    dashboard_parser = subparsers.add_parser("dashboard", help="Afficher l'etat global du systeme")
    dashboard_parser.set_defaults(func=cmd_dashboard)

    demo_parser = subparsers.add_parser("demo", help="Executer le scenario complet des travaux 4-6")
    demo_parser.add_argument("--order", default="c1", help="ID commande (defaut: c1)")
    demo_parser.add_argument("--driver", default="d3", help="ID livreur (defaut: d3)")
    demo_parser.set_defaults(func=cmd_demo)

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
