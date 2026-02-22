import { useEffect, useState, useCallback } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { getFlashcardSession, advanceFlashcard } from "@/services/api";
import { useToast } from "@/components/ui/ToastProvider";
import { cn } from "@/utils";
import type { FlashcardSessionResponse } from "@/types";

export default function FlashcardPage() {
  const { sessionId } = useParams<{ sessionId: string }>();
  const navigate = useNavigate();
  const { toast } = useToast();

  const [session, setSession] = useState<FlashcardSessionResponse | null>(null);
  const [flipped, setFlipped] = useState(false);
  const [loading, setLoading] = useState(true);
  const [advancing, setAdvancing] = useState(false);

  const refresh = useCallback(async () => {
    if (!sessionId) return;
    const res = await getFlashcardSession(sessionId);
    setSession(res);
    setFlipped(false);
  }, [sessionId]);

  useEffect(() => {
    setLoading(true);
    refresh().catch(() => toast("Session error", "error")).finally(() => setLoading(false));
  }, [refresh]); // eslint-disable-line

  useEffect(() => {
    if (session?.status === "completed") {
      navigate(`/flashcard/complete/${sessionId}`);
    }
  }, [session, sessionId, navigate]);

  async function advance() {
    if (!sessionId) return;
    setAdvancing(true);
    try {
      const res = await advanceFlashcard(sessionId, "next");
      if (res.completed) {
        navigate(`/flashcard/complete/${sessionId}`);
      } else {
        await refresh();
      }
    } catch {
      toast("Error advancing", "error");
    } finally {
      setAdvancing(false);
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <i className="ri-loader-4-line animate-spin text-3xl text-white/30" />
      </div>
    );
  }

  const card = session?.card;
  const progress = session?.progress_percentage ?? 0;

  return (
    <div className="max-w-xl mx-auto space-y-6 fade-in">
      {/* Progress */}
      <div className="space-y-2">
        <div className="flex items-center justify-between text-xs text-white/40">
          <span>Card {(session?.current_index ?? 0) + 1} of {session?.total_cards}</span>
          <span>{Math.round(progress)}%</span>
        </div>
        <div className="h-1.5 bg-white/[0.06] rounded-full overflow-hidden">
          <div
            className="h-full bg-gradient-to-r from-purple-500 to-teal-500 transition-all duration-500"
            style={{ width: `${progress}%` }}
          />
        </div>
      </div>

      {/* Card */}
      {card && (
        <div
          onClick={() => setFlipped((f) => !f)}
          className={cn(
            "glass border rounded-2xl p-8 min-h-[220px] flex flex-col items-center justify-center",
            "cursor-pointer transition-all duration-300 select-none",
            flipped ? "border-purple-500/40 bg-purple-600/5" : "border-white/10 hover:border-white/20"
          )}
        >
          <p className="text-xs text-white/30 uppercase tracking-widest mb-4">
            {flipped ? "Answer" : "Question"}
          </p>
          <p className="text-white text-center leading-relaxed">
            {flipped ? (card.answer) : (card.question)}
          </p>
          {!flipped && (
            <p className="text-xs text-white/20 mt-6">Tap to reveal answer</p>
          )}
        </div>
      )}

      {/* Rating buttons (shown after flip) */}
      {flipped && (
        <div className="flex gap-3 fade-in">
          <button
            onClick={() => advance()}
            disabled={advancing}
            className="flex-1 py-2.5 rounded-xl text-sm font-semibold text-white bg-purple-600 hover:bg-purple-500 disabled:opacity-50 transition"
          >
            {advancing ? <i className="ri-loader-4-line animate-spin" /> : "Next Card →"}
          </button>
          <button
            onClick={async () => { if (sessionId) { await advanceFlashcard(sessionId, "skip"); await refresh(); } }}
            disabled={advancing}
            className="px-4 py-2.5 rounded-xl text-sm text-white/40 hover:text-white/70 glass border border-white/10 transition"
          >
            Skip
          </button>
        </div>
      )}

      <button
        onClick={() => navigate(`/flashcard/complete/${sessionId}`)}
        className="w-full py-2 text-xs text-white/20 hover:text-white/50 transition"
      >
        End session
      </button>
    </div>
  );
}
