"use client";
import { useEffect, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Copy, Check } from "lucide-react";
import api from "@/lib/api";
import { toast } from "sonner";

interface Member {
  id: number;
  user_id: number;
  role: string;
  created_at: string;
}

interface InviteResult {
  invite_token: string;
  expires_at: string;
}

const ROLE_COLORS: Record<string, string> = {
  owner: "bg-orange-100 text-orange-700",
  editor: "bg-blue-100 text-blue-700",
  viewer: "bg-gray-100 text-gray-700",
};

export default function MembersPage() {
  const [members, setMembers] = useState<Member[]>([]);
  const [invite, setInvite] = useState<InviteResult | null>(null);
  const [copied, setCopied] = useState(false);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    api.get("/workspaces/me/members").then((r) => setMembers(r.data)).catch(() => {});
  }, []);

  const createInvite = async () => {
    setLoading(true);
    try {
      const r = await api.post("/workspaces/me/invite");
      setInvite(r.data);
    } catch {
      toast.error("Error generando invitación");
    } finally {
      setLoading(false);
    }
  };

  const copyLink = () => {
    if (!invite) return;
    const url = `${window.location.origin}/join/${invite.invite_token}`;
    navigator.clipboard.writeText(url);
    setCopied(true);
    toast.success("Link copiado");
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900">Equipo</h1>
        <Button onClick={createInvite} disabled={loading}>
          {loading ? "Generando..." : "Invitar miembro"}
        </Button>
      </div>

      {invite && (
        <Card className="border-orange-200 bg-orange-50">
          <CardContent className="pt-4">
            <p className="text-sm font-medium text-orange-800 mb-2">Link de invitación (expira en 48h):</p>
            <div className="flex items-center gap-2">
              <code className="flex-1 text-xs bg-white border rounded p-2 text-gray-700 truncate">
                {`${window.location.origin}/join/${invite.invite_token}`}
              </code>
              <Button size="sm" variant="outline" onClick={copyLink}>
                {copied ? <Check size={14} /> : <Copy size={14} />}
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      <Card>
        <CardHeader>
          <CardTitle className="text-base">Miembros ({members.length})</CardTitle>
        </CardHeader>
        <CardContent>
          {members.length === 0 ? (
            <p className="text-sm text-gray-400 text-center py-6">Sin miembros todavía</p>
          ) : (
            <div className="divide-y">
              {members.map((m) => (
                <div key={m.id} className="flex items-center justify-between py-3">
                  <div>
                    <p className="text-sm font-medium text-gray-800">Usuario #{m.user_id}</p>
                    <p className="text-xs text-gray-400">
                      Desde {new Date(m.created_at).toLocaleDateString("es")}
                    </p>
                  </div>
                  <Badge className={ROLE_COLORS[m.role] ?? "bg-gray-100"}>{m.role}</Badge>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
