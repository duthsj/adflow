"use client";
import { useEffect, useState } from "react";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import api from "@/lib/api";
import { Client } from "@/types";

export default function ClientsPage() {
  const [clients, setClients] = useState<Client[]>([]);

  useEffect(() => {
    api.get("/clients").then((r) => setClients(r.data));
  }, []);

  return (
    <div>
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold">Clientes</h1>
        <Link href="/dashboard/clients/new">
          <Button>+ Nuevo Cliente</Button>
        </Link>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {clients.map((c) => (
          <Link key={c.id} href={`/dashboard/clients/${c.id}`}>
            <div className="bg-white border rounded-lg p-4 hover:shadow-md transition-shadow cursor-pointer">
              <div className="flex justify-between items-start">
                <h3 className="font-semibold text-gray-900">{c.name}</h3>
                <Badge variant={c.active ? "default" : "secondary"}>
                  {c.active ? "Activo" : "Inactivo"}
                </Badge>
              </div>
              <p className="text-sm text-gray-500 mt-1">{c.industry}</p>
              {c.brand_guidelines.tone && (
                <p className="text-xs text-gray-400 mt-2">
                  Tono: {c.brand_guidelines.tone}
                </p>
              )}
            </div>
          </Link>
        ))}
        {clients.length === 0 && (
          <p className="text-gray-400 col-span-3 text-center py-12">
            No hay clientes aún. Crea el primero.
          </p>
        )}
      </div>
    </div>
  );
}
