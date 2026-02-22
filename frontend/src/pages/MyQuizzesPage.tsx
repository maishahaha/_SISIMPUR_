import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { getMyQuizzes, deleteJob } from "@/services/api";
import { useToast } from "@/components/ui/ToastProvider";
import { cn, formatDate, statusColor } from "@/utils";
import type { ProcessingJob } from "@/types";

export default function MyQuizzesPage() {
  const [jobs, setJobs] = useState<ProcessingJob[]>([]);
  const [loading, setLoading] = useState(true);
  const { toast } = useToast();

  async function load() {
    setLoading(true);
    try {
      const res = await getMyQuizzes();
      setJobs(res.jobs ?? []);
    } catch {
      toast("Failed to load quizzes", "error");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => { load(); }, []); // eslint-disable-line

  async function handleDelete(jobId: number, name: string) {
    if (!confirm(`Delete "${name}"? This cannot be undone.`)) return;
    try {
      await deleteJob(jobId);
      setJobs((prev) => prev.filter((j) => j.id !== jobId));
      toast("Quiz deleted", "success");
    } catch {
      toast("Delete failed", "error");
    }
  }

  return (
    <div className="space-y-6 fade-in">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">My Quizzes</h1>
          <p className="text-white/40 text-sm mt-1">Your generated quizzes and documents</p>
        </div>
        <Link
          to="/dashboard"
          className="flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-medium
            bg-purple-600/20 text-purple-300 border border-purple-500/30 hover:bg-purple-600/30 transition"
        >
          <i className="ri-add-line" /> New Quiz
        </Link>
      </div>

      {loading ? (
        <div className="flex items-center justify-center h-48">
          <i className="ri-loader-4-line animate-spin text-3xl text-white/30" />
        </div>
      ) : jobs.length === 0 ? (
        <div className="glass border border-white/10 rounded-2xl p-16 text-center">
          <i className="ri-book-open-line text-5xl text-white/10 mb-4 block" />
          <p className="text-white/30 text-sm">No quizzes yet. Create your first one!</p>
          <Link
            to="/dashboard"
            className="inline-flex items-center gap-2 mt-4 px-4 py-2 rounded-xl text-sm font-medium
              bg-purple-600 text-white hover:bg-purple-500 transition"
          >
            <i className="ri-sparkling-2-line" /> Create Quiz
          </Link>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
          {jobs.map((job) => (
            <QuizCard key={job.id} job={job} onDelete={handleDelete} />
          ))}
        </div>
      )}
    </div>
  );
}

function QuizCard({
  job,
  onDelete,
}: {
  job: ProcessingJob;
  onDelete: (id: number, name: string) => void;
}) {
  const color = statusColor(job.status);

  return (
    <div className="glass border border-white/10 rounded-2xl p-5 flex flex-col gap-4 hover:border-white/20 transition">
      {/* Header */}
      <div className="flex items-start justify-between gap-2">
        <div className="flex-1 min-w-0">
          <p className="text-white font-medium text-sm truncate">{job.original_filename}</p>
          <p className="text-white/40 text-xs mt-0.5">{formatDate(job.created_at)}</p>
        </div>
        <span className={cn("text-xs font-medium capitalize px-2 py-0.5 rounded-full", color)}>
          {job.status}
        </span>
      </div>

      {/* Meta */}
      <div className="flex items-center gap-4 text-xs text-white/40">
        {job.num_questions !== undefined && (
          <span><i className="ri-question-line mr-1" />{job.num_questions} Q</span>
        )}
        {job.question_type && (
          <span className="capitalize">{job.question_type.replace("_", " ")}</span>
        )}
        {job.language && <span className="capitalize">{job.language}</span>}
      </div>

      {/* Actions */}
      {job.status === "completed" && (
        <div className="flex gap-2 mt-auto">
          <Link
            to={`/give-exam?jobId=${job.id}`}
            className="flex-1 py-1.5 rounded-lg text-xs font-medium text-center
              bg-purple-600/20 text-purple-300 border border-purple-500/30 hover:bg-purple-600/30 transition"
          >
            <i className="ri-pencil-line mr-1" />Exam
          </Link>
          <Link
            to={`/give-exam?jobId=${job.id}&mode=flashcard`}
            className="flex-1 py-1.5 rounded-lg text-xs font-medium text-center
              bg-blue-600/20 text-blue-300 border border-blue-500/30 hover:bg-blue-600/30 transition"
          >
            <i className="ri-stack-line mr-1" />Flashcard
          </Link>
          <Link
            to={`/quiz-results/${job.id}`}
            className="flex-1 py-1.5 rounded-lg text-xs font-medium text-center
              bg-white/[0.05] text-white/50 border border-white/10 hover:bg-white/10 transition"
          >
            <i className="ri-bar-chart-line mr-1" />Results
          </Link>
        </div>
      )}

      {/* Delete */}
      <button
        onClick={() => onDelete(job.id, job.original_filename)}
        className="text-xs text-white/20 hover:text-red-400 transition flex items-center gap-1 self-start"
      >
        <i className="ri-delete-bin-line" /> Delete
      </button>
    </div>
  );
}
