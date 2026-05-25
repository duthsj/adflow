"use client";
import { useEffect, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import api from "@/lib/api";
import { toast } from "sonner";

interface BillingStatus {
  plan: "free" | "pro" | "agency";
  subscription_status: string;
}

const PLANS = [
  {
    id: "free",
    name: "Free",
    price: "$0",
    period: "",
    features: ["2 clientes", "10 contenidos/mes", "5 agentes AI", "Portal de aprobaciones"],
    priceId: null as string | null,
  },
  {
    id: "pro",
    name: "Pro",
    price: "$29",
    period: "/mes",
    features: ["20 clientes", "Contenido ilimitado", "5 agentes AI", "Analytics + PDF reports", "Media library"],
    priceId: "pro",
  },
  {
    id: "agency",
    name: "Agency",
    price: "$99",
    period: "/mes",
    features: ["Clientes ilimitados", "Todo en Pro", "Multi-workspace", "White label", "Soporte prioritario"],
    priceId: "agency",
  },
];

export default function BillingPage() {
  const [status, setStatus] = useState<BillingStatus | null>(null);
  const [loading, setLoading] = useState<string | null>(null);

  useEffect(() => {
    api.get("/billing/status").then((r) => setStatus(r.data)).catch(() => {});

    const params = new URLSearchParams(window.location.search);
    if (params.get("success")) toast.success("Suscripción activada. ¡Bienvenido!");
    if (params.get("cancelled")) toast.info("Pago cancelado.");
  }, []);

  const handleUpgrade = async (planId: string) => {
    setLoading(planId);
    try {
      const r = await api.post("/billing/checkout", { plan: planId });
      window.location.href = r.data.checkout_url;
    } catch {
      toast.error("Error iniciando el pago. Intenta de nuevo.");
      setLoading(null);
    }
  };

  const handlePortal = async () => {
    setLoading("portal");
    try {
      const r = await api.get("/billing/portal");
      window.location.href = r.data.portal_url;
    } catch {
      toast.error("Error abriendo el portal de facturación.");
      setLoading(null);
    }
  };

  const currentPlan = status?.plan ?? "free";

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Facturación</h1>
          <p className="text-sm text-gray-500 mt-1">
            Plan actual: <span className="font-medium capitalize">{currentPlan}</span>
            {status?.subscription_status === "active" && (
              <Badge className="ml-2 bg-green-100 text-green-700">Activo</Badge>
            )}
          </p>
        </div>
        {currentPlan !== "free" && (
          <Button variant="outline" onClick={handlePortal} disabled={loading === "portal"}>
            {loading === "portal" ? "Cargando..." : "Gestionar suscripción"}
          </Button>
        )}
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {PLANS.map((plan) => {
          const isCurrent = currentPlan === plan.id;
          return (
            <Card
              key={plan.id}
              className={`relative ${isCurrent ? "ring-2 ring-orange-500" : ""} ${plan.id === "pro" ? "shadow-lg" : ""}`}
            >
              {plan.id === "pro" && (
                <div className="absolute -top-3 left-1/2 -translate-x-1/2">
                  <Badge className="bg-orange-500 text-white px-3">Más popular</Badge>
                </div>
              )}
              <CardHeader className="pb-4">
                <div className="flex items-center justify-between">
                  <CardTitle className="text-lg">{plan.name}</CardTitle>
                  {isCurrent && <Badge variant="outline" className="text-orange-600 border-orange-300">Actual</Badge>}
                </div>
                <div className="flex items-baseline gap-1">
                  <span className="text-3xl font-bold">{plan.price}</span>
                  <span className="text-gray-500 text-sm">{plan.period}</span>
                </div>
              </CardHeader>
              <CardContent className="space-y-4">
                <ul className="space-y-2">
                  {plan.features.map((f) => (
                    <li key={f} className="flex items-center gap-2 text-sm text-gray-600">
                      <span className="text-orange-500">✓</span> {f}
                    </li>
                  ))}
                </ul>
                {!isCurrent && plan.priceId && (
                  <Button
                    className="w-full bg-orange-500 hover:bg-orange-600 text-white"
                    onClick={() => handleUpgrade(plan.priceId!)}
                    disabled={loading === plan.priceId}
                  >
                    {loading === plan.priceId ? "Redirigiendo..." : `Upgrade a ${plan.name}`}
                  </Button>
                )}
                {isCurrent && (
                  <Button className="w-full" variant="outline" disabled>
                    Plan actual
                  </Button>
                )}
              </CardContent>
            </Card>
          );
        })}
      </div>
    </div>
  );
}
