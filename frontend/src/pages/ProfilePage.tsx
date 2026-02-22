import { useAuth } from "@/contexts/AuthContext";
import { cn } from "@/utils";

export default function ProfilePage() {
  const { user } = useAuth();

  return (
    <div className="max-w-2xl mx-auto space-y-6 fade-in">
      <div>
        <h1 className="text-2xl font-bold text-white">Profile</h1>
        <p className="text-white/40 text-sm mt-1">Your account information</p>
      </div>

      {/* Avatar section */}
      <div className="glass border border-white/10 rounded-2xl p-8 flex flex-col sm:flex-row items-center gap-6">
        <div className={cn(
          "w-20 h-20 rounded-full bg-gradient-to-br from-purple-500 to-blue-500",
          "flex items-center justify-center text-3xl font-bold text-white flex-shrink-0"
        )}>
          {user?.username?.[0]?.toUpperCase() ?? "U"}
        </div>
        <div className="text-center sm:text-left">
          <h2 className="text-xl font-semibold text-white">{user?.username ?? "—"}</h2>
          <p className="text-white/40 text-sm">{user?.email ?? "—"}</p>
        </div>
      </div>

      {/* Details */}
      <div className="glass border border-white/10 rounded-2xl p-6 space-y-4">
        <h3 className="text-sm font-semibold text-white/60 uppercase tracking-wider">Account Details</h3>
        <div className="space-y-3">
          {[
            { icon: "ri-user-line", label: "Username", value: user?.username },
            { icon: "ri-mail-line", label: "Email", value: user?.email },
            { icon: "ri-id-card-line", label: "User ID", value: user?.id ? String(user.id) : undefined },
          ].map((item) => (
            <div key={item.label} className="flex items-center gap-4 py-3 border-b border-white/[0.04] last:border-0">
              <i className={cn(item.icon, "text-white/30 text-lg w-5")} />
              <div className="flex-1">
                <p className="text-xs text-white/40">{item.label}</p>
                <p className="text-sm text-white mt-0.5">{item.value ?? "—"}</p>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
