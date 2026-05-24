"use client";
import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import ContentApproval from "@/components/portal/ContentApproval";
import axios from "axios";

interface ContentItem {
  id: number;
  type: string;
  body: string;
  status: string;
  created_at: string;
}

interface PortalData {
  client_name: string;
  project_title: string | null;
  content_items: ContentItem[];
}

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export default function PortalPage() {
  const { token } = useParams<{ token: string }>();
  const [data, setData] = useState<PortalData | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    axios
      .get(`${API_URL}/portal/${token}`)
      .then((r) => setData(r.data))
      .catch((e) => {
        if (e.response?.status === 404) setError("Este enlace no existe o ha expirado.");
        else if (e.response?.status === 410) setError("Este enlace ha expirado.");
        else setError("Error al cargar el portal.");
      });
  }, [token]);

  const handleStatusChange = (id: number, status: "approved" | "rejected") => {
    setData((prev) =>
      prev
        ? {
            ...prev,
            content_items: prev.content_items.map((item) =>
              item.id === id ? { ...item, status } : item
            ),
          }
        : prev
    );
  };

  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center">
          <p className="text-gray-500 text-lg">{error}</p>
          <p className="text-gray-400 text-sm mt-2">Contacta a tu agencia para obtener un nuevo enlace.</p>
        </div>
      </div>
    );
  }

  if (!data) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <p className="text-gray-400">Cargando...</p>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white border-b px-6 py-4">
        <div className="max-w-3xl mx-auto">
          <h1 className="text-xl font-bold text-orange-500">MuelaADS</h1>
          <p className="text-sm text-gray-500 mt-1">
            Portal de aprobaciones — {data.client_name}
            {data.project_title && <span className="ml-2">· {data.project_title}</span>}
          </p>
        </div>
      </header>
      <main className="max-w-3xl mx-auto px-6 py-8 space-y-4">
        <div className="flex justify-between items-center">
          <h2 className="font-semibold text-gray-900">
            Contenido para revisar ({data.content_items.length})
          </h2>
          <p className="text-sm text-gray-400">
            {data.content_items.filter((i) => i.status === "approved").length} aprobados
          </p>
        </div>
        {data.content_items.length === 0 ? (
          <p className="text-gray-400 text-center py-12">No hay contenido pendiente de revisión.</p>
        ) : (
          data.content_items.map((item) => (
            <ContentApproval
              key={item.id}
              item={item}
              token={token}
              onStatusChange={handleStatusChange}
            />
          ))
        )}
      </main>
    </div>
  );
}
