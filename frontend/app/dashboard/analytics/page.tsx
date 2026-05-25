"use client";
import { useEffect, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import KPICard from "@/components/analytics/KPICard";
import PostsChart from "@/components/analytics/PostsChart";
import PlatformChart from "@/components/analytics/PlatformChart";
import api from "@/lib/api";
import { toast } from "sonner";

interface Client { id: number; name: string; }
interface Summary { total_posts: number; avg_reach: number; avg_engagement: number; pending_approvals: number; }
interface PlatformStat { platform: string; posts: number; reach: number; engagement: number; }

export default function AnalyticsPage() {
  const [clients, setClients] = useState<Client[]>([]);
  const [selectedClient, setSelectedClient] = useState<number | null>(null);
  const [period, setPeriod] = useState<"week" | "month">("week");
  const [summary, setSummary] = useState<Summary | null>(null);
  const [platforms, setPlatforms] = useState<PlatformStat[]>([]);
  const [insights, setInsights] = useState<string[]>([]);
  const [loadingInsights, setLoadingInsights] = useState(false);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    api.get("/clients").then((r) => {
      setClients(r.data);
      if (r.data.length > 0) setSelectedClient(r.data[0].id);
    });
  }, []);

  useEffect(() => {
    if (!selectedClient) return;
    setLoading(true);
    Promise.all([
      api.get(`/analytics/summary?client_id=${selectedClient}&period=${period}`),
      api.get(`/analytics/by-platform?client_id=${selectedClient}&period=${period}`),
    ])
      .then(([s, p]) => {
        setSummary(s.data);
        setPlatforms(p.data);
        setInsights([]);
      })
      .catch(() => toast.error("Error cargando analytics"))
      .finally(() => setLoading(false));
  }, [selectedClient, period]);

  const loadInsights = async () => {
    if (!selectedClient) return;
    setLoadingInsights(true);
    try {
      const r = await api.post("/analytics/insights", { client_id: selectedClient, period });
      setInsights(r.data.insights);
    } catch {
      toast.error("Error generando insights");
    } finally {
      setLoadingInsights(false);
    }
  };

  const downloadReport = async () => {
    if (!selectedClient) return;
    try {
      const r = await api.post(
        "/reports/generate",
        { client_id: selectedClient, period, include_insights: insights.length > 0 },
        { responseType: "blob" }
      );
      const url = URL.createObjectURL(new Blob([r.data], { type: "application/pdf" }));
      const a = document.createElement("a");
      a.href = url;
      a.download = `reporte-${period}.pdf`;
      a.click();
      URL.revokeObjectURL(url);
      toast.success("Reporte descargado");
    } catch {
      toast.error("Error generando reporte");
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900">Analytics</h1>
        <div className="flex gap-2">
          <select
            className="border rounded-lg px-3 py-2 text-sm bg-white"
            value={selectedClient ?? ""}
            onChange={(e) => setSelectedClient(Number(e.target.value))}
          >
            {clients.map((c) => (
              <option key={c.id} value={c.id}>{c.name}</option>
            ))}
          </select>
          <select
            className="border rounded-lg px-3 py-2 text-sm bg-white"
            value={period}
            onChange={(e) => setPeriod(e.target.value as "week" | "month")}
          >
            <option value="week">Esta semana</option>
            <option value="month">Este mes</option>
          </select>
          <Button variant="outline" size="sm" onClick={downloadReport}>
            Descargar PDF
          </Button>
        </div>
      </div>

      {loading ? (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {[...Array(4)].map((_, i) => (
            <div key={i} className="h-28 bg-gray-100 rounded-xl animate-pulse" />
          ))}
        </div>
      ) : summary ? (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <KPICard label="Posts publicados" value={summary.total_posts} sub={period === "week" ? "esta semana" : "este mes"} />
          <KPICard label="Alcance promedio" value={summary.avg_reach.toFixed(0)} />
          <KPICard label="Engagement" value={`${summary.avg_engagement.toFixed(1)}%`} />
          <KPICard label="Aprobaciones pendientes" value={summary.pending_approvals} />
        </div>
      ) : (
        <div className="text-center py-12 text-gray-400">
          {clients.length === 0 ? "Crea un cliente para ver analytics" : "Sin datos"}
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle className="text-sm font-medium text-gray-700">Posts por período</CardTitle>
          </CardHeader>
          <CardContent>
            <PostsChart data={[]} />
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle className="text-sm font-medium text-gray-700">Por plataforma</CardTitle>
          </CardHeader>
          <CardContent>
            <PlatformChart data={platforms} />
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader className="flex flex-row items-center justify-between">
          <CardTitle className="text-sm font-medium text-gray-700">AI Insights</CardTitle>
          <Button size="sm" variant="outline" onClick={loadInsights} disabled={loadingInsights}>
            {loadingInsights ? "Generando..." : "Generar insights"}
          </Button>
        </CardHeader>
        <CardContent>
          {insights.length > 0 ? (
            <ul className="space-y-2">
              {insights.map((ins, i) => (
                <li key={i} className="flex gap-2 text-sm text-gray-700">
                  <span className="text-orange-500 font-bold">{i + 1}.</span>
                  {ins}
                </li>
              ))}
            </ul>
          ) : (
            <p className="text-sm text-gray-400">
              Haz clic en &quot;Generar insights&quot; para ver recomendaciones AI
            </p>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
