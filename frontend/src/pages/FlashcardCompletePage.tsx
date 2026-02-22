import { useParams, useNavigate } from "react-router-dom";
import { cn } from "@/utils";

export default function FlashcardCompletePage() {
  const { sessionId } = useParams<{ sessionId: string }>();
  const navigate = useNavigate();
  void sessionId; // available for future API call

  return (
    <div className="max-w-md mx-auto text-center space-y-6 pt-12 fade-in">
      <div className="w-20 h-20 rounded-full bg-gradient-to-br from-purple-500 to-teal-500 flex items-center justify-center mx-auto">
        <i className="ri-check-double-line text-4xl text-white" />
      </div>

      <div>
        <h1 className="text-3xl font-bold gradient-text">Session Complete!</h1>
        <p className="text-white/40 mt-2 text-sm">
          You've reviewed all the flashcards in this session.
        </p>
      </div>

      <div className="glass border border-white/10 rounded-2xl p-6 text-left space-y-3">
        <p className="text-xs text-white/40 uppercase tracking-wider">Tips</p>
        <ul className="space-y-2 text-sm text-white/60">
          <li className="flex items-start gap-2">
            <i className="ri-arrow-right-line text-purple-400 mt-0.5" />
            Repeat cards you marked as <span className="text-red-400 mx-1">Hard</span> tomorrow.
          </li>
          <li className="flex items-start gap-2">
            <i className="ri-arrow-right-line text-purple-400 mt-0.5" />
            <span className="text-yellow-400 mr-1">Medium</span> cards in 3 days.
          </li>
          <li className="flex items-start gap-2">
            <i className="ri-arrow-right-line text-purple-400 mt-0.5" />
            <span className="text-green-400 mr-1">Easy</span> cards in a week.
          </li>
        </ul>
      </div>

      <div className="flex gap-3">
        <button
          onClick={() => navigate("/give-exam")}
          className={cn(
            "flex-1 py-3 rounded-xl text-sm font-semibold text-white",
            "bg-gradient-to-r from-purple-600 to-teal-600 hover:from-purple-500 hover:to-teal-500 transition"
          )}
        >
          <i className="ri-stack-line mr-1.5" />New Session
        </button>
        <button
          onClick={() => navigate("/dashboard")}
          className="flex-1 py-3 rounded-xl text-sm font-medium glass border border-white/10 text-white/60 hover:text-white hover:border-white/20 transition"
        >
          <i className="ri-home-line mr-1.5" />Home
        </button>
      </div>
    </div>
  );
}
