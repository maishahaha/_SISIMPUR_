import { useEffect, useState, useCallback } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { getExamSession, answerQuestion, submitExam } from "@/services/api";
import { useToast } from "@/components/ui/ToastProvider";
import { cn } from "@/utils";
import type { ExamSessionResponse } from "@/types";

export default function ExamPage() {
  const { sessionId } = useParams<{ sessionId: string }>();
  const navigate = useNavigate();
  const { toast } = useToast();

  const [session, setSession] = useState<ExamSessionResponse | null>(null);
  const [selected, setSelected] = useState<string>("");
  const [textAnswer, setTextAnswer] = useState("");
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [elapsed, setElapsed] = useState(0);

  const refresh = useCallback(async () => {
    if (!sessionId) return;
    try {
      const res = await getExamSession(sessionId);
      setSession(res);
      setSelected("");
      setTextAnswer("");
    } catch {
      toast("Session error", "error");
    }
  }, [sessionId]); // eslint-disable-line

  useEffect(() => {
    setLoading(true);
    refresh().finally(() => setLoading(false));
  }, [refresh]);

  // Timer
  useEffect(() => {
    const t = setInterval(() => setElapsed((e) => e + 1), 1000);
    return () => clearInterval(t);
  }, []);

  const question = session?.question;
  const progress = session
    ? ((session.current_index ?? 0) / (session.total_questions ?? 1)) * 100
    : 0;

  async function handleAnswer() {
    if (!question || !sessionId) return;
    const ans = question.question_type === "MULTIPLECHOICE"
      ? selected
      : textAnswer;
    if (!ans) return toast("Select or type an answer", "error");
    setSubmitting(true);
    try {
      const isLast = session?.is_last_question;
      await answerQuestion(sessionId, ans, isLast ? "submit" : "next");
      if (isLast) {
        navigate(`/exam/result/${sessionId}`);
      } else {
        await refresh();
      }
    } catch {
      toast("Failed to submit answer", "error");
    } finally {
      setSubmitting(false);
    }
  }

  async function handleSubmit() {
    if (!sessionId) return;
    if (!confirm("Submit and end the exam?")) return;
    setSubmitting(true);
    try {
      await submitExam(sessionId);
      navigate(`/exam/result/${sessionId}`);
    } catch {
      toast("Submit failed", "error");
      setSubmitting(false);
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <i className="ri-loader-4-line animate-spin text-3xl text-white/30" />
      </div>
    );
  }

  if (session?.session_status === "completed") {
    navigate(`/exam/result/${sessionId}`);
    return null;
  }

  const mins = String(Math.floor(elapsed / 60)).padStart(2, "0");
  const secs = String(elapsed % 60).padStart(2, "0");

  return (
    <div className="max-w-2xl mx-auto space-y-6 fade-in">
      {/* Progress bar */}
      <div className="space-y-2">
        <div className="flex items-center justify-between text-xs text-white/40">
          <span>Question {(session?.current_index ?? 0) + 1} of {session?.total_questions}</span>
          <span className="font-mono">{mins}:{secs}</span>
        </div>
        <div className="h-1.5 bg-white/[0.06] rounded-full overflow-hidden">
          <div
            className="h-full bg-gradient-to-r from-purple-500 to-blue-500 transition-all duration-500"
            style={{ width: `${progress}%` }}
          />
        </div>
      </div>

      {/* Question card */}
      {question && (
        <div className="glass border border-white/10 rounded-2xl p-6 space-y-5">
          <p className="text-white font-medium leading-relaxed">{question.question}</p>

          {/* MCQ / T-F options */}
          {(question.question_type === "MULTIPLECHOICE") &&
            question.options && (
              <div className="space-y-2">
                {Object.entries(question.options).map(([key, val]) => (
                  <button
                    key={key}
                    onClick={() => setSelected(key)}
                    className={cn(
                      "w-full text-left px-4 py-3 rounded-xl border text-sm transition",
                      selected === key
                        ? "border-purple-500/60 bg-purple-600/15 text-white"
                        : "border-white/[0.08] bg-white/[0.02] text-white/70 hover:border-white/20 hover:text-white"
                    )}
                  >
                    <span className="font-semibold mr-2">{key}.</span>{val}
                  </button>
                ))}
              </div>
            )}

          {/* Short answer */}
          {question.question_type === "SHORT" && (
            <textarea
              rows={3}
              value={textAnswer}
              onChange={(e) => setTextAnswer(e.target.value)}
              placeholder="Type your answer…"
              className="w-full bg-white/[0.05] border border-white/[0.08] rounded-xl px-4 py-3 text-sm text-white placeholder:text-white/30 outline-none focus:border-purple-500/50 transition resize-none"
            />
          )}

          {/* Actions */}
          <div className="flex gap-3 pt-2">
            <button
              onClick={handleAnswer}
              disabled={submitting}
              className="flex-1 py-2.5 rounded-xl text-sm font-semibold text-white bg-purple-600 hover:bg-purple-500 disabled:opacity-50 transition"
            >
              {submitting ? <i className="ri-loader-4-line animate-spin" /> : "Next →"}
            </button>
            <button
              onClick={handleSubmit}
              disabled={submitting}
              className="px-4 py-2.5 rounded-xl text-sm text-white/40 hover:text-red-400 hover:bg-red-500/10 transition"
            >
              End Exam
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
