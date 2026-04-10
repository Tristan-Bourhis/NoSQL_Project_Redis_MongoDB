import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import { api } from "@/lib/api"

export function useOrderCounts() {
  return useQuery({
    queryKey: ["order-counts"],
    queryFn: () => api.get<Record<string, number>>("/orders/counts"),
    refetchInterval: 5000,
  })
}

export function useOrders(status: string) {
  return useQuery({
    queryKey: ["orders", status],
    queryFn: () => api.get<any[]>(`/orders?status=${status}`),
    refetchInterval: 5000,
  })
}

export function useDrivers() {
  return useQuery({
    queryKey: ["drivers"],
    queryFn: () => api.get<any[]>("/drivers"),
    refetchInterval: 5000,
  })
}

export function useDriversByRegion(region: string) {
  return useQuery({
    queryKey: ["drivers-region", region],
    queryFn: () => api.get<any[]>(`/drivers/by-region?region=${region}`),
  })
}

export function useTopDrivers(limit = 5) {
  return useQuery({
    queryKey: ["top-drivers", limit],
    queryFn: () => api.get<any[]>(`/drivers/top?limit=${limit}`),
  })
}

export function useGeoPoints() {
  return useQuery({
    queryKey: ["geo-points"],
    queryFn: () => api.get<{ delivery_points: any[]; driver_positions: any[] }>("/geo/points"),
  })
}

export function useGeoNearby(lieu: string, radius: number, enabled: boolean) {
  return useQuery({
    queryKey: ["geo-nearby", lieu, radius],
    queryFn: () => api.get<any[]>(`/geo/nearby?lieu=${lieu}&radius=${radius}`),
    enabled,
  })
}

export function useRegionStats() {
  return useQuery({
    queryKey: ["region-stats"],
    queryFn: () => api.get<any[]>("/analytics/regions"),
  })
}

export function useAnalyticsTopDrivers(limit = 5) {
  return useQuery({
    queryKey: ["analytics-top", limit],
    queryFn: () => api.get<any[]>(`/analytics/top-drivers?limit=${limit}`),
  })
}

export function useDeliveryCount() {
  return useQuery({
    queryKey: ["delivery-count"],
    queryFn: () => api.get<{ count: number }>("/analytics/deliveries/count"),
  })
}

export function useAssignOrder() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ orderId, driverId }: { orderId: string; driverId: string }) =>
      api.post(`/orders/${orderId}/assign`, { driver_id: driverId }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["orders"] })
      qc.invalidateQueries({ queryKey: ["order-counts"] })
      qc.invalidateQueries({ queryKey: ["drivers"] })
    },
  })
}

export function useCompleteOrder() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ orderId, driverId }: { orderId: string; driverId: string }) =>
      api.post(`/orders/${orderId}/complete`, { driver_id: driverId }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["orders"] })
      qc.invalidateQueries({ queryKey: ["order-counts"] })
      qc.invalidateQueries({ queryKey: ["drivers"] })
      qc.invalidateQueries({ queryKey: ["delivery-count"] })
    },
  })
}

export function useGeoInit() {
  return useMutation({
    mutationFn: () => api.post("/geo/init"),
  })
}
