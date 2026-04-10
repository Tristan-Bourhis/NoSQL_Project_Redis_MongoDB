from datetime import datetime
from config import get_redis, get_mongo_db
from delivery_system.service import DeliveryService


REGION_MAP = {
    "Marais":     "Paris",
    "Belleville": "Paris",
    "Bercy":      "Paris",
    "Auteuil":    "Paris",
    "Montmartre": "Paris",
    "Bastille":   "Paris",
    "Oberkampf":  "Paris",
    "Republique": "Paris",
    "Nation":     "Paris",
    "Chatelet":   "Paris",
}


def sync_to_mongo(order_id: str, driver_id: str):
    r = get_redis()
    db = get_mongo_db()

    svc = DeliveryService(r)
    res = svc.complete_delivery(order_id, driver_id)

    if not res.ok:
        print(f"Erreur Redis : {res.message}")
        return

    print(f"Redis : {order_id} -> livree")

    order = r.hgetall(f"order:{order_id}")
    if not order:
        print(f"Commande {order_id} introuvable")
        return

    driver = r.hgetall(f"driver:{driver_id}")
    if not driver:
        print(f"Livreur {driver_id} introuvable")
        return

    now = datetime.now()
    destination = order.get("destination", "")
    region = REGION_MAP.get(destination, driver.get("region", ""))

    document = {
        "command_id":       order_id,
        "client":           order.get("client", ""),
        "driver_id":        driver_id,
        "driver_name":      driver.get("name", ""),
        "pickup_time":      now,
        "delivery_time":    now,
        "duration_minutes": 0,
        "amount":           int(order.get("amount", 0)),
        "region":           region,
        "rating":           float(driver.get("rating", 0)),
        "review":           "",
        "status":           "completed",
    }

    col = db["deliveries"]
    insert_res = col.insert_one(document)
    print(f"MongoDB : insere _id={insert_res.inserted_id}")
    print(f"  {order_id} | {driver.get('name')} | {document['amount']}E | {region}")


if __name__ == "__main__":
    r = get_redis()
    db = get_mongo_db()

    pending = r.smembers("orders:en_attente")
    print(f"En attente : {sorted(pending)}")

    print("\n1. Assignation c1 -> d3")
    svc = DeliveryService(r)
    res = svc.assign_order("c1", "d3")
    print(f"   {res.message}")

    print("\n2. Cloture + sync c1 -> MongoDB")
    sync_to_mongo("c1", "d3")

    print("\n3. Verification MongoDB")
    doc = db["deliveries"].find_one(
        {"command_id": "c1", "driver_id": "d3", "status": "completed"},
        sort=[("delivery_time", -1)]
    )
    if doc:
        print(f"   {doc['command_id']} | {doc['client']} | {doc['driver_name']} | "
              f"{doc['amount']}E | {doc['region']} | {doc['status']}")
    else:
        print("   Non trouve")
