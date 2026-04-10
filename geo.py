from config import get_redis

DELIVERY_POINTS = [
    ("Marais",    2.364, 48.861),
    ("Belleville", 2.379, 48.870),
    ("Bercy",     2.381, 48.840),
    ("Auteuil",   2.254, 48.851),
]

DRIVER_POSITIONS = [
    ("d1", 2.365, 48.862),
    ("d2", 2.378, 48.871),
    ("d3", 2.320, 48.920),
    ("d4", 2.400, 48.750),
]

PARIS_CENTER = (2.3522, 48.8566)


def init_geo_data(r):
    r.delete("delivery_points", "drivers_locations")
    for name, lon, lat in DELIVERY_POINTS:
        r.geoadd("delivery_points", (lon, lat, name))
    for name, lon, lat in DRIVER_POSITIONS:
        r.geoadd("drivers_locations", (lon, lat, name))
    print(f"{len(DELIVERY_POINTS)} lieux charges")
    print(f"{len(DRIVER_POSITIONS)} positions chargees")


def find_nearby_drivers(r, lieu="Marais", radius_km=2):
    coords = r.geopos("delivery_points", lieu)
    if not coords or not coords[0]:
        print(f"{lieu} introuvable")
        return []

    lon, lat = coords[0]
    results = r.geosearch(
        "drivers_locations",
        longitude=lon, latitude=lat,
        radius=radius_km, unit="km",
        sort="ASC", withcoord=True, withdist=True,
    )

    print(f"Livreurs dans {radius_km}km de {lieu} :")
    for member, dist, coord in results:
        print(f"  {member} : {dist}km ({coord[0]:.4f}, {coord[1]:.4f})")
    return results


def find_best_driver(r, lieu="Marais", radius_km=3):
    coords = r.geopos("delivery_points", lieu)
    if not coords or not coords[0]:
        print(f"{lieu} introuvable")
        return None

    lon, lat = coords[0]
    results = r.geosearch(
        "drivers_locations",
        longitude=lon, latitude=lat,
        radius=radius_km, unit="km",
        sort="ASC", withdist=True,
    )

    if not results:
        print(f"Aucun livreur dans {radius_km}km de {lieu}")
        return None

    candidates = []
    for member, dist in results:
        rating = float(r.hget(f"driver:{member}", "rating") or 0)
        candidates.append({"id": member, "dist_km": float(dist), "rating": rating})

    print(f"Candidats dans {radius_km}km de {lieu} :")
    for c in candidates:
        print(f"  {c['id']} : {c['dist_km']}km, rating {c['rating']}")

    by_dist = min(candidates, key=lambda c: c["dist_km"])
    by_rating = max(candidates, key=lambda c: c["rating"])

    print(f"Plus proche : {by_dist['id']} ({by_dist['dist_km']}km)")
    print(f"Mieux note  : {by_rating['id']} (rating {by_rating['rating']})")
    return by_dist


def monitor_driver(r, driver_id, new_lon, new_lat, zone_limit_km=5):
    r.geoadd("drivers_locations", (new_lon, new_lat, driver_id))
    dist = r.geodist("drivers_locations", driver_id, "paris_center", unit="km")
    if dist is None:
        r.geoadd("drivers_locations", (PARIS_CENTER[0], PARIS_CENTER[1], "paris_center"))
        dist = r.geodist("drivers_locations", driver_id, "paris_center", unit="km")

    print(f"{driver_id} -> ({new_lon}, {new_lat}), {dist}km du centre")
    if dist and float(dist) > zone_limit_km:
        print(f"ALERTE : {driver_id} hors zone (>{zone_limit_km}km)")
    return dist


if __name__ == "__main__":
    r = get_redis()

    print("--- Travail 1 : Positions geo-spatiales ---")
    init_geo_data(r)

    print("\n--- Travail 2 : Livreurs proches ---")
    nearby = find_nearby_drivers(r, "Marais", 2)
    print(f"\n2 plus proches du Marais :")
    for member, dist, coord in nearby[:2]:
        print(f"  {member} : {dist}km")

    print("\n--- Travail 3 : Affectation optimale ---")
    find_best_driver(r, "Marais", 3)

    print("\n--- Travail 4 : Monitoring ---")
    r.geoadd("drivers_locations", (PARIS_CENTER[0], PARIS_CENTER[1], "paris_center"))
    monitor_driver(r, "d1", 2.370, 48.865)
    monitor_driver(r, "d3", 2.100, 49.000)
