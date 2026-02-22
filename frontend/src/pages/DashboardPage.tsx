import { useState, useCallback, useEffect, useRef } from "react";
import { useDropzone } from "react-dropzone";
import { Link } from "react-router-dom";
import { processDocument, getJobStatus, getMyQuizzes } from "@/services/api";
import { useToast } from "@/components/ui/ToastProvider";
import { cn } from "@/utils";
import type { ProcessingJob } from "@/types";

interface JobState {
  id: number;
  status: string;
  original_filename: string;
  num_questions?: number;
  question_type?: string;
  error_message?: string;
}

const QUESTION_COUNTS = [10, 15, 20] as const;

const LANGUAGES = [
  { value: "auto", label: "Auto Detect" },
  { value: "english", label: "English" },
  { value: "bengali", label: "Bangla" },
];

export default function DashboardPage() {
  const [file, setFile] = useState<File | null>(null);
  const [numQuestions, setNumQuestions] = useState<number | "custom">(10);
  const [customCount, setCustomCount] = useState("");
  const [questionType, setQuestionType] = useState<"mcq" | "short_answer">("mcq");
  const [language, setLanguage] = useState("auto");
  const [loading, setLoading] = useState(false);
  const [job, setJob] = useState<JobState | null>(null);
  const [polling, setPolling] = useState(false);
  const [recentJobs, setRecentJobs] = useState<ProcessingJob[]>([]);
  const [progress, setProgress] = useState(0);
  const progressRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const { toast } = useToast();

  // Load recent quizzes on mount
  useEffect(() => {
    getMyQuizzes()
      .then((res) => setRecentJobs((res.jobs ?? []).slice(0, 5)))
      .catch((err) => console.error("Failed to load recent quizzes:", err));
  }, []);

  // Simulate progress percentage for pending/processing jobs
  useEffect(() => {
    if (progressRef.current) clearInterval(progressRef.current);
    const status = job?.status;
    if (job && ["pending", "processing"].includes(status ?? "")) {
      setProgress(5);
      progressRef.current = setInterval(() => {
        setProgress((p) => (p < 90 ? p + Math.random() * 4 : p));
      }, 800);
    } else if (status === "completed") {
      setProgress(100);
    } else {
      setProgress(0);
    }
    return () => {
      if (progressRef.current) clearInterval(progressRef.current);
    };
  }, [job]); // eslint-disable-line

  // Drop zone
  const onDrop = useCallback((accepted: File[]) => {
    if (accepted[0]) setFile(accepted[0]);
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    maxFiles: 1,
    accept: {
      "image/*": [".jpg", ".jpeg", ".png"],
      "application/pdf": [".pdf"],
      "application/vnd.ms-powerpoint": [".ppt"],
      "application/vnd.openxmlformats-officedocument.presentationml.presentation": [".pptx"],
      "application/msword": [".doc"],
      "application/vnd.openxmlformats-officedocument.wordprocessingml.document": [".docx"],
      "text/plain": [".txt"],
    },
    maxSize: 50 * 1024 * 1024, // 50 MB
  });

  // Poll job status
  useEffect(() => {
    if (!job || !polling) return;
    if (["completed", "failed"].includes(job.status)) {
      setPolling(false);
      return;
    }
    const timer = setTimeout(async () => {
      try {
        const res = await getJobStatus(job.id);
        setJob((prev) => prev ? { ...prev, status: res.status } : null);
      } catch {
        // ignore
      }
    }, 3000);
    return () => clearTimeout(timer);
  }, [job, polling]);

  async function handleGenerate() {
    if (!file) return toast("Please drop a file first", "error");
    const count = numQuestions === "custom" ? Number(customCount) : numQuestions;
    if (!count || count < 1) return toast("Please enter a valid question count", "error");
    setLoading(true);
    setJob(null);
    try {
      const fd = new FormData();
      fd.append("document", file);
      fd.append("num_questions", String(count));
      fd.append("question_type", questionType);
      fd.append("language", language);
      const res = await processDocument(fd);
      toast("Document submitted! Processing started.", "success");
      setJob({ id: res.job_id, status: "pending", original_filename: file.name, question_type: questionType });
      setPolling(true);
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : "Upload failed";
      toast(msg, "error");
    } finally {
      setLoading(false);
    }
  }

  // When job completes, refresh recent quizzes list
  useEffect(() => {
    if (job?.status === "completed") {
      getMyQuizzes()
        .then((res) => setRecentJobs((res.jobs ?? []).slice(0, 5)))
        .catch((err) => console.error("Failed to refresh quiz list:", err));
    }
  }, [job]);

  const statusColor: Record<string, string> = {
    pending: "text-yellow-400",
    processing: "text-blue-400",
    completed: "text-green-400",
    failed: "text-red-400",
  };

  return (
    <div className="fade-in">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-white">Create New Quiz</h1>
        <span className="flex items-center gap-1 px-3 py-1 rounded-full bg-purple-600/20 border border-purple-500/30 text-purple-300 text-xs font-medium">
          <span className="material-icons text-sm">auto_awesome</span>
          AI Powered
        </span>
      </div>

      {/* Two-column grid: left = form, right = quiz status */}
      <div className="grid grid-cols-1 lg:grid-cols-[1fr_340px] gap-6 items-start">

        {/* ── LEFT COLUMN ── */}
        <div className="space-y-6">

          {/* Drop Zone */}
          <div
            {...getRootProps()}
            className={cn(
              "glass border-2 border-dashed rounded-2xl p-10 text-center cursor-pointer transition",
              isDragActive
                ? "border-purple-400 bg-purple-500/10"
                : "border-white/20 hover:border-purple-400/50 hover:bg-white/[0.03]"
            )}
          >
            <input {...getInputProps()} />
            {file ? (
              <div className="space-y-2">
                <span className="material-icons text-4xl text-purple-400">picture_as_pdf</span>
                <p className="text-white font-medium">{file.name}</p>
                <p className="text-white/40 text-xs">
                  {(file.size / 1024 / 1024).toFixed(2)} MB
                </p>
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    setFile(null);
                    setJob(null);
                  }}
                  className="text-xs text-red-400 hover:text-red-300 transition"
                >
                  <i className="ri-close-line" /> Remove
                </button>
              </div>
            ) : (
              <div className="space-y-3">
                <span className="material-icons text-5xl text-white/20">cloud_upload</span>
                <div>
                  <h3 className="text-white/80 font-semibold text-base">
                    {isDragActive ? "Drop it here…" : "Upload your study material"}
                  </h3>
                  <p className="text-white/40 text-sm mt-1">
                    Drag and drop your PDF, PPT, or images here to let our AI generate a quiz instantly.
                  </p>
                </div>
                <button
                  type="button"
                  className="inline-flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-medium
                    bg-white/[0.08] border border-white/10 text-white/70 hover:bg-white/[0.12] transition"
                >
                  <span className="material-icons text-base">folder_open</span>
                  Browse Files
                </button>
                <p className="text-white/30 text-xs">Supported: PDF, DOCX, JPG, PNG (Max 50MB)</p>
              </div>
            )}
          </div>

          {/* Config */}
          <div className="glass border border-white/10 rounded-2xl p-6 space-y-5">
            {/* Number of questions */}
            <div className="space-y-2">
              <label className="flex items-center gap-1.5 text-xs font-semibold text-white/50 uppercase tracking-wider">
                <span className="material-icons text-sm">format_list_numbered</span>
                Number of Questions
              </label>
              <div className="flex flex-wrap gap-2">
                {QUESTION_COUNTS.map((n) => (
                  <button
                    key={n}
                    onClick={() => setNumQuestions(n)}
                    className={cn(
                      "px-4 py-2 rounded-xl text-sm font-medium border transition",
                      numQuestions === n
                        ? "bg-purple-600/30 border-purple-500/50 text-purple-300"
                        : "bg-white/[0.05] border-white/10 text-white/60 hover:bg-white/[0.08] hover:text-white/80"
                    )}
                  >
                    {n}
                  </button>
                ))}
                <button
                  onClick={() => setNumQuestions("custom")}
                  className={cn(
                    "px-4 py-2 rounded-xl text-sm font-medium border transition",
                    numQuestions === "custom"
                      ? "bg-purple-600/30 border-purple-500/50 text-purple-300"
                      : "bg-white/[0.05] border-white/10 text-white/60 hover:bg-white/[0.08] hover:text-white/80"
                  )}
                >
                  Custom
                </button>
                {numQuestions === "custom" && (
                  <input
                    type="number"
                    min={1}
                    max={100}
                    placeholder="Enter count"
                    value={customCount}
                    onChange={(e) => setCustomCount(e.target.value)}
                    className="px-3 py-2 rounded-xl text-sm bg-white/[0.05] border border-white/10 text-white
                      outline-none focus:border-purple-500/50 transition w-32"
                  />
                )}
              </div>
            </div>

            {/* Question type */}
            <div className="space-y-2">
              <label className="flex items-center gap-1.5 text-xs font-semibold text-white/50 uppercase tracking-wider">
                <span className="material-icons text-sm">quiz</span>
                Question Type
              </label>
              <div className="flex gap-2">
                <button
                  onClick={() => setQuestionType("mcq")}
                  className={cn(
                    "flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-medium border transition",
                    questionType === "mcq"
                      ? "bg-purple-600/30 border-purple-500/50 text-purple-300"
                      : "bg-white/[0.05] border-white/10 text-white/60 hover:bg-white/[0.08] hover:text-white/80"
                  )}
                >
                  <span className="material-icons text-base">check_circle</span>
                  MCQ
                </button>
                <button
                  onClick={() => setQuestionType("short_answer")}
                  className={cn(
                    "flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-medium border transition",
                    questionType === "short_answer"
                      ? "bg-purple-600/30 border-purple-500/50 text-purple-300"
                      : "bg-white/[0.05] border-white/10 text-white/60 hover:bg-white/[0.08] hover:text-white/80"
                  )}
                >
                  <span className="material-icons text-base">edit</span>
                  Short Ans
                </button>
              </div>
            </div>

            {/* Language */}
            <div className="space-y-2">
              <label className="flex items-center gap-1.5 text-xs font-semibold text-white/50 uppercase tracking-wider">
                <span className="material-icons text-sm">translate</span>
                Language
              </label>
              <div className="flex flex-wrap gap-2">
                {LANGUAGES.map((l) => (
                  <button
                    key={l.value}
                    onClick={() => setLanguage(l.value)}
                    className={cn(
                      "px-4 py-2 rounded-xl text-sm font-medium border transition",
                      language === l.value
                        ? "bg-purple-600/30 border-purple-500/50 text-purple-300"
                        : "bg-white/[0.05] border-white/10 text-white/60 hover:bg-white/[0.08] hover:text-white/80"
                    )}
                  >
                    {l.label}
                  </button>
                ))}
              </div>
            </div>
          </div>

          {/* Generate button */}
          <button
            onClick={handleGenerate}
            disabled={!file || loading}
            className={cn(
              "w-full py-3 rounded-xl font-semibold text-white transition",
              "bg-gradient-to-r from-purple-600 to-blue-600",
              "hover:from-purple-500 hover:to-blue-500 shadow-lg",
              "disabled:opacity-40 disabled:cursor-not-allowed"
            )}
          >
            {loading ? (
              <span className="flex items-center justify-center gap-2">
                <i className="ri-loader-4-line animate-spin" /> Uploading…
              </span>
            ) : (
              <span className="flex items-center justify-center gap-2">
                <span className="material-icons text-base">auto_awesome</span>
                Generate Quiz
              </span>
            )}
          </button>

          {/* Recent Activity */}
          <div className="glass border border-white/10 rounded-2xl p-6 space-y-4">
            <div className="flex items-center justify-between">
              <h4 className="text-sm font-semibold text-white/70">Recent Activity</h4>
              <Link to="/my-quizzes" className="text-xs text-purple-400 hover:text-purple-300 transition">
                View All
              </Link>
            </div>
            <div className="space-y-2">
              {RECENT_ACTIVITY.map((item, idx) => (
                <div key={idx} className="flex items-center gap-3 p-2 rounded-xl hover:bg-white/[0.04] transition cursor-pointer group">
                  <div
                    className={cn(
                      "w-10 h-10 rounded-xl flex items-center justify-center text-xs font-bold shrink-0",
                      item.score >= 80 ? "bg-green-500/20 text-green-400" :
                      item.score >= 60 ? "bg-yellow-500/20 text-yellow-400" :
                      "bg-red-500/20 text-red-400"
                    )}
                  >
                    {item.score}%
                  </div>
                  <div className="flex-1 min-w-0">
                    <h5 className="text-sm font-medium text-white/80 truncate">{item.title}</h5>
                    <p className="text-xs text-white/40">{item.date} • {item.questions} Qs</p>
                  </div>
                  <span className="material-icons text-white/20 group-hover:text-white/50 transition text-base">chevron_right</span>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* ── RIGHT COLUMN: Quiz Status ── */}
        <div
          data-testid="quiz-status-panel"
          className="glass border border-white/10 rounded-2xl p-6 space-y-4 lg:sticky lg:top-6"
        >
          <h3 className="text-sm font-semibold text-white/70">Quiz Status</h3>

          {/* No quizzes yet */}
          {!job && recentJobs.length === 0 && (
            <div className="flex flex-col items-center gap-3 py-8 text-center">
              <span className="material-icons text-4xl text-white/10">quiz</span>
              <p className="text-xs text-white/30">No quizzes yet.<br />Generate your first quiz above.</p>
            </div>
          )}

          {/* Currently submitted job – processing */}
          {job && ["pending", "processing"].includes(job.status) && (
            <div className="flex items-center gap-3 p-3 rounded-xl bg-white/[0.04]">
              <span className="material-icons text-purple-400 text-2xl">picture_as_pdf</span>
              <div className="flex-1 min-w-0">
                <h4 className="text-sm font-medium text-white truncate">{job.original_filename}</h4>
                <div className="flex items-center gap-2 mt-1">
                  <div className="flex-1 h-1 rounded-full bg-white/10 overflow-hidden">
                    <div
                      className="h-full rounded-full bg-gradient-to-r from-purple-500 to-blue-500 transition-all duration-700"
                      style={{ width: `${Math.round(progress)}%` }}
                    />
                  </div>
                  <span className="text-xs text-white/50 shrink-0">{Math.round(progress)}%</span>
                </div>
                <p className="text-xs text-white/40 mt-0.5">Processing…</p>
              </div>
              <span className={cn("text-xs font-semibold capitalize", statusColor[job.status] ?? "text-white/50")}>
                <i className="ri-loader-4-line animate-spin" /> {job.status}
              </span>
            </div>
          )}

          {/* Currently submitted job – completed */}
          {job && job.status === "completed" && (
            <div className="flex items-center gap-3 p-3 rounded-xl bg-white/[0.04]">
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 mb-0.5">
                  <span className="text-xs font-semibold text-green-400">Ready</span>
                  <span className="text-xs text-white/30">just now</span>
                </div>
                <h4 className="text-sm font-medium text-white truncate">{job.original_filename}</h4>
                {job.num_questions && (
                  <p className="text-xs text-white/40">{job.num_questions} Questions · {job.question_type === "mcq" ? "MCQ" : "Short Ans"}</p>
                )}
                <p className="text-xs text-white/30 mt-0.5 flex items-center gap-1">
                  <span className="px-1 py-0.5 rounded bg-purple-600/30 text-purple-300 text-[10px] font-bold">AI</span>
                  Generated from &quot;{job.original_filename}&quot;
                </p>
              </div>
              <Link
                to="/my-quizzes"
                className="flex items-center gap-1 px-3 py-1.5 rounded-lg text-sm font-medium
                  bg-purple-600/20 text-purple-300 border border-purple-500/30 hover:bg-purple-600/30 transition whitespace-nowrap"
              >
                Start Exam
                <span className="material-icons text-base">arrow_forward</span>
              </Link>
            </div>
          )}

          {/* Currently submitted job – failed */}
          {job && job.status === "failed" && (
            <div className="flex items-center gap-3 p-3 rounded-xl bg-red-500/10 border border-red-500/20">
              <span className="material-icons text-red-400">error</span>
              <div className="flex-1 min-w-0">
                <h4 className="text-sm font-medium text-red-300">Processing failed</h4>
                <p className="text-xs text-white/40 truncate">{job.original_filename}</p>
              </div>
            </div>
          )}

          {/* Recent completed quizzes from API */}
          {recentJobs
            .filter((j) => !job || j.id !== job.id)
            .filter((j) => j.status === "completed")
            .slice(0, 2)
            .map((j) => (
              <div key={j.id} className="flex items-center gap-3 p-3 rounded-xl bg-white/[0.04]">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-0.5">
                    <span className="text-xs font-semibold text-green-400">Ready</span>
                    <span className="text-xs text-white/30">
                      {j.completed_at ? new Date(j.completed_at).toLocaleDateString() : ""}
                    </span>
                  </div>
                  <h4 className="text-sm font-medium text-white truncate">{j.original_filename}</h4>
                  <p className="text-xs text-white/40">
                    {j.num_questions} Questions · {j.question_type === "MULTIPLECHOICE" ? "MCQ" : "Short Ans"}
                  </p>
                  <p className="text-xs text-white/30 mt-0.5 flex items-center gap-1">
                    <span className="px-1 py-0.5 rounded bg-purple-600/30 text-purple-300 text-[10px] font-bold">AI</span>
                    Generated from &quot;{j.original_filename}&quot;
                  </p>
                </div>
                <Link
                  to="/my-quizzes"
                  className="flex items-center gap-1 px-3 py-1.5 rounded-lg text-sm font-medium
                    bg-purple-600/20 text-purple-300 border border-purple-500/30 hover:bg-purple-600/30 transition whitespace-nowrap"
                >
                  Start Exam
                  <span className="material-icons text-base">arrow_forward</span>
                </Link>
              </div>
            ))}
        </div>
      </div>
    </div>
  );
}

const RECENT_ACTIVITY = [
  { title: "Chemistry Basics", score: 85, date: "Yesterday", questions: 15 },
  { title: "English Literature", score: 60, date: "2 days ago", questions: 10 },
  { title: "Math: Calculus 101", score: 92, date: "Oct 24", questions: 20 },
];
