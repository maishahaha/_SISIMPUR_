import { useEffect, useState } from "react";
import { useSearchParams, useNavigate } from "react-router-dom";
import { getMyQuizzes, startExam, startFlashcard } from "@/services/api";
import { useToast } from "@/components/ui/ToastProvider";
import { cn } from "@/utils";
import type { ProcessingJob } from "@/types";

export default function GiveExamPage() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const { toast } = useToast();

  const preselectedJobId = searchParams.get("jobId") ?? "";
  const preselectedMode = searchParams.get("mode") ?? "exam";

  const [jobs, setJobs] = useState<ProcessingJob[]>([]);
  const [selectedJobId, setSelectedJobId] = useState<number | null>(
    preselectedJobId ? Number(preselectedJobId) : null
  );
  const [mode, setMode] = useState<"exam" | "flashcard">(
    preselectedMode === "flashcard" ? "flashcard" : "exam"
  );
  const [loading, setLoading] = useState(false);
  const [fetching, setFetching] = useState(true);

  useEffect(() => {
    getMyQuizzes()
      .then((res) =>
        setJobs((res.jobs ?? []).filter((j) => j.status === "completed"))
      )
      .catch(() => toast("Failed to load quizzes", "error"))
      .finally(() => setFetching(false));
  }, []); // eslint-disable-line

  async function handleStart() {
    if (!selectedJobId) return toast("Select a quiz first", "error");
    setLoading(true);
    try {
      if (mode === "exam") {
        const res = await startExam(selectedJobId);
        navigate(`/exam/${res.session_id}`);
      } else {
        const res = await startFlashcard(selectedJobId);
        navigate(`/flashcard/${res.session_id}`);
      }
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : "Failed to start";
      toast(msg, "error");
      setLoading(false);
    }
  }

  return (
    <div className="max-w-xl mx-auto space-y-6 fade-in">
      <div>
        <h1 className="text-2xl font-bold text-white">Give Exam</h1>
        <p className="text-white/40 text-sm mt-1">Choose a quiz and start practicing</p>
      </div>

      {/* Mode toggle */}
      <div className="flex gap-1 p-1 bg-white/[0.05] rounded-xl">
        {(["exam", "flashcard"] as const).map((m) => (
          <button
            key={m}
            onClick={() => setMode(m)}
            className={cn(
              "flex-1 py-2 rounded-lg text-sm font-medium capitalize transition flex items-center justify-center gap-2",
              mode === m
                ? "bg-purple-600 text-white shadow"
                : "text-white/50 hover:text-white"
            )}
          >
            <i className={m === "exam" ? "ri-pencil-ruler-2-line" : "ri-stack-line"} />
            {m === "exam" ? "Exam Mode" : "Flashcard Mode"}
          </button>
        ))}
      </div>

      {/* Quiz selector */}
      <div className="glass border border-white/10 rounded-2xl p-5 space-y-3">
        <p className="text-sm font-medium text-white/60">Select a Quiz</p>
        {fetching ? (
          <div className="flex items-center justify-center h-20">
            <i className="ri-loader-4-line animate-spin text-2xl text-white/30" />
          </div>
        ) : jobs.length === 0 ? (
          <p className="text-white/30 text-sm text-center py-6">
            No completed quizzes. <a href="/dashboard" className="text-purple-400 hover:underline">Create one first.</a>
          </p>
        ) : (
          <div className="space-y-2 max-h-64 overflow-y-auto pr-1">
            {jobs.map((job) => (
              <button
                key={job.id}
                onClick={() => setSelectedJobId(job.id)}
                className={cn(
                  "w-full text-left p-3 rounded-xl border transition",
                  selectedJobId === job.id
                    ? "border-purple-500/50 bg-purple-600/10"
                    : "border-white/[0.06] bg-white/[0.02] hover:border-white/20"
                )}
              >
                <p className="text-sm text-white font-medium truncate">{job.original_filename}</p>
                <p className="text-xs text-white/30 mt-0.5">
                  {job.num_questions} questions · {job.question_type?.replace("_", " ")}
                </p>
              </button>
            ))}
          </div>
        )}
      </div>

      <button
        onClick={handleStart}
        disabled={!selectedJobId || loading}
        className={cn(
          "w-full py-3 rounded-xl font-semibold text-white transition",
          "bg-gradient-to-r from-purple-600 to-blue-600",
          "hover:from-purple-500 hover:to-blue-500 shadow-lg",
          "disabled:opacity-40 disabled:cursor-not-allowed"
        )}
      >
        {loading ? (
          <span className="flex items-center justify-center gap-2">
            <i className="ri-loader-4-line animate-spin" /> Starting…
          </span>
        ) : (
          <span className="flex items-center justify-center gap-2">
            <i className={mode === "exam" ? "ri-play-line" : "ri-stack-line"} />
            Start {mode === "exam" ? "Exam" : "Flashcard"}
          </span>
        )}
      </button>
    </div>
  );
}
