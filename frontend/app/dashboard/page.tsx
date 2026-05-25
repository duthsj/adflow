"use client";
import { useEffect, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import api from "@/lib/api";

interface Stats { active_clients: number; active_projects: number; content_this_week: number; }

export default function DashboardPage() {
  const [stats, setStats] = useState<Stats | null>(null);

  useEffect(() => {
    Promise.all([
      api.get("/clients"),
      api.get("/projects"),
      api.get("/content"),
    ]).then(([clients, projects, content]) => {
      const now = Date.now();
      const weekMs = 7 * 24 * 60 * 60 * 1000;
      setStats({
        active_clients: clients.data.filter((c: { active: boolean }) => c.active).length,
        active_projects: projects.data.filter((p: { status: string }) =>
          ["pending", "in_progress", "review"].includes(p.status)
        ).length,
        content_this_week: content.data.filter((c: { created_at: string }) =>
          new Date(c.created_at).getTime() > now - weekMs
        ).length,
      });
    });
  }, []);

  const cards = [
    { label: "Clientes Activos", value: stats?.active_clients },
    { label: "Proyectos en Curso", value: stats?.active_projects },
    { label: "Contenido Esta Semana", value: stats?.content_this_week },
  ];

  return (
    <div>
      <h1 className="text-2xl font-bold text-gray-900 mb-6">Dashboard</h1>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {cards.map(({ label, value }) => (
          <Card key={label}>
            <CardHeader>
              <CardTitle className="text-sm text-gray-500">{label}</CardTitle>
            </CardHeader>
            <CardContent>
              {value === undefined ? (
                <div className="h-9 w-16 bg-gray-100 rounded animate-pulse" />
              ) : (
                <p className="text-3xl font-bold">{value}</p>
              )}
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}
