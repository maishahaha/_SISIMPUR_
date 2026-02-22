import { clsx, type ClassValue } from "clsx";

export function cn(...inputs: ClassValue[]) {
  return clsx(inputs);
}

/** Format a date string like "Jan 01, 2026 12:30" */
export function formatDate(iso: string) {
  return new Date(iso).toLocaleString("en-US", {
    month: "short",
    day: "2-digit",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

/** Format seconds to MM:SS */
export function formatTime(seconds: number) {
  if (seconds <= 0) return "00:00";
  const m = Math.floor(seconds / 60)
    .toString()
    .padStart(2, "0");
  const s = Math.floor(seconds % 60)
    .toString()
    .padStart(2, "0");
  return `${m}:${s}`;
}

/** Return Tailwind colour classes for a job status badge */
export function statusColor(status: string) {
  switch (status) {
    case "completed":
      return "bg-emerald-500/20 text-emerald-400 border border-emerald-500/30";
    case "processing":
      return "bg-blue-500/20 text-blue-400 border border-blue-500/30";
    case "failed":
      return "bg-red-500/20 text-red-400 border border-red-500/30";
    default:
      return "bg-gray-500/20 text-gray-400 border border-gray-500/30";
  }
}

/** Return a label for question type */
export function questionTypeLabel(type: string) {
  switch (type) {
    case "MULTIPLECHOICE":
      return "Multiple Choice";
    case "SHORT":
      return "Short Answer";
    default:
      return type;
  }
}
