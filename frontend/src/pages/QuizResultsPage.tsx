import { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { getQuizResults } from "@/services/api";
import { useToast } from "@/components/ui/ToastProvider";
import { cn } from "@/utils";
import type { QuizResultsResponse } from "@/types";

export default function QuizResultsPage() {
  const { jobId } = useParams<{ jobId: string }>();
  const navigate = useNavigate();
  const { toast } = useToast();
  const [data, setData] = useState<QuizResultsResponse | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!jobId) return;
    getQuizResults(Number(jobId))
      .then(setData)
      .catch(() => toast("Failed to load results", "error"))
      .finally(() => setLoading(false));
  }, [jobId]); // eslint-disable-line

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <i className="ri-loader-4-line animate-spin text-3xl text-white/30" />
      </div>
    );
  }

  if (!data) return null;

  const pairs = data.qa_pairs ?? [];

  return (
    <div className="max-w-3xl mx-auto space-y-6 fade-in">
      {/* Header */}
      <div className="flex items-center gap-3">
        <button
          onClick={() => navigate(-1)}
          className="w-8 h-8 rounded-lg flex items-center justify-center text-white/40 hover:text-white hover:bg-white/10 transition"
        >
          <i className="ri-arrow-left-line" />
        </button>
        <div>
          <h1 className="text-2xl font-bold text-white">Quiz Preview</h1>
          <p className="text-white/40 text-sm mt-0.5">{String(data.job_id ?? "Document")}</p>
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
        <StatCard icon="ri-question-line" label="Questions" value={pairs.length} />
        <StatCard icon="ri-file-text-line" label="Type" value={data.form_settings?.selected_question_type_display ?? data.form_settings?.selected_question_type ?? "Mixed"} />
        <StatCard icon="ri-translate-2" label="Language" value={data.form_settings?.selected_language_display ?? data.form_settings?.selected_language ?? "English"} />
      </div>

      {/* Q&A list */}
      <div className="space-y-4">
        {pairs.map((pair, idx) => (
          <div key={idx} className="glass border border-white/10 rounded-2xl p-5 space-y-3">
            <div className="flex gap-3">
              <span className="w-6 h-6 rounded-full bg-purple-600/30 text-purple-300 text-xs flex items-center justify-center flex-shrink-0">
                {idx + 1}
              </span>
              <p className="text-sm text-white leading-relaxed">{pair.question}</p>
            </div>

            {pair.options && Object.keys(pair.options).length > 0 && (
              <div className="ml-9 grid grid-cols-1 sm:grid-cols-2 gap-2">
                {Object.entries(pair.options).map(([key, val]) => (
                  <div
                    key={key}
                    className={cn(
                      "px-3 py-2 rounded-lg text-xs border transition",
                      pair.correct_option === key
                        ? "border-green-500/40 bg-green-500/10 text-green-300"
                        : "border-white/[0.06] text-white/50"
                    )}
                  >
                    <span className="font-semibold mr-1">{key}.</span>{val}
                  </div>
                ))}
              </div>
            )}

            <div className="ml-9 pt-2 border-t border-white/[0.06]">
              <p className="text-xs text-white/40">Answer</p>
              <p className="text-sm text-green-300 mt-0.5">{pair.answer}</p>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

function StatCard({ icon, label, value }: { icon: string; label: string; value: string | number }) {
  return (
    <div className="glass border border-white/10 rounded-xl p-4 flex items-center gap-3">
      <i className={cn(icon, "text-purple-400 text-xl")} />
      <div>
        <p className="text-xs text-white/40">{label}</p>
        <p className="text-sm font-medium text-white capitalize">{String(value)}</p>
      </div>
    </div>
  );
}
