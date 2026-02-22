import { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { getExamResult } from "@/services/api";
import { useToast } from "@/components/ui/ToastProvider";
import { cn } from "@/utils";
import type { ExamResultResponse } from "@/types";

export default function ExamResultPage() {
  const { sessionId } = useParams<{ sessionId: string }>();
  const navigate = useNavigate();
  const { toast } = useToast();
  const [result, setResult] = useState<ExamResultResponse | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!sessionId) return;
    getExamResult(sessionId)
      .then(setResult)
      .catch(() => toast("Failed to load result", "error"))
      .finally(() => setLoading(false));
  }, [sessionId]); // eslint-disable-line

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <i className="ri-loader-4-line animate-spin text-3xl text-white/30" />
      </div>
    );
  }

  if (!result) return null;

  const pct = result.total_questions
    ? Math.round((result.correct_answers / result.total_questions) * 100)
    : 0;

  const grade =
    pct >= 90 ? { label: "Excellent!", color: "text-green-400" } :
    pct >= 70 ? { label: "Good Job!", color: "text-blue-400" } :
    pct >= 50 ? { label: "Keep Practicing", color: "text-yellow-400" } :
    { label: "Needs Improvement", color: "text-red-400" };

  return (
    <div className="max-w-2xl mx-auto space-y-6 fade-in">
      {/* Score card */}
      <div className="glass border border-white/10 rounded-2xl p-8 text-center space-y-4">
        <div className={cn("text-6xl font-bold gradient-text")}>{pct}%</div>
        <p className={cn("text-lg font-semibold", grade.color)}>{grade.label}</p>
        <div className="flex items-center justify-center gap-8 pt-2">
          <div>
            <p className="text-2xl font-bold text-green-400">{result.correct_answers}</p>
            <p className="text-xs text-white/40 mt-0.5">Correct</p>
          </div>
          <div className="w-px h-10 bg-white/10" />
          <div>
            <p className="text-2xl font-bold text-red-400">
              {result.total_questions - result.correct_answers}
            </p>
            <p className="text-xs text-white/40 mt-0.5">Wrong</p>
          </div>
          <div className="w-px h-10 bg-white/10" />
          <div>
            <p className="text-2xl font-bold text-white">{result.total_questions}</p>
            <p className="text-xs text-white/40 mt-0.5">Total</p>
          </div>
        </div>
      </div>

      {/* Answer review */}
      {result.answers && result.answers.length > 0 && (
        <div className="space-y-3">
          <h2 className="text-sm font-semibold text-white/60 uppercase tracking-wider px-1">Review</h2>
          {result.answers.map((ans, idx) => (
            <div key={idx} className={cn(
              "glass border rounded-2xl p-4 space-y-2",
              ans.is_correct ? "border-green-500/20" : "border-red-500/20"
            )}>
              <div className="flex items-start gap-2">
                <i className={cn(
                  "text-sm mt-0.5",
                  ans.is_correct ? "ri-check-line text-green-400" : "ri-close-line text-red-400"
                )} />
                <p className="text-sm text-white leading-relaxed">{ans.question}</p>
              </div>
              <div className="pl-5 grid grid-cols-2 gap-x-4 gap-y-1 text-xs">
                <div>
                  <span className="text-white/30">Your answer: </span>
                  <span className={ans.is_correct ? "text-green-400" : "text-red-400"}>
                    {ans.user_answer ?? "—"}
                  </span>
                </div>
                {!ans.is_correct && (
                  <div>
                    <span className="text-white/30">Correct: </span>
                    <span className="text-green-400">{ans.correct_answer}</span>
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Actions */}
      <div className="flex gap-3">
        <button
          onClick={() => navigate("/give-exam")}
          className="flex-1 py-2.5 rounded-xl text-sm font-semibold text-white bg-purple-600 hover:bg-purple-500 transition"
        >
          <i className="ri-refresh-line mr-1.5" />Try Again
        </button>
        <button
          onClick={() => navigate("/my-quizzes")}
          className="flex-1 py-2.5 rounded-xl text-sm font-medium text-white/60 hover:text-white glass border border-white/10 hover:border-white/20 transition"
        >
          <i className="ri-book-2-line mr-1.5" />My Quizzes
        </button>
      </div>
    </div>
  );
}
