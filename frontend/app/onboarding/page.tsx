"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import api from "@/lib/api";
import { toast } from "sonner";

export default function OnboardingPage() {
  const [name, setName] = useState("");
  const [loading, setLoading] = useState(false);
  const router = useRouter();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim()) return;
    setLoading(true);
    try {
      await api.put("/workspaces/me", { name: name.trim() });
      toast.success("Workspace configurado");
      router.push("/dashboard");
    } catch {
      toast.error("Error configurando workspace");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center p-4">
      <Card className="w-full max-w-md">
        <CardHeader className="text-center">
          <h1 className="text-2xl font-bold text-orange-500">MuelaADS</h1>
          <CardTitle className="text-lg mt-2">¡Bienvenido! Configura tu agencia</CardTitle>
          <p className="text-sm text-gray-500">Dale un nombre a tu workspace para comenzar</p>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="name">Nombre de tu agencia</Label>
              <Input
                id="name"
                placeholder="Ej: Agencia Creativa XYZ"
                value={name}
                onChange={(e) => setName(e.target.value)}
                autoFocus
              />
            </div>
            <Button
              type="submit"
              className="w-full bg-orange-500 hover:bg-orange-600 text-white"
              disabled={loading || !name.trim()}
            >
              {loading ? "Configurando..." : "Comenzar →"}
            </Button>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}
