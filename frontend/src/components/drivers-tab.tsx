import { useState } from "react"
import { useDrivers, useTopDrivers } from "@/hooks/use-delivery"
import { Badge } from "@/components/ui/badge"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"

export function DriversTab() {
  const [regionFilter, setRegionFilter] = useState("all")
  const drivers = useDrivers()
  const top5 = useTopDrivers(5)

  const filtered = regionFilter === "all"
    ? drivers.data
    : drivers.data?.filter((d: any) => d.regions?.includes(regionFilter))

  return (
    <div className="space-y-4">
      <Card>
        <CardHeader>
          <CardTitle>Top 5 par rating</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex gap-3">
            {top5.data?.map((d: any, i: number) => (
              <div key={d.id} className="flex items-center gap-2 rounded-lg border p-3 flex-1">
                <span className="text-lg font-bold">#{i + 1}</span>
                <div className="text-left">
                  <div className="text-sm font-medium">{d.name}</div>
                  <div className="text-xs text-gray-500">{d.id} - {d.rating}</div>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="flex flex-row items-center justify-between">
          <CardTitle>Livreurs</CardTitle>
          <select
            className="border rounded px-2 py-1 text-sm"
            value={regionFilter}
            onChange={(e) => setRegionFilter(e.target.value)}
          >
            <option value="all">Toutes regions</option>
            <option value="Paris">Paris</option>
            <option value="Banlieue">Banlieue</option>
          </select>
        </CardHeader>
        <CardContent>
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b text-left">
                <th className="p-2">ID</th>
                <th className="p-2">Nom</th>
                <th className="p-2">Rating</th>
                <th className="p-2">Regions</th>
                <th className="p-2">En cours</th>
                <th className="p-2">Completees</th>
              </tr>
            </thead>
            <tbody>
              {filtered?.map((d: any) => (
                <tr key={d.id} className="border-b">
                  <td className="p-2 font-mono">{d.id}</td>
                  <td className="p-2">{d.name}</td>
                  <td className="p-2">{d.rating}</td>
                  <td className="p-2">
                    {d.regions?.map((r: string) => (
                      <Badge key={r} variant="secondary" className="mr-1">{r}</Badge>
                    ))}
                  </td>
                  <td className="p-2">{d.deliveries_in_progress || 0}</td>
                  <td className="p-2">{d.deliveries_completed || 0}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </CardContent>
      </Card>
    </div>
  )
}
