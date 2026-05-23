"use client";
import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import api from "@/lib/api";
import { ContentItem } from "@/types";

interface Props {
  projectId: number;
  onGenerated: (item: ContentItem) => void;
}

export default function ContentGenerator({ projectId, onGenerated }: Props) {
  const [contentType, setContentType] = useState("post");
  const [instructions, setInstructions] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const generate = async () => {
    setLoading(true);
    setError("");
    try {
      const { data } = await api.post("/content/generate", {
        project_id: projectId,
        content_type: contentType,
        instructions: instructions || undefined,
      });
      onGenerated(data);
      setInstructions("");
    } catch {
      setError("Error al generar contenido. Intenta de nuevo.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="bg-white border rounded-lg p-6 space-y-4">
      <div className="flex items-center gap-2">
        <h3 className="font-semibold">Generar Contenido AI</h3>
        <Badge variant="secondary">Claude Sonnet 4.6</Badge>
      </div>
      <div>
        <Label>Tipo de contenido</Label>
        <Select value={contentType} onValueChange={(v) => setContentType(v ?? contentType)}>
          <SelectTrigger>
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="post">Post</SelectItem>
            <SelectItem value="story">Story</SelectItem>
            <SelectItem value="reel">Reel (caption)</SelectItem>
            <SelectItem value="carousel">Carrusel</SelectItem>
          </SelectContent>
        </Select>
      </div>
      <div>
        <Label>Instrucciones adicionales (opcional)</Label>
        <Textarea
          placeholder="ej: Enfocarse en el lanzamiento del nuevo producto, incluir CTA para link en bio..."
          value={instructions}
          onChange={(e) => setInstructions(e.target.value)}
          rows={3}
        />
      </div>
      {error && <p className="text-red-500 text-sm">{error}</p>}
      <Button onClick={generate} disabled={loading} className="w-full">
        {loading ? "Generando..." : "Generar con AI"}
      </Button>
    </div>
  );
}
