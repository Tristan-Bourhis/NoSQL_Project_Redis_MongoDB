import * as Tabs from "@radix-ui/react-tabs"
import { OrdersTab } from "./orders-tab"
import { DriversTab } from "./drivers-tab"
import { GeoTab } from "./geo-tab"
import { AnalyticsTab } from "./analytics-tab"

const tabs = [
  { value: "orders", label: "Commandes", component: OrdersTab },
  { value: "drivers", label: "Livreurs", component: DriversTab },
  { value: "geo", label: "Geo", component: GeoTab },
  { value: "analytics", label: "Analytics", component: AnalyticsTab },
]

export function Dashboard() {
  return (
    <div className="min-h-screen bg-[hsl(var(--background))] p-6">
      <h1 className="text-2xl font-bold mb-6">Systeme de livraison</h1>
      <Tabs.Root defaultValue="orders">
        <Tabs.List className="flex border-b mb-4">
          {tabs.map((t) => (
            <Tabs.Trigger
              key={t.value}
              value={t.value}
              className="px-4 py-2 text-sm font-medium border-b-2 border-transparent data-[state=active]:border-[hsl(var(--primary))] data-[state=active]:text-[hsl(var(--foreground))] text-[hsl(var(--muted-foreground))] transition-colors"
            >
              {t.label}
            </Tabs.Trigger>
          ))}
        </Tabs.List>
        {tabs.map((t) => (
          <Tabs.Content key={t.value} value={t.value}>
            <t.component />
          </Tabs.Content>
        ))}
      </Tabs.Root>
    </div>
  )
}
