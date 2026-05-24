"use client";
import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import {
  Select, SelectContent, SelectItem, SelectTrigger, SelectValue,
} from "@/components/ui/select";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import api from "@/lib/api";
import { ContentItem, ServiceType } from "@/types";

interface Props {
  projectId: number;
  serviceType: ServiceType;
  onGenerated: (item: ContentItem) => void;
}

const CONTENT_TYPES: Record<ServiceType, { value: string; label: string }[]> = {
  social_media: [
    { value: "post", label: "Post" },
    { value: "story", label: "Story" },
    { value: "reel", label: "Reel (caption)" },
    { value: "carousel", label: "Carrusel" },
  ],
  ads: [
    { value: "facebook_ad", label: "Facebook/Instagram Ad" },
    { value: "google_search_ad", label: "Google Search Ad" },
    { value: "ab_test", label: "A/B Test Variants" },
    { value: "story_ad", label: "Story Ad" },
  ],
  seo: [
    { value: "blog_post", label: "Blog Post" },
    { value: "meta_tags", label: "Meta Tags" },
    { value: "keyword_research", label: "Keyword Research" },
    { value: "product_description", label: "Product Description" },
  ],
  design: [
    { value: "image_prompt", label: "Image Gen Prompt" },
    { value: "design_brief", label: "Design Brief" },
    { value: "banner_brief", label: "Banner Brief" },
    { value: "logo_brief", label: "Logo Brief" },
  ],
  video: [
    { value: "reel_script", label: "Reel Script" },
    { value: "storyboard", label: "Storyboard" },
    { value: "youtube_script", label: "YouTube Script" },
    { value: "caption", label: "Video Caption" },
    { value: "thumbnail_brief", label: "Thumbnail Brief" },
  ],
};

const AGENT_LABELS: Record<ServiceType, string> = {
  social_media: "Social Media Agent",
  ads: "Ads Agent",
  seo: "SEO Agent",
  design: "Design Agent",
  video: "Video Agent",
};

export default function ContentGenerator({ projectId, serviceType, onGenerated }: Props) {
  const options = CONTENT_TYPES[serviceType] || CONTENT_TYPES.social_media;
  const [contentType, setContentType] = useState(options[0].value);
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
        <Badge variant="secondary">{AGENT_LABELS[serviceType]}</Badge>
      </div>
      <div>
        <Label>Tipo de contenido</Label>
        <Select value={contentType} onValueChange={(v) => setContentType(v ?? contentType)}>
          <SelectTrigger><SelectValue /></SelectTrigger>
          <SelectContent>
            {options.map((o) => (
              <SelectItem key={o.value} value={o.value}>{o.label}</SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>
      <div>
        <Label>Instrucciones adicionales (opcional)</Label>
        <Textarea
          placeholder="ej: Enfocarse en el lanzamiento del nuevo producto..."
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
