import random
from datetime import datetime, timedelta
from faker import Faker

from config import get_redis, get_mongo_db

fake = Faker("fr_FR")

BASE_DRIVERS = [
    {"id": "d1", "name": "Alice Dupont", "regions": ["Paris", "Banlieue"], "rating": 4.8},
    {"id": "d2", "name": "Bob Martin", "regions": ["Paris"], "rating": 4.5},
    {"id": "d3", "name": "Charlie Lefevre", "regions": ["Banlieue"], "rating": 4.9},
    {"id": "d4", "name": "Diana Russo", "regions": ["Banlieue", "Paris"], "rating": 4.3},
]

BASE_ORDERS = [
    {"id": "c1", "client": "Client A", "destination": "Marais", "region": "Paris", "amount": 25, "created_at": "14:00"},
    {"id": "c2", "client": "Client B", "destination": "Belleville", "region": "Paris", "amount": 15, "created_at": "14:05"},
    {"id": "c3", "client": "Client C", "destination": "Bercy", "region": "Paris", "amount": 30, "created_at": "14:10"},
    {"id": "c4", "client": "Client D", "destination": "Auteuil", "region": "Paris", "amount": 20, "created_at": "14:15"},
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
    drivers = []
    for i in range(5, 5 + count):
        num_regions = random.randint(1, len(REGIONS))
        drivers.append({
            "id": f"d{i}",
            "name": fake.name(),
            "regions": random.sample(REGIONS, num_regions),
            "rating": round(random.uniform(3.5, 5.0), 1),
        })
    return drivers


def generate_extra_orders(count=16):
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
            "region": random.choice(REGIONS),
            "amount": random.randint(10, 50),
            "created_at": f"{hour}:{minute:02d}",
        })
    return orders


def generate_deliveries(drivers, count=30):
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
            "region": random.choice(driver["regions"]),
            "rating": round(random.uniform(3.0, 5.0), 1),
            "review": random.choice(REVIEWS),
            "status": "completed",
        })
    return deliveries


def load_drivers_redis(r, drivers):
    pipe = r.pipeline()
    for d in drivers:
        key = f"driver:{d['id']}"
        pipe.hset(key, mapping={
            "name": d["name"],
            "region": d["regions"][0],
            "rating": str(d["rating"]),
            "deliveries_in_progress": "0",
            "deliveries_completed": "0",
        })
        pipe.zadd("drivers:ratings", {d["id"]: d["rating"]})
        for region in d["regions"]:
            pipe.sadd(f"driver:{d['id']}:regions", region)
            pipe.sadd(f"region:{region}:drivers", d["id"])
    pipe.execute()
    print(f"  {len(drivers)} livreurs charges")


def load_orders_redis(r, orders):
    pipe = r.pipeline()
    for o in orders:
        key = f"order:{o['id']}"
        pipe.hset(key, mapping={
            "client": o["client"],
            "destination": o["destination"],
            "region": o["region"],
            "amount": str(o["amount"]),
            "created_at": o["created_at"],
            "status": "en_attente",
        })
        pipe.sadd("orders:en_attente", o["id"])
        pipe.sadd(f"orders:en_attente:{o['region']}", o["id"])
    pipe.execute()
    print(f"  {len(orders)} commandes chargees")


def load_deliveries_mongo(db, deliveries):
    col = db["deliveries"]
    col.drop()
    if deliveries:
        col.insert_many(deliveries)
    print(f"  {len(deliveries)} livraisons chargees")


def main():
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

    print("[Redis]")
    r = get_redis()
    r.flushdb()
    load_drivers_redis(r, all_drivers)
    load_orders_redis(r, all_orders)

    print("[MongoDB]")
    db = get_mongo_db()
    load_deliveries_mongo(db, all_deliveries)

    nb_base_d = len(BASE_DRIVERS)
    nb_base_o = len(BASE_ORDERS)
    nb_base_l = len(base_deliveries)
    print(f"Livreurs : {len(all_drivers)} ({nb_base_d} base + {len(all_drivers) - nb_base_d} gen)")
    print(f"Commandes : {len(all_orders)} ({nb_base_o} base + {len(all_orders) - nb_base_o} gen)")
    print(f"Livraisons : {len(all_deliveries)} ({nb_base_l} base + {len(extra_deliveries)} gen)")


if __name__ == "__main__":
    main()
