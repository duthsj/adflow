"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";
import { LayoutDashboard, Users, FolderKanban, Calendar, LogOut } from "lucide-react";
import { removeToken } from "@/lib/auth";
import { useRouter } from "next/navigation";

const nav = [
  { href: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { href: "/dashboard/clients", label: "Clientes", icon: Users },
  { href: "/dashboard/projects", label: "Proyectos", icon: FolderKanban },
  { href: "/dashboard/calendar", label: "Calendario", icon: Calendar },
];

export default function Sidebar() {
  const pathname = usePathname();
  const router = useRouter();

  const logout = () => {
    removeToken();
    router.push("/login");
  };

  return (
    <aside className="w-64 bg-gray-900 text-white min-h-screen flex flex-col">
      <div className="p-6 border-b border-gray-700">
        <h1 className="text-xl font-bold text-orange-400">MuelaADS</h1>
        <p className="text-xs text-gray-400 mt-1">Marketing Agency</p>
      </div>
      <nav className="flex-1 p-4 space-y-1">
        {nav.map(({ href, label, icon: Icon }) => (
          <Link
            key={href}
            href={href}
            className={cn(
              "flex items-center gap-3 px-3 py-2 rounded-lg text-sm transition-colors",
              pathname === href
                ? "bg-orange-500 text-white"
                : "text-gray-300 hover:bg-gray-800"
            )}
          >
            <Icon size={18} />
            {label}
          </Link>
        ))}
      </nav>
      <div className="p-4 border-t border-gray-700">
        <button
          onClick={logout}
          className="flex items-center gap-3 px-3 py-2 text-sm text-gray-300 hover:text-white w-full"
        >
          <LogOut size={18} />
          Salir
        </button>
      </div>
    </aside>
  );
}
