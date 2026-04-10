import { useRegionStats, useAnalyticsTopDrivers, useDeliveryCount } from "@/hooks/use-delivery"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"

export function AnalyticsTab() {
  const regions = useRegionStats()
  const topDrivers = useAnalyticsTopDrivers(5)
  const count = useDeliveryCount()

  return (
    <div className="space-y-4">
      <Card>
        <CardHeader>
          <CardTitle>Total livraisons : {count.data?.count ?? "..."}</CardTitle>
        </CardHeader>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Performance par region</CardTitle>
        </CardHeader>
        <CardContent>
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b text-left">
                <th className="p-2">Region</th>
                <th className="p-2">Livraisons</th>
                <th className="p-2">Revenu</th>
                <th className="p-2">Duree moy</th>
                <th className="p-2">Rating moy</th>
              </tr>
            </thead>
            <tbody>
              {regions.data?.map((r: any) => (
                <tr key={r.region} className="border-b">
                  <td className="p-2 font-medium">{r.region}</td>
                  <td className="p-2">{r.nb_livraisons}</td>
                  <td className="p-2">{r.revenu_total}E</td>
                  <td className="p-2">{r.duree_moy}min</td>
                  <td className="p-2">{r.rating_moy}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Top livreurs par revenu</CardTitle>
        </CardHeader>
        <CardContent>
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b text-left">
                <th className="p-2">#</th>
                <th className="p-2">Livreur</th>
                <th className="p-2">Livraisons</th>
                <th className="p-2">Revenu</th>
                <th className="p-2">Duree moy</th>
                <th className="p-2">Rating moy</th>
              </tr>
            </thead>
            <tbody>
              {topDrivers.data?.map((d: any, i: number) => (
                <tr key={d.driver_id} className="border-b">
                  <td className="p-2 font-bold">#{i + 1}</td>
                  <td className="p-2">{d.driver_name} ({d.driver_id})</td>
                  <td className="p-2">{d.nb_livraisons}</td>
                  <td className="p-2">{d.revenu_total}E</td>
                  <td className="p-2">{d.duree_moy}min</td>
                  <td className="p-2">{d.rating_moy}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </CardContent>
      </Card>
    </div>
  )
}
