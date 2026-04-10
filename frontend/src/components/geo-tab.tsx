import { useState, useEffect } from "react"
import { MapContainer, TileLayer, Marker, Popup, Circle, useMap } from "react-leaflet"
import L from "leaflet"
import { useGeoPoints, useGeoNearby, useGeoInit } from "@/hooks/use-delivery"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import "leaflet/dist/leaflet.css"

const blueIcon = new L.Icon({
  iconUrl: "https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-blue.png",
  shadowUrl: "https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-shadow.png",
  iconSize: [25, 41], iconAnchor: [12, 41], popupAnchor: [1, -34],
})

const greenIcon = new L.Icon({
  iconUrl: "https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-green.png",
  shadowUrl: "https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-shadow.png",
  iconSize: [25, 41], iconAnchor: [12, 41], popupAnchor: [1, -34],
})

const redIcon = new L.Icon({
  iconUrl: "https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-red.png",
  shadowUrl: "https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-shadow.png",
  iconSize: [25, 41], iconAnchor: [12, 41], popupAnchor: [1, -34],
})

function FitBounds({ points }: { points: [number, number][] }) {
  const map = useMap()
  useEffect(() => {
    if (points.length > 0) map.fitBounds(points, { padding: [30, 30] })
  }, [points, map])
  return null
}

export function GeoTab() {
  const [lieu, setLieu] = useState("Marais")
  const [radius, setRadius] = useState(2)
  const [searchEnabled, setSearchEnabled] = useState(false)
  const points = useGeoPoints()
  const nearby = useGeoNearby(lieu, radius, searchEnabled)
  const geoInit = useGeoInit()

  const selectedPoint = points.data?.delivery_points.find((p: any) => p.name === lieu)
  const allCoords: [number, number][] = [
    ...(points.data?.delivery_points.map((p: any) => [p.lat, p.lon] as [number, number]) || []),
    ...(points.data?.driver_positions.map((p: any) => [p.lat, p.lon] as [number, number]) || []),
  ]

  const nearbyIds = new Set(nearby.data?.map((d: any) => d.id) || [])

  return (
    <div className="space-y-4">
      <div className="flex gap-2 items-center">
        <Button variant="outline" onClick={() => geoInit.mutate()}>Init geo data</Button>
        <select className="border rounded px-2 py-1 text-sm" value={lieu} onChange={(e) => { setLieu(e.target.value); setSearchEnabled(false) }}>
          {points.data?.delivery_points.map((p: any) => (
            <option key={p.name} value={p.name}>{p.name}</option>
          ))}
        </select>
        <input type="number" className="border rounded px-2 py-1 text-sm w-20" value={radius} onChange={(e) => setRadius(Number(e.target.value))} min={0.5} max={20} step={0.5} />
        <span className="text-sm">km</span>
        <Button onClick={() => setSearchEnabled(true)}>Chercher</Button>
      </div>

      <div className="grid grid-cols-3 gap-4">
        <Card className="col-span-2">
          <CardContent className="p-0">
            <MapContainer center={[48.861, 2.364]} zoom={13} style={{ height: 450, borderRadius: "0.75rem" }}>
              <TileLayer url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" />
              <FitBounds points={allCoords} />
              {points.data?.delivery_points.map((p: any) => (
                <Marker key={p.name} position={[p.lat, p.lon]} icon={blueIcon}>
                  <Popup>{p.name}</Popup>
                </Marker>
              ))}
              {points.data?.driver_positions.map((p: any) => (
                <Marker key={p.name} position={[p.lat, p.lon]} icon={nearbyIds.has(p.name) ? greenIcon : redIcon}>
                  <Popup>{p.name}</Popup>
                </Marker>
              ))}
              {searchEnabled && selectedPoint && (
                <Circle center={[selectedPoint.lat, selectedPoint.lon]} radius={radius * 1000} pathOptions={{ color: "blue", fillOpacity: 0.1 }} />
              )}
            </MapContainer>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Livreurs proches</CardTitle>
          </CardHeader>
          <CardContent>
            {!searchEnabled && <p className="text-sm text-gray-400">Cliquer "Chercher"</p>}
            {nearby.data?.length === 0 && searchEnabled && <p className="text-sm">Aucun</p>}
            {nearby.data?.map((d: any, i: number) => (
              <div key={d.id} className="flex justify-between border-b py-2 text-sm">
                <div>
                  <span className="font-medium">{d.name}</span>
                  <span className="ml-2 text-gray-500 text-xs">{d.id} - rating {d.rating}</span>
                </div>
                <span>{d.dist_km.toFixed(2)} km</span>
              </div>
            ))}
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
