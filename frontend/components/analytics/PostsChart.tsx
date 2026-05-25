"use client";
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts";

interface PostsChartProps {
  data: { date: string; posts: number }[];
}

export default function PostsChart({ data }: PostsChartProps) {
  if (data.length === 0) {
    return (
      <div className="flex items-center justify-center h-48 text-gray-400 text-sm">
        Sin datos para mostrar
      </div>
    );
  }
  return (
    <ResponsiveContainer width="100%" height={200}>
      <LineChart data={data}>
        <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
        <XAxis dataKey="date" tick={{ fontSize: 12 }} />
        <YAxis tick={{ fontSize: 12 }} />
        <Tooltip />
        <Line type="monotone" dataKey="posts" stroke="#ea580c" strokeWidth={2} dot={false} />
      </LineChart>
    </ResponsiveContainer>
  );
}
