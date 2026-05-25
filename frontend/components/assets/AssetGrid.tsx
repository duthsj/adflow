"use client";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Trash2 } from "lucide-react";

interface Asset {
  id: number;
  filename: string;
  type: string;
  size: number;
  created_at: string;
}

interface AssetGridProps {
  assets: Asset[];
  onDelete: (id: number) => void;
}

function formatBytes(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

export default function AssetGrid({ assets, onDelete }: AssetGridProps) {
  if (assets.length === 0) {
    return (
      <div className="text-center py-16 text-gray-400">
        <p className="text-lg mb-2">Sin assets</p>
        <p className="text-sm">Sube imágenes, videos o documentos para comenzar</p>
      </div>
    );
  }

  return (
    <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
      {assets.map((asset) => (
        <div key={asset.id} className="bg-white border rounded-xl p-3 space-y-2 hover:shadow-sm transition-shadow">
          <div className="h-24 bg-gray-50 rounded-lg flex items-center justify-center text-gray-300 text-2xl">
            {asset.type === "image" ? "🖼" : asset.type === "video" ? "🎬" : "📄"}
          </div>
          <p className="text-xs text-gray-700 font-medium truncate">{asset.filename}</p>
          <div className="flex items-center justify-between">
            <Badge variant="outline" className="text-xs">{asset.type}</Badge>
            <span className="text-xs text-gray-400">{formatBytes(asset.size)}</span>
          </div>
          <Button
            variant="ghost"
            size="sm"
            className="w-full text-red-500 hover:text-red-600 hover:bg-red-50"
            onClick={() => onDelete(asset.id)}
          >
            <Trash2 size={14} className="mr-1" />
            Eliminar
          </Button>
        </div>
      ))}
    </div>
  );
}
