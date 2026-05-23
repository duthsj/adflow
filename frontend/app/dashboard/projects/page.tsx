"use client";
import { useEffect, useState } from "react";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import api from "@/lib/api";
import { Project } from "@/types";

const STATUS_LABELS: Record<string, string> = {
  pending: "Pendiente",
  in_progress: "En curso",
  review: "Revisión",
  approved: "Aprobado",
  delivered: "Entregado",
};

const STATUS_VARIANTS: Record<
  string,
  "default" | "secondary" | "outline" | "destructive"
> = {
  pending: "secondary",
  in_progress: "default",
  review: "outline",
  approved: "default",
  delivered: "secondary",
};

export default function ProjectsPage() {
  const [projects, setProjects] = useState<Project[]>([]);

  useEffect(() => {
    api.get("/projects").then((r) => setProjects(r.data));
  }, []);

  return (
    <div>
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold">Proyectos</h1>
        <Link href="/dashboard/projects/new">
          <Button>+ Nuevo Proyecto</Button>
        </Link>
      </div>
      <div className="bg-white border rounded-lg divide-y">
        {projects.map((p) => (
          <Link key={p.id} href={`/dashboard/projects/${p.id}`}>
            <div className="flex items-center justify-between p-4 hover:bg-gray-50">
              <div>
                <h3 className="font-medium">{p.title}</h3>
                <p className="text-sm text-gray-500">
                  {p.service_type.replace("_", " ")}
                </p>
              </div>
              <Badge variant={STATUS_VARIANTS[p.status]}>
                {STATUS_LABELS[p.status]}
              </Badge>
            </div>
          </Link>
        ))}
        {projects.length === 0 && (
          <p className="text-center text-gray-400 py-12">
            No hay proyectos. Crea el primero.
          </p>
        )}
      </div>
    </div>
  );
}
