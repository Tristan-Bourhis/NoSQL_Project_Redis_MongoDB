import random
from datetime import datetime, timedelta
from faker import Faker

from config import get_redis, get_mongo_db

fake = Faker("fr_FR")


BASE_DRIVERS = [
    {"id": "d1", "name": "Alice Dupont", "region": "Paris", "rating": 4.8},
    {"id": "d2", "name": "Bob Martin", "region": "Paris", "rating": 4.5},
    {"id": "d3", "name": "Charlie Lefevre", "region": "Banlieue", "rating": 4.9},
    {"id": "d4", "name": "Diana Russo", "region": "Banlieue", "rating": 4.3},
]

BASE_ORDERS = [
    {"id": "c1", "client": "Client A", "destination": "Marais", "amount": 25, "created_at": "14:00"},
    {"id": "c2", "client": "Client B", "destination": "Belleville", "amount": 15, "created_at": "14:05"},
    {"id": "c3", "client": "Client C", "destination": "Bercy", "amount": 30, "created_at": "14:10"},
    {"id": "c4", "client": "Client D", "destination": "Auteuil", "amount": 20, "created_at": "14:15"},
]

REGIONS = ["Paris", "Banlieue"]
DESTINATIONS = ["Marais", "Belleville", "Bercy", "Auteuil", "Montmartre",
                "Bastille", "Oberkampf", "Republique", "Nation", "Chatelet"]
REVIEWS = [
    "Excellent service !",
    "Livraison rapide, merci.",
    "Tres bien, livreur sympathique.",
    "Un peu en retard mais correct.",
    "Parfait, rien a redire.",
    "Service impeccable, je recommande.",
    "Bonne livraison dans l'ensemble.",
    "Livreur tres professionnel.",
    "Correct, sans plus.",
    "Super rapide !",
]



def generate_extra_drivers(count=16):
    """Génère des livreurs supplémentaires (d5, d6, ...)."""
    drivers = []
    for i in range(5, 5 + count):
        drivers.append({
            "id": f"d{i}",
            "name": fake.name(),
            "region": random.choice(REGIONS),
            "rating": round(random.uniform(3.5, 5.0), 1),
        })
    return drivers




def generate_extra_orders(count=16):
    """Génère des commandes supplémentaires (c5, c6, ...)."""
    orders = []
    base_hour = 14
    base_minute = 20
    for i in range(5, 5 + count):
        minute = base_minute + (i - 5) * 5
        hour = base_hour + minute // 60
        minute = minute % 60
        orders.append({
            "id": f"c{i}",
            "client": fake.first_name(),
            "destination": random.choice(DESTINATIONS),
            "amount": random.randint(10, 50),
            "created_at": f"{hour}:{minute:02d}",
        })
    return orders




def generate_deliveries(drivers, count=30):
    """Génère des livraisons complétées pour l'historique MongoDB."""
    deliveries = []
    base_date = datetime(2025, 12, 6, 10, 0, 0)

    for i in range(count):
        driver = random.choice(drivers)
        duration = random.randint(10, 40)
        pickup = base_date + timedelta(minutes=random.randint(0, 480))
        delivery_time = pickup + timedelta(minutes=duration)

        deliveries.append({
            "command_id": f"c{i + 100}",
            "client": fake.first_name(),
            "driver_id": driver["id"],
            "driver_name": driver["name"],
            "pickup_time": pickup,
            "delivery_time": delivery_time,
            "duration_minutes": duration,
            "amount": random.randint(10, 50),
            "region": driver["region"],
            "rating": round(random.uniform(3.0, 5.0), 1),
            "review": random.choice(REVIEWS),
            "status": "completed",
        })

    return deliveries




def load_drivers_redis(r, drivers):
    """Charge les livreurs dans Redis (hash + sorted set)."""
    pipe = r.pipeline()
    for d in drivers:
        key = f"driver:{d['id']}"
        pipe.hset(key, mapping={
            "name": d["name"],
            "region": d["region"],
            "rating": str(d["rating"]),
            "deliveries_in_progress": "0",
            "deliveries_completed": "0",
        })
        pipe.zadd("drivers:ratings", {d["id"]: d["rating"]})
    pipe.execute()
    print(f"  -> {len(drivers)} livreurs charges dans Redis")


