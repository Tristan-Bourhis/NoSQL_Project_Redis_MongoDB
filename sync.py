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
    """
    Clôture une livraison dans Redis ET la synchronise dans MongoDB.
    C'est le pont entre les deux bases de données.
    """

    r  = get_redis()
    db = get_mongo_db()

    service = DeliveryService(r)
    result  = service.complete_delivery(order_id, driver_id)

    if not result.ok:
        print(f"Erreur Redis : {result.message}")
        return

    print(f"Redis mis à jour : commande {order_id} → livree")

    order_data = r.hgetall(f"order:{order_id}")

    if not order_data:
        print(f"Commande {order_id} introuvable dans Redis")
        return

    driver_data = r.hgetall(f"driver:{driver_id}")

    if not driver_data:
        print(f"Livreur {driver_id} introuvable dans Redis")
        return

    now = datetime.now()

    destination = order_data.get("destination", "")
    region = REGION_MAP.get(destination, driver_data.get("region", ""))

    document = {
        "command_id":       order_id,
        "client":           order_data.get("client", ""),
        "driver_id":        driver_id,
        "driver_name":      driver_data.get("name", ""),
        "pickup_time":      now,          # heure de clôture
        "delivery_time":    now,
        "duration_minutes": 0,            # non disponible dans Redis
        "amount":           int(order_data.get("amount", 0)),
        "region":           region,       # depuis la destination
        "rating":           float(driver_data.get("rating", 0)),
        "review":           "",           # rempli par le client après
        "status":           "completed",
    }

    collection = db["deliveries"]
    insert_result = collection.insert_one(document)

    print(f"MongoDB mis à jour : document inséré (_id={insert_result.inserted_id})")
    print(f"   Commande : {order_id} | Livreur : {driver_data.get('name')} | Montant : {document['amount']}€ | Région : {region}")


if __name__ == "__main__":

    print("=" * 55)
    print("   Synchronisation Redis → MongoDB")
    print("=" * 55)

    r  = get_redis()
    db = get_mongo_db()

    en_attente = r.smembers("orders:en_attente")
    print(f"\nCommandes en attente : {sorted(en_attente)}")

    print("\n[1] Assignation de c1 à d3...")
    service = DeliveryService(r)
    res = service.assign_order("c1", "d3")
    print(f"    → {res.message}")

    print("\n[2] Clôture et synchronisation c1 → MongoDB...")
    sync_to_mongo("c1", "d3")

    print("\n[3] Vérification dans MongoDB...")
    doc = db["deliveries"].find_one(
        {"command_id": "c1", "driver_id": "d3", "status": "completed"},
        sort=[("delivery_time", -1)]   
    )
    if doc:
        print(f"    Document trouvé dans MongoDB :")
        print(f"       command_id : {doc['command_id']}")
        print(f"       client     : {doc['client']}")
        print(f"       driver     : {doc['driver_name']}")
        print(f"       montant    : {doc['amount']}€")
        print(f"       région     : {doc['region']}")
        print(f"       statut     : {doc['status']}")
    else:
        print("    Document non trouvé")

    print("\n" + "=" * 55)