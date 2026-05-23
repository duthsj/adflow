"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import api from "@/lib/api";

export default function ClientForm() {
  const router = useRouter();
  const [loading, setLoading] = useState(false);
  const [form, setForm] = useState({
    name: "",
    industry: "",
    brand_guidelines: { tone: "", colors: "", keywords: "", avoid: "" },
    social_accounts: { instagram: "", facebook: "", tiktok: "" },
  });

  const set = (key: string, value: string) =>
    setForm((f) => ({ ...f, [key]: value }));
  const setBrand = (key: string, value: string) =>
    setForm((f) => ({ ...f, brand_guidelines: { ...f.brand_guidelines, [key]: value } }));
  const setSocial = (key: string, value: string) =>
    setForm((f) => ({ ...f, social_accounts: { ...f.social_accounts, [key]: value } }));

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try {
      await api.post("/clients", {
        name: form.name,
        industry: form.industry,
        brand_guidelines: {
          tone: form.brand_guidelines.tone,
          colors: form.brand_guidelines.colors
            .split(",")
            .map((s) => s.trim())
            .filter(Boolean),
          keywords: form.brand_guidelines.keywords
            .split(",")
            .map((s) => s.trim())
            .filter(Boolean),
          avoid: form.brand_guidelines.avoid
            .split(",")
            .map((s) => s.trim())
            .filter(Boolean),
          fonts: [],
        },
        social_accounts: {
          instagram: form.social_accounts.instagram || undefined,
          facebook: form.social_accounts.facebook || undefined,
          tiktok: form.social_accounts.tiktok || undefined,
        },
      });
      router.push("/dashboard/clients");
    } finally {
      setLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-6 max-w-2xl">
      <div className="grid grid-cols-2 gap-4">
        <div>
          <Label>Nombre del cliente</Label>
          <Input
            value={form.name}
            onChange={(e) => set("name", e.target.value)}
            required
          />
        </div>
        <div>
          <Label>Industria</Label>
          <Input
            value={form.industry}
            onChange={(e) => set("industry", e.target.value)}
            required
          />
        </div>
      </div>
      <div>
        <h3 className="font-semibold mb-3">Brand Guidelines</h3>
        <div className="space-y-3">
          <div>
            <Label>Tono de voz</Label>
            <Input
              placeholder="ej: profesional, cercano, divertido"
              value={form.brand_guidelines.tone}
              onChange={(e) => setBrand("tone", e.target.value)}
            />
          </div>
          <div>
            <Label>Keywords (separadas por coma)</Label>
            <Input
              placeholder="ej: innovación, calidad, confianza"
              value={form.brand_guidelines.keywords}
              onChange={(e) => setBrand("keywords", e.target.value)}
            />
          </div>
          <div>
            <Label>Evitar (separadas por coma)</Label>
            <Input
              placeholder="ej: competencia, precio, descuento"
              value={form.brand_guidelines.avoid}
              onChange={(e) => setBrand("avoid", e.target.value)}
            />
          </div>
        </div>
      </div>
      <div>
        <h3 className="font-semibold mb-3">Redes Sociales</h3>
        <div className="grid grid-cols-3 gap-3">
          <div>
            <Label>Instagram</Label>
            <Input
              placeholder="@handle"
              value={form.social_accounts.instagram}
              onChange={(e) => setSocial("instagram", e.target.value)}
            />
          </div>
          <div>
            <Label>Facebook</Label>
            <Input
              placeholder="página"
              value={form.social_accounts.facebook}
              onChange={(e) => setSocial("facebook", e.target.value)}
            />
          </div>
          <div>
            <Label>TikTok</Label>
            <Input
              placeholder="@handle"
              value={form.social_accounts.tiktok}
              onChange={(e) => setSocial("tiktok", e.target.value)}
            />
          </div>
        </div>
      </div>
      <Button type="submit" disabled={loading}>
        {loading ? "Guardando..." : "Crear Cliente"}
      </Button>
    </form>
  );
}
