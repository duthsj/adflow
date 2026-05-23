"use client";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import api from "@/lib/api";
import { Client } from "@/types";

export default function NewProjectPage() {
  const router = useRouter();
  const [clients, setClients] = useState<Client[]>([]);
  const [form, setForm] = useState({
    client_id: "",
    title: "",
    service_type: "",
  });

  useEffect(() => {
    api.get("/clients").then((r) => setClients(r.data));
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    await api.post("/projects", {
      ...form,
      client_id: parseInt(form.client_id),
    });
    router.push("/dashboard/projects");
  };

  return (
    <div>
      <h1 className="text-2xl font-bold mb-6">Nuevo Proyecto</h1>
      <form onSubmit={handleSubmit} className="space-y-4 max-w-lg">
        <div>
          <Label>Cliente</Label>
          <Select
            onValueChange={(v) => setForm((f) => ({ ...f, client_id: (v as string) || "" }))}
          >
            <SelectTrigger>
              <SelectValue placeholder="Seleccionar cliente" />
            </SelectTrigger>
            <SelectContent>
              {clients.map((c) => (
                <SelectItem key={c.id} value={String(c.id)}>
                  {c.name}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
        <div>
          <Label>Título del proyecto</Label>
          <Input
            value={form.title}
            onChange={(e) => setForm((f) => ({ ...f, title: e.target.value }))}
            required
          />
        </div>
        <div>
          <Label>Tipo de servicio</Label>
          <Select
            onValueChange={(v) => setForm((f) => ({ ...f, service_type: (v as string) || "" }))}
          >
            <SelectTrigger>
              <SelectValue placeholder="Seleccionar servicio" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="social_media">Redes Sociales</SelectItem>
              <SelectItem value="ads">Publicidad</SelectItem>
              <SelectItem value="design">Diseño</SelectItem>
              <SelectItem value="video">Video</SelectItem>
              <SelectItem value="seo">SEO</SelectItem>
            </SelectContent>
          </Select>
        </div>
        <Button type="submit">Crear Proyecto</Button>
      </form>
    </div>
  );
}
