"use client";
import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import axios from "axios";

interface ContentItem {
  id: number;
  type: string;
  body: string;
  status: string;
  created_at: string;
}

interface Props {
  item: ContentItem;
  token: string;
  onStatusChange: (id: number, status: "approved" | "rejected") => void;
}

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export default function ContentApproval({ item, token, onStatusChange }: Props) {
  const [loading, setLoading] = useState<"approve" | "reject" | null>(null);
  const [comment, setComment] = useState("");

  const approve = async () => {
    setLoading("approve");
    try {
      await axios.post(`${API_URL}/portal/${token}/approve`, { content_id: item.id });
      onStatusChange(item.id, "approved");
    } finally {
      setLoading(null);
    }
  };

  const reject = async () => {
    setLoading("reject");
    try {
      await axios.post(`${API_URL}/portal/${token}/reject`, {
        content_id: item.id,
        comment: comment || undefined,
      });
      onStatusChange(item.id, "rejected");
    } finally {
      setLoading(null);
    }
  };

  return (
    <div className="bg-white border rounded-lg p-5 space-y-3">
      <div className="flex items-center justify-between">
        <Badge variant="outline" className="capitalize">{item.type}</Badge>
        <Badge variant={item.status === "approved" ? "default" : "secondary"}>
          {item.status === "approved" ? "Aprobado ✓" : "Pendiente revisión"}
        </Badge>
      </div>
      <p className="text-gray-800 text-sm whitespace-pre-wrap">{item.body}</p>
      {item.status !== "approved" && (
        <div className="space-y-2 pt-2 border-t">
          <input
            type="text"
            placeholder="Comentario para rechazo (opcional)"
            value={comment}
            onChange={(e) => setComment(e.target.value)}
            className="w-full text-sm border rounded px-3 py-1.5 text-gray-700"
          />
          <div className="flex gap-2">
            <Button
              size="sm"
              onClick={approve}
              disabled={loading !== null}
              className="bg-green-600 hover:bg-green-700 text-white"
            >
              {loading === "approve" ? "..." : "✓ Aprobar"}
            </Button>
            <Button
              size="sm"
              variant="outline"
              onClick={reject}
              disabled={loading !== null}
              className="border-red-300 text-red-600 hover:bg-red-50"
            >
              {loading === "reject" ? "..." : "✗ Rechazar"}
            </Button>
          </div>
        </div>
      )}
    </div>
  );
}
