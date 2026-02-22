import { useNavigate } from "react-router-dom";
import { useAuth } from "@/contexts/AuthContext";
import { useToast } from "@/components/ui/ToastProvider";
import { cn } from "@/utils";
import { useState } from "react";

interface NavbarProps {
  onMenuToggle: () => void;
}

export default function Navbar({ onMenuToggle }: NavbarProps) {
  const { user, signOut } = useAuth();
  const { toast } = useToast();
  const navigate = useNavigate();
  const [profileOpen, setProfileOpen] = useState(false);

  async function handleLogout() {
    try {
      await signOut();
      navigate("/signin");
    } catch {
      toast("Logout failed", "error");
    }
  }

  return (
    <header className="h-16 flex items-center justify-between px-4 md:px-6 border-b border-white/[0.06] glass sticky top-0 z-20">
      {/* Left */}
      <div className="flex items-center gap-3">
        {/* Mobile logo */}
        <div className="flex items-center gap-2 md:hidden">
          <span className="material-icons text-purple-400 text-xl">school</span>
          <span className="gradient-text font-bold text-base tracking-widest select-none">SISIMPUR</span>
        </div>
        <button
          onClick={onMenuToggle}
          className="md:hidden w-9 h-9 rounded-lg flex items-center justify-center text-white/60 hover:text-white hover:bg-white/10 transition"
        >
          <span className="material-icons text-xl">menu</span>
        </button>

        {/* Desktop search */}
        <div className="relative hidden md:flex items-center">
          <span className="material-icons absolute left-3 text-white/30 text-base">search</span>
          <input
            type="text"
            placeholder="Search topics, quizzes…"
            className={cn(
              "bg-white/[0.05] border border-white/[0.08] rounded-xl pl-9 pr-16 py-2",
              "text-sm text-white/80 placeholder:text-white/30 outline-none",
              "focus:border-purple-500/50 focus:bg-white/[0.08] transition w-64"
            )}
          />
          <span className="absolute right-3 text-xs text-white/30 pointer-events-none select-none">⌘K</span>
        </div>
      </div>

      {/* Right */}
      <div className="flex items-center gap-2">
        {/* Notifications */}
        <button className="w-9 h-9 rounded-lg flex items-center justify-center text-white/50 hover:text-white hover:bg-white/10 transition relative">
          <span className="material-icons text-xl">notifications</span>
        </button>

        {/* Profile dropdown */}
        <div className="relative">
          <button
            onClick={() => setProfileOpen((p) => !p)}
            className="flex items-center gap-2 px-2 py-1.5 rounded-xl hover:bg-white/[0.06] transition"
          >
            <div className="w-8 h-8 rounded-full overflow-hidden bg-gradient-to-br from-purple-500 to-blue-500 flex items-center justify-center text-white font-semibold text-sm">
              {user?.username?.[0]?.toUpperCase() ?? "U"}
            </div>
            <div className="hidden sm:block text-left">
              <p className="text-sm font-medium text-white leading-tight">{user?.username ?? "User"}</p>
              <p className="text-xs text-white/40 leading-tight">Student</p>
            </div>
            <span className="material-icons text-white/40 text-base hidden sm:block">expand_more</span>
          </button>

          {profileOpen && (
            <div className="absolute right-0 top-12 w-52 glass border border-white/10 rounded-xl overflow-hidden shadow-2xl">
              <div className="px-4 py-3 border-b border-white/[0.06]">
                <p className="text-sm font-medium text-white truncate">
                  {user?.username ?? "User"}
                </p>
                <p className="text-xs text-white/40 truncate">{user?.email ?? ""}</p>
              </div>
              <div className="p-2 space-y-1">
                <button
                  onClick={handleLogout}
                  className="w-full flex items-center gap-2.5 px-3 py-2 rounded-lg text-sm text-red-400
                    hover:bg-red-500/10 transition"
                >
                  <span className="material-icons text-base">logout</span>
                  Sign Out
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </header>
  );
}
