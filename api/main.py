from __future__ import annotations

from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from config import get_redis, get_mongo_db
from delivery_system.service import DeliveryService
from delivery_system.mongo_service import MongoAnalytics
from geo import (
    init_geo_data, find_nearby_drivers, find_best_driver, monitor_driver,
    DELIVERY_POINTS, DRIVER_POSITIONS,
)

app = FastAPI(title="Delivery System API")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


def _svc() -> DeliveryService:
    return DeliveryService(get_redis())


def _analytics() -> MongoAnalytics:
    return MongoAnalytics(get_mongo_db())


class AssignBody(BaseModel):
    driver_id: str


class MonitorBody(BaseModel):
    driver_id: str
    lon: float
    lat: float


@app.get("/api/orders")
def list_orders(status: str = Query("en_attente")):
    svc = _svc()
    ids = svc.list_orders(status)
    orders = []
    for oid in ids:
        snap = svc.order_snapshot(oid)
        snap["id"] = oid
        orders.append(snap)
    return orders


@app.get("/api/orders/counts")
def order_counts():
    return _svc().count_orders_by_status()


@app.get("/api/orders/{order_id}")
def get_order(order_id: str):
    snap = _svc().order_snapshot(order_id)
    snap["id"] = order_id
    return snap


@app.post("/api/orders/{order_id}/assign")
def assign_order(order_id: str, body: AssignBody):
    res = _svc().assign_order(order_id, body.driver_id)
    return {"ok": res.ok, "message": res.message}


@app.post("/api/orders/{order_id}/complete")
def complete_order(order_id: str, body: AssignBody):
    r = get_redis()
    db = get_mongo_db()
    svc = DeliveryService(r)
    res = svc.complete_delivery(order_id, body.driver_id)
    if res.ok:
        from sync import sync_delivery_to_mongo
        sync_delivery_to_mongo(r, db, order_id, body.driver_id)
    return {"ok": res.ok, "message": res.message}


@app.get("/api/drivers")
def list_drivers():
    svc = _svc()
    r = svc.redis
    ids = r.zrange("drivers:ratings", 0, -1, withscores=True)
    drivers = []
    for did, rating in ids:
        snap = r.hgetall(f"driver:{did}")
        snap["id"] = did
        snap["rating"] = rating
        snap["regions"] = sorted(r.smembers(f"driver:{did}:regions"))
        drivers.append(snap)
    return drivers


@app.get("/api/drivers/top")
def top_drivers(limit: int = Query(5)):
    return _svc().top_rated_drivers(limit)


@app.get("/api/drivers/by-region")
def drivers_by_region(region: str = Query("Paris")):
    return _svc().get_drivers_by_region(region)


@app.get("/api/drivers/{driver_id}")
def get_driver(driver_id: str):
    svc = _svc()
    snap = svc.driver_snapshot(driver_id)
    snap["id"] = driver_id
    snap["regions_list"] = svc.get_driver_regions(driver_id)
    return snap


@app.get("/api/drivers/{driver_id}/history")
def driver_history(driver_id: str):
    a = _analytics()
    history = a.driver_history(driver_id)
    for doc in history:
        doc["_id"] = str(doc["_id"])
    stats = a.driver_stats(driver_id)
    return {"deliveries": history, "stats": stats}


@app.post("/api/geo/init")
def geo_init():
    r = get_redis()
    init_geo_data(r)
    return {"ok": True}


@app.get("/api/geo/points")
def geo_points():
    return {
        "delivery_points": [{"name": n, "lon": lo, "lat": la} for n, lo, la in DELIVERY_POINTS],
        "driver_positions": [{"name": n, "lon": lo, "lat": la} for n, lo, la in DRIVER_POSITIONS],
    }


@app.get("/api/geo/nearby")
def geo_nearby(lieu: str = Query("Marais"), radius: float = Query(2)):
    r = get_redis()
    coords = r.geopos("delivery_points", lieu)
    if not coords or not coords[0]:
        return []
    lon, lat = coords[0]
    results = r.geosearch(
        "drivers_locations",
        longitude=lon, latitude=lat,
        radius=radius, unit="km",
        sort="ASC", withcoord=True, withdist=True,
    )
    out = []
    for member, dist, coord in results:
        rating = float(r.hget(f"driver:{member}", "rating") or 0)
        name = r.hget(f"driver:{member}", "name") or member
        out.append({
            "id": member, "name": name, "dist_km": float(dist),
            "lon": coord[0], "lat": coord[1], "rating": rating,
        })
    return out


@app.get("/api/geo/best")
def geo_best(lieu: str = Query("Marais"), radius: float = Query(3)):
    r = get_redis()
    result = find_best_driver(r, lieu, radius)
    return result


@app.post("/api/geo/monitor")
def geo_monitor(body: MonitorBody):
    r = get_redis()
    dist = monitor_driver(r, body.driver_id, body.lon, body.lat)
    alert = dist is not None and float(dist) > 5
    return {"driver_id": body.driver_id, "dist_km": float(dist or 0), "alert": alert}


@app.get("/api/analytics/regions")
def analytics_regions():
    return _analytics().performance_by_region()


@app.get("/api/analytics/top-drivers")
def analytics_top_drivers(limit: int = Query(2)):
    return _analytics().top_drivers(limit)


@app.get("/api/analytics/deliveries/count")
def analytics_count():
    return {"count": _analytics().count_deliveries()}


@app.post("/api/cache/refresh")
def cache_refresh():
    return _svc().refresh_cache()


@app.get("/api/cache")
def cache_show():
    svc = _svc()
    return {
        "top5": svc.get_cached_top5_drivers(),
        "ttl": svc.get_cache_ttl(),
        "pending_paris": svc.get_cached_pending_orders("Paris"),
        "pending_banlieue": svc.get_cached_pending_orders("Banlieue"),
    }


@app.get("/api/dashboard")
def dashboard():
    svc = _svc()
    return {
        "counts": svc.count_orders_by_status(),
        "top2": svc.top_rated_drivers(2),
        "in_progress": svc.deliveries_in_progress_per_driver(),
    }