def load_orders_redis(r, orders):
    """Charge les commandes dans Redis (hash + set par statut)."""
    pipe = r.pipeline()
    for o in orders:
        key = f"order:{o['id']}"
        pipe.hset(key, mapping={
            "client": o["client"],
            "destination": o["destination"],
            "amount": str(o["amount"]),
            "created_at": o["created_at"],
            "status": "en_attente",
        })
        pipe.sadd("orders:en_attente", o["id"])
    pipe.execute()
    print(f"  -> {len(orders)} commandes chargees dans Redis")




def load_deliveries_mongo(db, deliveries):
    """Charge les livraisons historiques dans MongoDB."""
    collection = db["deliveries"]
    collection.drop()
    if deliveries:
        collection.insert_many(deliveries)
    print(f"  -> {len(deliveries)} livraisons chargees dans MongoDB")



def main():
    print("=" * 60)
    print("  Generateur de donnees - Systeme de livraison")
    print("=" * 60)

    all_drivers = BASE_DRIVERS + generate_extra_drivers(16)
    all_orders = BASE_ORDERS + generate_extra_orders(16)

    base_deliveries = [
        {
            "command_id": "c1", "client": "Client A",
            "driver_id": "d3", "driver_name": "Charlie Lefevre",
            "pickup_time": datetime(2025, 12, 6, 14, 5, 0),
            "delivery_time": datetime(2025, 12, 6, 14, 25, 0),
            "duration_minutes": 20, "amount": 25,
            "region": "Paris", "rating": 4.9,
            "review": "Excellent service !", "status": "completed",
        },
        {
            "command_id": "c2", "client": "Client B",
            "driver_id": "d1", "driver_name": "Alice Dupont",
            "pickup_time": datetime(2025, 12, 6, 14, 10, 0),
            "delivery_time": datetime(2025, 12, 6, 14, 25, 0),
            "duration_minutes": 15, "amount": 15,
            "region": "Paris", "rating": 4.8,
            "review": "Livraison rapide, merci.", "status": "completed",
        },
        {
            "command_id": "c3", "client": "Client C",
            "driver_id": "d2", "driver_name": "Bob Martin",
            "pickup_time": datetime(2025, 12, 6, 14, 15, 0),
            "delivery_time": datetime(2025, 12, 6, 14, 40, 0),
            "duration_minutes": 25, "amount": 30,
            "region": "Paris", "rating": 4.5,
            "review": "Correct, sans plus.", "status": "completed",
        },
        {
            "command_id": "c4", "client": "Client D",
            "driver_id": "d1", "driver_name": "Alice Dupont",
            "pickup_time": datetime(2025, 12, 6, 14, 20, 0),
            "delivery_time": datetime(2025, 12, 6, 14, 38, 0),
            "duration_minutes": 18, "amount": 20,
            "region": "Paris", "rating": 4.8,
            "review": "Tres bien, livreur sympathique.", "status": "completed",
        },
    ]
    extra_deliveries = generate_deliveries(all_drivers, count=30)
    all_deliveries = base_deliveries + extra_deliveries

    print("\n[Redis] Chargement des donnees...")
    r = get_redis()
    r.flushdb()     
    load_drivers_redis(r, all_drivers)
    load_orders_redis(r, all_orders)

    print("\n[MongoDB] Chargement des donnees...")
    db = get_mongo_db()
    load_deliveries_mongo(db, all_deliveries)

    print("\n" + "=" * 60)
    print(f"    Livreurs :    {len(all_drivers)} ({len(BASE_DRIVERS)} de base + {len(all_drivers) - len(BASE_DRIVERS)} generes)")
    print(f"    Commandes :   {len(all_orders)} ({len(BASE_ORDERS)} de base + {len(all_orders) - len(BASE_ORDERS)} generees)")
    print(f"    Livraisons :  {len(all_deliveries)} ({len(base_deliveries)} de base + {len(extra_deliveries)} generees)")
    print("=" * 60)


if __name__ == "__main__":
    main()
