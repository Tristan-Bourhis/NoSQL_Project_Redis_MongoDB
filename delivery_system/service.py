from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from redis import Redis
from redis.exceptions import WatchError


@dataclass(frozen=True)
class OperationResult:
    ok: bool
    message: str


class DeliveryService:
    STATUS_SETS = {
        "en_attente": "orders:en_attente",
        "assignee": "orders:assignees",
        "livree": "orders:livrees",
    }

    def __init__(self, redis_client: Redis):
        self.redis = redis_client

    @staticmethod
    def _order_key(order_id: str) -> str:
        return f"order:{order_id}"

    @staticmethod
    def _driver_key(driver_id: str) -> str:
        return f"driver:{driver_id}"

    @staticmethod
    def _driver_orders_key(driver_id: str) -> str:
        return f"driver:{driver_id}:orders"

    def assign_order(self, order_id: str, driver_id: str) -> OperationResult:
        order_key = self._order_key(order_id)
        driver_key = self._driver_key(driver_id)

        while True:
            try:
                with self.redis.pipeline() as pipe:
                    pipe.watch(order_key, driver_key)

                    if not pipe.exists(order_key):
                        return OperationResult(False, "ORDER_NOT_FOUND")
                    if not pipe.exists(driver_key):
                        return OperationResult(False, "DRIVER_NOT_FOUND")

                    status = pipe.hget(order_key, "status")
                    if status != "en_attente":
                        return OperationResult(False, f"ORDER_NOT_PENDING (status={status})")

                    pipe.multi()
                    pipe.hset(order_key, mapping={"status": "assignee", "driver_id": driver_id})
                    pipe.srem(self.STATUS_SETS["en_attente"], order_id)
                    pipe.sadd(self.STATUS_SETS["assignee"], order_id)
                    pipe.sadd(self._driver_orders_key(driver_id), order_id)
                    pipe.hincrby(driver_key, "deliveries_in_progress", 1)
                    pipe.execute()
                    return OperationResult(True, "OK")
            except WatchError:
                continue

    def complete_delivery(self, order_id: str, driver_id: str) -> OperationResult:
        order_key = self._order_key(order_id)
        driver_key = self._driver_key(driver_id)
        driver_orders_key = self._driver_orders_key(driver_id)

        while True:
            try:
                with self.redis.pipeline() as pipe:
                    pipe.watch(order_key, driver_key)

                    if not pipe.exists(order_key):
                        return OperationResult(False, "ORDER_NOT_FOUND")
                    if not pipe.exists(driver_key):
                        return OperationResult(False, "DRIVER_NOT_FOUND")

                    status = pipe.hget(order_key, "status")
                    assigned_driver = pipe.hget(order_key, "driver_id")
                    if status != "assignee":
                        return OperationResult(False, f"ORDER_NOT_ASSIGNED (status={status})")
                    if assigned_driver != driver_id:
                        return OperationResult(
                            False,
                            f"ORDER_ASSIGNED_TO_OTHER_DRIVER (driver_id={assigned_driver})",
                        )

                    raw_in_progress = pipe.hget(driver_key, "deliveries_in_progress") or "0"
                    in_progress = int(raw_in_progress)

                    pipe.multi()
                    pipe.hset(order_key, "status", "livree")
                    pipe.srem(self.STATUS_SETS["assignee"], order_id)
                    pipe.sadd(self.STATUS_SETS["livree"], order_id)
                    pipe.srem(driver_orders_key, order_id)
                    if in_progress > 0:
                        pipe.hincrby(driver_key, "deliveries_in_progress", -1)
                    else:
                        pipe.hset(driver_key, "deliveries_in_progress", "0")
                    pipe.hincrby(driver_key, "deliveries_completed", 1)
                    pipe.execute()
                    return OperationResult(True, "OK")
            except WatchError:
                continue

    def count_orders_by_status(self) -> dict[str, int]:
        return {
            status: self.redis.scard(redis_key)
            for status, redis_key in self.STATUS_SETS.items()
        }

    def list_orders(self, status: str) -> list[str]:
        redis_key = self.STATUS_SETS[status]
        return sorted(self.redis.smembers(redis_key))

    def best_rated_driver(self) -> dict[str, Any] | None:
        top = self.redis.zrevrange("drivers:ratings", 0, 0, withscores=True)
        if not top:
            return None
        driver_id, rating = top[0]
        name = self.redis.hget(self._driver_key(driver_id), "name") or "N/A"
        return {"id": driver_id, "name": name, "rating": float(rating)}

    def top_rated_drivers(self, limit: int = 2) -> list[dict[str, Any]]:
        top = self.redis.zrevrange("drivers:ratings", 0, limit - 1, withscores=True)
        result: list[dict[str, Any]] = []
        for driver_id, rating in top:
            name = self.redis.hget(self._driver_key(driver_id), "name") or "N/A"
            result.append({"id": driver_id, "name": name, "rating": float(rating)})
        return result

    def deliveries_in_progress_per_driver(self) -> list[dict[str, Any]]:
        driver_ids = self.redis.zrange("drivers:ratings", 0, -1)
        if not driver_ids:
            return []

        pipe = self.redis.pipeline(transaction=False)
        for driver_id in driver_ids:
            pipe.hget(self._driver_key(driver_id), "name")
            pipe.hget(self._driver_key(driver_id), "deliveries_in_progress")
        raw = pipe.execute()

        result: list[dict[str, Any]] = []
        idx = 0
        for driver_id in driver_ids:
            name = raw[idx] or "N/A"
            in_progress = int(raw[idx + 1] or "0")
            idx += 2
            result.append({"id": driver_id, "name": name, "in_progress": in_progress})
        return result

    def order_snapshot(self, order_id: str) -> dict[str, str]:
        return self.redis.hgetall(self._order_key(order_id))

    def driver_snapshot(self, driver_id: str) -> dict[str, str]:
        return self.redis.hgetall(self._driver_key(driver_id))
