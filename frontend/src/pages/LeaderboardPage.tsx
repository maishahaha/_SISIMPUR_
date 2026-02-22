import { useEffect, useState } from "react";
import { getLeaderboard } from "@/services/api";
import { useToast } from "@/components/ui/ToastProvider";
import { cn } from "@/utils";
import type { LeaderboardEntry } from "@/types";

const PERIODS = [
  { value: "all", label: "All Time" },
  { value: "week", label: "This Week" },
  { value: "month", label: "This Month" },
];

const MEDAL = ["🥇", "🥈", "🥉"];

export default function LeaderboardPage() {
  const [entries, setEntries] = useState<LeaderboardEntry[]>([]);
  const [period, setPeriod] = useState<"all" | "week" | "month" | "year">("all");
  const [loading, setLoading] = useState(true);
  const { toast } = useToast();

  useEffect(() => {
    setLoading(true);
    getLeaderboard(period)
      .then((res) => setEntries(res.leaderboard ?? []))
      .catch(() => toast("Failed to load leaderboard", "error"))
      .finally(() => setLoading(false));
  }, [period]); // eslint-disable-line

  return (
    <div className="max-w-2xl mx-auto space-y-6 fade-in">
      <div>
        <h1 className="text-2xl font-bold text-white">Leaderboard</h1>
        <p className="text-white/40 text-sm mt-1">Top performers ranked by score</p>
      </div>

      {/* Period filter */}
      <div className="flex gap-2">
        {PERIODS.map((p) => (
          <button
            key={p.value}
            onClick={() => setPeriod(p.value as "all" | "week" | "month" | "year")}
            className={cn(
              "px-4 py-1.5 rounded-xl text-sm font-medium transition",
              period === p.value
                ? "bg-purple-600 text-white"
                : "text-white/40 hover:text-white hover:bg-white/[0.06]"
            )}
          >
            {p.label}
          </button>
        ))}
      </div>

      {/* Table */}
      <div className="glass border border-white/10 rounded-2xl overflow-hidden">
        {loading ? (
          <div className="flex items-center justify-center h-48">
            <i className="ri-loader-4-line animate-spin text-3xl text-white/30" />
          </div>
        ) : entries.length === 0 ? (
          <div className="text-center py-16 text-white/30 text-sm">No entries yet.</div>
        ) : (
          <table className="w-full">
            <thead>
              <tr className="border-b border-white/[0.06] text-xs text-white/40 uppercase tracking-wider">
                <th className="px-6 py-3 text-left">Rank</th>
                <th className="px-6 py-3 text-left">User</th>
                <th className="px-6 py-3 text-right">Score</th>
                <th className="px-6 py-3 text-right hidden sm:table-cell">Exams</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-white/[0.04]">
              {entries.map((entry, idx) => (
                <tr key={entry.username} className="hover:bg-white/[0.02] transition">
                  <td className="px-6 py-4 text-sm font-medium">
                    {idx < 3 ? (
                      <span className="text-lg">{MEDAL[idx]}</span>
                    ) : (
                      <span className="text-white/40">#{idx + 1}</span>
                    )}
                  </td>
                  <td className="px-6 py-4">
                    <div className="flex items-center gap-3">
                      <div className="w-8 h-8 rounded-full bg-gradient-to-br from-purple-500 to-blue-500 flex items-center justify-center text-xs font-bold text-white">
                        {entry.username[0]?.toUpperCase()}
                      </div>
                      <span className="text-sm text-white">{entry.username}</span>
                    </div>
                  </td>
                  <td className="px-6 py-4 text-right">
                    <span className="text-sm font-semibold text-purple-300">
                      {entry.total_score}
                    </span>
                  </td>
                  <td className="px-6 py-4 text-right text-xs text-white/40 hidden sm:table-cell">
                    {entry.total_exams ?? "—"}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
