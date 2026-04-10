import { useState } from "react"
import { useOrders, useOrderCounts, useDrivers, useAssignOrder, useCompleteOrder } from "@/hooks/use-delivery"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"

const STATUS_VARIANT: Record<string, "warning" | "default" | "success"> = {
  en_attente: "warning",
  assignee: "default",
  livree: "success",
}

export function OrdersTab() {
  const [status, setStatus] = useState("en_attente")
  const counts = useOrderCounts()
  const orders = useOrders(status)
  const drivers = useDrivers()
  const assign = useAssignOrder()
  const complete = useCompleteOrder()
  const [selectedDrivers, setSelectedDrivers] = useState<Record<string, string>>({})

  return (
    <div className="space-y-4">
      <div className="flex gap-3">
        {counts.data && Object.entries(counts.data).map(([s, n]: [string, number]) => (
          <Card key={s} className={`cursor-pointer flex-1 ${status === s ? "ring-2 ring-[hsl(var(--ring))]" : ""}`} onClick={() => setStatus(s)}>
            <CardHeader className="p-4">
              <CardTitle className="text-sm">{s}</CardTitle>
            </CardHeader>
            <CardContent className="p-4 pt-0">
              <span className="text-2xl font-bold">{n}</span>
            </CardContent>
          </Card>
        ))}
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Commandes - {status}</CardTitle>
        </CardHeader>
        <CardContent>
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b text-left">
                <th className="p-2">ID</th>
                <th className="p-2">Client</th>
                <th className="p-2">Destination</th>
                <th className="p-2">Region</th>
                <th className="p-2">Montant</th>
                <th className="p-2">Statut</th>
                <th className="p-2">Actions</th>
              </tr>
            </thead>
            <tbody>
              {orders.data?.map((o: any) => (
                <tr key={o.id} className="border-b">
                  <td className="p-2 font-mono">{o.id}</td>
                  <td className="p-2">{o.client}</td>
                  <td className="p-2">{o.destination}</td>
                  <td className="p-2">{o.region}</td>
                  <td className="p-2">{o.amount}E</td>
                  <td className="p-2"><Badge variant={STATUS_VARIANT[o.status]}>{o.status}</Badge></td>
                  <td className="p-2 flex gap-1 items-center">
                    {o.status === "en_attente" && (
                      <>
                        <select
                          className="border rounded px-1 py-0.5 text-xs"
                          value={selectedDrivers[o.id] || ""}
                          onChange={(e) => setSelectedDrivers((prev) => ({ ...prev, [o.id]: e.target.value }))}
                        >
                          <option value="">livreur</option>
                          {drivers.data?.map((d: any) => (
                            <option key={d.id} value={d.id}>{d.id} - {d.name}</option>
                          ))}
                        </select>
                        <Button size="sm" disabled={!selectedDrivers[o.id]} onClick={() => assign.mutate({ orderId: o.id, driverId: selectedDrivers[o.id] })}>
                          Assigner
                        </Button>
                      </>
                    )}
                    {o.status === "assignee" && o.driver_id && (
                      <Button size="sm" variant="secondary" onClick={() => complete.mutate({ orderId: o.id, driverId: o.driver_id })}>
                        Completer
                      </Button>
                    )}
                    {o.status === "livree" && <span className="text-xs text-gray-400">terminee</span>}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </CardContent>
      </Card>
    </div>
  )
}
