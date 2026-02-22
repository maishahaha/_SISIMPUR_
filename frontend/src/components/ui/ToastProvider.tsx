import React, { createContext, useContext, useState, useCallback } from "react";
import { cn } from "@/utils";

type ToastType = "success" | "error" | "info" | "warning";

interface Toast {
  id: string;
  message: string;
  type: ToastType;
}

interface ToastContextValue {
  toast: (message: string, type?: ToastType) => void;
}

const ToastContext = createContext<ToastContextValue>({ toast: () => {} });

export function ToastProvider({ children }: { children: React.ReactNode }) {
  const [toasts, setToasts] = useState<Toast[]>([]);

  const toast = useCallback((message: string, type: ToastType = "info") => {
    const id = Math.random().toString(36).slice(2);
    setToasts((prev) => [...prev, { id, message, type }]);
    setTimeout(() => {
      setToasts((prev) => prev.filter((t) => t.id !== id));
    }, 4000);
  }, []);

  const icon: Record<ToastType, string> = {
    success: "ri-check-circle-line text-emerald-400",
    error: "ri-error-warning-line text-red-400",
    info: "ri-information-line text-blue-400",
    warning: "ri-alert-line text-yellow-400",
  };

  const border: Record<ToastType, string> = {
    success: "border-emerald-500/40",
    error: "border-red-500/40",
    info: "border-blue-500/40",
    warning: "border-yellow-500/40",
  };

  return (
    <ToastContext.Provider value={{ toast }}>
      {children}
      <div className="fixed bottom-6 right-6 z-50 flex flex-col gap-2">
        {toasts.map((t) => (
          <div
            key={t.id}
            className={cn(
              "glass flex items-center gap-3 px-4 py-3 rounded-xl min-w-[280px] max-w-sm fade-in",
              "border",
              border[t.type]
            )}
          >
            <i className={cn("text-lg", icon[t.type])} />
            <span className="text-sm text-white/90">{t.message}</span>
            <button
              onClick={() => setToasts((p) => p.filter((x) => x.id !== t.id))}
              className="ml-auto text-white/40 hover:text-white/80 transition"
            >
              <i className="ri-close-line" />
            </button>
          </div>
        ))}
      </div>
    </ToastContext.Provider>
  );
}

export function useToast() {
  return useContext(ToastContext);
}
