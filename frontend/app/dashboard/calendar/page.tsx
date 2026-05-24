"use client";
import { useEffect, useState } from "react";
import api from "@/lib/api";
import { format, startOfMonth, endOfMonth, eachDayOfInterval, isSameDay } from "date-fns";
import { es } from "date-fns/locale";

interface ScheduledPost {
  id: number;
  platform: string;
  scheduled_at: string;
  status: string;
}

const PLATFORM_COLORS: Record<string, string> = {
  instagram: "bg-pink-100 text-pink-700",
  facebook: "bg-blue-100 text-blue-700",
  tiktok: "bg-black text-white",
  linkedin: "bg-sky-100 text-sky-700",
  twitter: "bg-sky-50 text-sky-600",
};

export default function CalendarPage() {
  const [posts, setPosts] = useState<ScheduledPost[]>([]);
  const [currentMonth, setCurrentMonth] = useState(new Date());

  useEffect(() => {
    api.get("/content").catch(() => {});
    setPosts([]);
  }, []);

  const days = eachDayOfInterval({
    start: startOfMonth(currentMonth),
    end: endOfMonth(currentMonth),
  });

  const postsOnDay = (day: Date) =>
    posts.filter((p) => isSameDay(new Date(p.scheduled_at), day));

  const prevMonth = () =>
    setCurrentMonth((d) => new Date(d.getFullYear(), d.getMonth() - 1, 1));
  const nextMonth = () =>
    setCurrentMonth((d) => new Date(d.getFullYear(), d.getMonth() + 1, 1));

  return (
    <div>
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold">Calendario de Contenido</h1>
        <div className="flex items-center gap-3">
          <button onClick={prevMonth} className="p-2 hover:bg-gray-100 rounded">←</button>
          <span className="font-medium capitalize">
            {format(currentMonth, "MMMM yyyy", { locale: es })}
          </span>
          <button onClick={nextMonth} className="p-2 hover:bg-gray-100 rounded">→</button>
        </div>
      </div>

      <div className="grid grid-cols-7 gap-px bg-gray-200 border border-gray-200 rounded-lg overflow-hidden">
        {["Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom"].map((d) => (
          <div key={d} className="bg-gray-50 text-center text-xs font-medium text-gray-500 py-2">
            {d}
          </div>
        ))}
        {days.map((day) => {
          const dayPosts = postsOnDay(day);
          return (
            <div
              key={day.toISOString()}
              className="bg-white min-h-[80px] p-2"
            >
              <p className="text-xs text-gray-500 mb-1">{format(day, "d")}</p>
              {dayPosts.map((p) => (
                <div
                  key={p.id}
                  className={`text-xs rounded px-1 py-0.5 mb-0.5 truncate ${
                    PLATFORM_COLORS[p.platform] || "bg-gray-100 text-gray-600"
                  }`}
                >
                  {p.platform}
                </div>
              ))}
            </div>
          );
        })}
      </div>

      <p className="text-xs text-gray-400 mt-4 text-center">
        El calendario mostrará posts programados via Blotato una vez configuradas las integraciones.
      </p>
    </div>
  );
}
