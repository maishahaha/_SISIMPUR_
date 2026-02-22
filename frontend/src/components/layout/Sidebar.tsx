import { Link, useLocation, useNavigate } from "react-router-dom";
import { cn } from "@/utils";
import { useAuth } from "@/contexts/AuthContext";
import { useToast } from "@/components/ui/ToastProvider";

const NAV_ITEMS = [
  { href: "/dashboard", label: "New Quiz", icon: "add_circle" },
  { href: "/give-exam", label: "Give Exam", icon: "edit_document" },
  { href: "/my-quizzes", label: "My Quizzes", icon: "inventory_2" },
  { href: "/leaderboard", label: "Leaderboard", icon: "leaderboard" },
  { href: "/analytics", label: "Analytics", icon: "bar_chart" },
];

interface SidebarProps {
  collapsed: boolean;
  onToggle: () => void;
}

export default function Sidebar({ collapsed, onToggle }: SidebarProps) {
  const { pathname } = useLocation();
  const { signOut } = useAuth();
  const { toast } = useToast();
  const navigate = useNavigate();

  async function handleLogout() {
    try {
      await signOut();
      navigate("/signin");
    } catch {
      toast("Logout failed", "error");
    }
  }

  return (
    <aside
      className={cn(
        "fixed top-0 left-0 h-full z-30 flex flex-col transition-all duration-300 ease-in-out",
        "glass border-r border-white/[0.06]",
        collapsed ? "w-16" : "w-60"
      )}
    >
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-5 border-b border-white/[0.06]">
        <div className="flex items-center gap-2">
          <span className="material-icons text-purple-400 text-2xl">school</span>
          {!collapsed && (
            <span className="gradient-text font-bold text-lg tracking-widest select-none">
              SISIMPUR
            </span>
          )}
        </div>
        <button
          onClick={onToggle}
          className={cn(
            "w-8 h-8 rounded-lg flex items-center justify-center",
            "text-white/50 hover:text-white hover:bg-white/10 transition",
            collapsed && "mx-auto"
          )}
        >
          <i className={cn(collapsed ? "ri-arrow-right-s-line" : "ri-arrow-left-s-line", "text-lg")} />
        </button>
      </div>

      {/* Nav */}
      <nav className="flex-1 px-2 py-4 space-y-1">
        {NAV_ITEMS.map((item) => {
          const isActive = item.href === "/dashboard" ? pathname === "/dashboard" : pathname.startsWith(item.href);
          return (
            <Link
              key={item.href}
              to={item.href}
              className={cn(
                "flex items-center gap-3 px-3 py-2.5 rounded-xl transition-all duration-200 group",
                isActive
                  ? "bg-purple-600/25 text-purple-300 border border-purple-500/30"
                  : "text-white/50 hover:text-white/80 hover:bg-white/[0.06]"
              )}
            >
              <span className="material-icons text-xl shrink-0">{item.icon}</span>
              {!collapsed && (
                <span className="text-sm font-medium truncate">{item.label}</span>
              )}
            </Link>
          );
        })}
      </nav>

      {/* Upgrade card */}
      {!collapsed && (
        <div className="mx-3 mb-3 rounded-xl bg-gradient-to-br from-purple-700/30 to-blue-700/30 border border-purple-500/30 p-4 space-y-2">
          <div className="flex items-center gap-1.5">
            <span className="material-icons text-yellow-400 text-base">workspace_premium</span>
            <span className="text-xs font-bold text-yellow-400 tracking-wider">PRO</span>
          </div>
          <h4 className="text-sm font-semibold text-white">Upgrade Plan</h4>
          <p className="text-xs text-white/50">Get unlimited AI quizzes and detailed analytics.</p>
          <button className="w-full py-1.5 rounded-lg text-xs font-semibold bg-gradient-to-r from-purple-600 to-blue-600 text-white hover:opacity-90 transition">
            Upgrade Now
          </button>
        </div>
      )}

      {/* Log Out */}
      <div className="px-2 py-3 border-t border-white/[0.06]">
        <button
          onClick={handleLogout}
          className={cn(
            "w-full flex items-center gap-3 px-3 py-2.5 rounded-xl transition",
            "text-white/50 hover:text-red-400 hover:bg-red-500/10"
          )}
        >
          <span className="material-icons text-xl shrink-0">logout</span>
          {!collapsed && <span className="text-sm font-medium">Log Out</span>}
        </button>
      </div>
    </aside>
  );
}
