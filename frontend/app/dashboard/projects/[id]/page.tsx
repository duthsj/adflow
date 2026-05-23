"use client";
import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import ContentGenerator from "@/components/agents/ContentGenerator";
import api from "@/lib/api";
import { Project, ContentItem } from "@/types";

const STATUS_LABELS: Record<string, string> = {
  pending: "Pendiente",
  in_progress: "En curso",
  review: "Revisión",
  approved: "Aprobado",
  delivered: "Entregado",
};

export default function ProjectDetailPage() {
  const { id } = useParams<{ id: string }>();
  const [project, setProject] = useState<Project | null>(null);
  const [content, setContent] = useState<ContentItem[]>([]);

  useEffect(() => {
    api.get(`/projects/${id}`).then((r) => setProject(r.data));
    api.get(`/content?project_id=${id}`).then((r) => setContent(r.data));
  }, [id]);

  const handleGenerated = (item: ContentItem) => {
    setContent((prev) => [item, ...prev]);
  };

  const approve = async (contentId: number) => {
    await api.post("/content/approve", { content_id: contentId });
    setContent((prev) =>
      prev.map((c) =>
        c.id === contentId ? { ...c, status: "approved" as const } : c
      )
    );
  };

  if (!project) return <div className="text-gray-400">Cargando...</div>;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">{project.title}</h1>
        <p className="text-gray-500 mt-1">
          {project.service_type.replace("_", " ")} &middot;{" "}
          {STATUS_LABELS[project.status]}
        </p>
      </div>

      {project.service_type === "social_media" && (
        <ContentGenerator
          projectId={project.id}
          onGenerated={handleGenerated}
        />
      )}

      <div>
        <h2 className="font-semibold mb-3">
          Contenido generado ({content.length})
        </h2>
        <div className="space-y-3">
          {content.map((c) => (
            <div key={c.id} className="bg-white border rounded-lg p-4">
              <div className="flex justify-between items-start mb-2">
                <Badge variant="outline">{c.type}</Badge>
                <Badge
                  variant={c.status === "approved" ? "default" : "secondary"}
                >
                  {c.status}
                </Badge>
              </div>
              <p className="text-sm text-gray-800 whitespace-pre-wrap">
                {c.body}
              </p>
              {c.status === "draft" && (
                <Button
                  size="sm"
                  variant="outline"
                  className="mt-3"
                  onClick={() => approve(c.id)}
                >
                  Aprobar
                </Button>
              )}
            </div>
          ))}
          {content.length === 0 && (
            <p className="text-gray-400 text-center py-8">
              Sin contenido aún. Genera el primero.
            </p>
          )}
        </div>
      </div>
    </div>
  );
}
