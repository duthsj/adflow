"use client";
import { useEffect, useState } from "react";
import AssetGrid from "@/components/assets/AssetGrid";
import UploadButton from "@/components/assets/UploadButton";
import api from "@/lib/api";
import { toast } from "sonner";

interface Client { id: number; name: string; }
interface Asset { id: number; filename: string; type: string; size: number; r2_key: string; created_at: string; }

const TYPE_MAP: Record<string, string> = {
  "image/jpeg": "image",
  "image/png": "image",
  "image/gif": "image",
  "image/webp": "image",
  "video/mp4": "video",
  "video/quicktime": "video",
  "application/pdf": "doc",
  "application/msword": "doc",
};

export default function AssetsPage() {
  const [clients, setClients] = useState<Client[]>([]);
  const [selectedClient, setSelectedClient] = useState<number | null>(null);
  const [assets, setAssets] = useState<Asset[]>([]);
  const [uploading, setUploading] = useState(false);
  const [typeFilter, setTypeFilter] = useState("");

  useEffect(() => {
    api.get("/clients").then((r) => {
      setClients(r.data);
      if (r.data.length > 0) setSelectedClient(r.data[0].id);
    });
  }, []);

  useEffect(() => {
    if (!selectedClient) return;
    const params = new URLSearchParams({ client_id: String(selectedClient) });
    if (typeFilter) params.set("asset_type", typeFilter);
    api.get(`/assets?${params}`).then((r) => setAssets(r.data));
  }, [selectedClient, typeFilter]);

  const handleUpload = async (file: File) => {
    if (!selectedClient) return;
    setUploading(true);
    const assetType = TYPE_MAP[file.type] ?? "doc";
    const form = new FormData();
    form.append("file", file);
    form.append("client_id", String(selectedClient));
    form.append("asset_type", assetType);
    try {
      const r = await api.post("/assets/upload", form, {
        headers: { "Content-Type": "multipart/form-data" },
      });
      setAssets((prev) => [r.data, ...prev]);
      toast.success(`${file.name} subido correctamente`);
    } catch {
      toast.error("Error subiendo archivo");
    } finally {
      setUploading(false);
    }
  };

  const handleDelete = async (id: number) => {
    try {
      await api.delete(`/assets/${id}`);
      setAssets((prev) => prev.filter((a) => a.id !== id));
      toast.success("Asset eliminado");
    } catch {
      toast.error("Error eliminando asset");
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900">Media Library</h1>
        <div className="flex gap-2">
          <select
            className="border rounded-lg px-3 py-2 text-sm bg-white"
            value={selectedClient ?? ""}
            onChange={(e) => setSelectedClient(Number(e.target.value))}
          >
            {clients.map((c) => <option key={c.id} value={c.id}>{c.name}</option>)}
          </select>
          <select
            className="border rounded-lg px-3 py-2 text-sm bg-white"
            value={typeFilter}
            onChange={(e) => setTypeFilter(e.target.value)}
          >
            <option value="">Todos los tipos</option>
            <option value="image">Imágenes</option>
            <option value="video">Videos</option>
            <option value="doc">Documentos</option>
          </select>
          {selectedClient && (
            <UploadButton
              uploading={uploading}
              onUpload={handleUpload}
            />
          )}
        </div>
      </div>
      <AssetGrid assets={assets} onDelete={handleDelete} />
    </div>
  );
}
