"use client";
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts";

interface PlatformStat {
  platform: string;
  posts: number;
  reach: number;
  engagement: number;
}

export default function PlatformChart({ data }: { data: PlatformStat[] }) {
  if (data.length === 0) {
    return (
      <div className="flex items-center justify-center h-48 text-gray-400 text-sm">
        Sin datos de plataformas
      </div>
    );
  }
  return (
    <ResponsiveContainer width="100%" height={200}>
      <BarChart data={data}>
        <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
        <XAxis dataKey="platform" tick={{ fontSize: 12 }} />
        <YAxis tick={{ fontSize: 12 }} />
        <Tooltip />
        <Bar dataKey="posts" fill="#ea580c" radius={[4, 4, 0, 0]} />
      </BarChart>
    </ResponsiveContainer>
  );
}
