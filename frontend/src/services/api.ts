/**
 * Centralised API client for the Sisimpur Django backend.
 * All requests go through Vite dev server proxy (/api/* → Django).
 *
 * Auth flow:
 *   - Sign-in / sign-up / OTP → Django endpoints (/api/auth/*)
 *   - Django calls Supabase Admin SDK + stores metadata to MongoDB
 *   - Django returns a Supabase JWT → stored in localStorage as "sisimpur_jwt"
 *   - Every subsequent request carries: Authorization: Bearer <token>
 *   - Django verifies the JWT on each protected endpoint
 */

import axios from "axios";
import { getStoredToken } from "@/contexts/AuthContext";
import type {
  OtpResponse,
  AuthTokenResponse,
  MyQuizzesResponse,
  ProcessDocumentResponse,
  JobStatusResponse,
  QuizResultsResponse,
  StartExamResponse,
  ExamSessionResponse,
  AnswerResponse,
  SubmitExamResponse,
  ExamResultResponse,
  StartFlashcardResponse,
  FlashcardSessionResponse,
  AdvanceFlashcardResponse,
  LeaderboardResponse,
} from "@/types";

// ----------------------------------------------------------------
// Axios instance
// ----------------------------------------------------------------
const api = axios.create({
  baseURL: "", // use relative URLs so Vite proxy handles forwarding
  withCredentials: true, // keep sending session + csrftoken cookies (Phase 1 compat)
  headers: { "Content-Type": "application/json" },
});

// Attach CSRF token (Django) + JWT Bearer token on every request.
api.interceptors.request.use((config) => {
  // 1. CSRF cookie (still needed for Django CSRF middleware on non-GET requests)
  if (typeof document !== "undefined") {
    const csrfToken = document.cookie
      .split("; ")
      .find((row) => row.startsWith("csrftoken="))
      ?.split("=")[1];
    if (csrfToken) {
      config.headers["X-CSRFToken"] = csrfToken;
    }
  }

  // 2. JWT issued by Django (backed by Supabase) — stored in localStorage
  const token = getStoredToken();
  if (token) {
    config.headers["Authorization"] = `Bearer ${token}`;
  }

  return config;
});

// Convert error responses to Error instances with the backend's message
api.interceptors.response.use(
  (response) => response,
  (error) => {
    const backendMessage: string | undefined = error.response?.data?.message;
    if (backendMessage) {
      return Promise.reject(new Error(backendMessage));
    }
    return Promise.reject(error);
  }
);


// ----------------------------------------------------------------
// Auth  (all calls go to Django; Django talks to Supabase + MongoDB)
// ----------------------------------------------------------------

/** Send a one-time password to the given email address (signup flow). */
export async function sendOtp(email: string): Promise<OtpResponse> {
  const { data } = await api.post<OtpResponse>("/api/auth/send-otp/", { email });
  if (!data.success) throw new Error(data.message);
  return data;
}

/** Verify the OTP received by email. */
export async function verifyOtp(email: string, otp_code: string): Promise<OtpResponse> {
  const { data } = await api.post<OtpResponse>("/api/auth/verify-otp/", { email, otp_code });
  if (!data.success) throw new Error(data.message);
  return data;
}

/**
 * Sign in with email + password.
 * Returns a Supabase JWT issued by Django and the user profile.
 */
export async function login(email: string, password: string): Promise<AuthTokenResponse> {
  const { data } = await api.post<AuthTokenResponse>("/api/auth/login/", { email, password });
  if (!data.success) throw new Error(data.message ?? "Login failed");
  return data;
}

/**
 * Create a new account.
 * Returns a Supabase JWT issued by Django and the new user profile.
 */
export async function signup(
  email: string,
  password: string,
  password_confirm: string
): Promise<AuthTokenResponse> {
  const { data } = await api.post<AuthTokenResponse>("/api/auth/signup/", {
    email,
    password,
    password_confirm,
  });
  if (!data.success) throw new Error(data.message ?? "Signup failed");
  return data;
}

/** Sign out — Django invalidates the Supabase session server-side. */
export async function logout(): Promise<void> {
  await api.post("/api/auth/logout/");
}

// ----------------------------------------------------------------
// Brain / Documents
// ----------------------------------------------------------------
export async function processDocument(formData: FormData): Promise<ProcessDocumentResponse> {
  const { data } = await api.post<ProcessDocumentResponse>(
    "/api/brain/process/document/",
    formData,
    { headers: { "Content-Type": "multipart/form-data" } }
  );
  return data;
}

export async function getJobStatus(jobId: number): Promise<JobStatusResponse> {
  const { data } = await api.get<JobStatusResponse>(`/api/brain/jobs/${jobId}/status/`);
  return data;
}

export async function deleteJob(jobId: number): Promise<{ success: boolean }> {
  const { data } = await api.delete<{ success: boolean }>(`/api/brain/jobs/${jobId}/delete/`);
  return data;
}

export async function downloadResults(jobId: number): Promise<void> {
  window.open(`/api/brain/jobs/${jobId}/download/`, "_blank");
}

// ----------------------------------------------------------------
// Dashboard – Quizzes
// ----------------------------------------------------------------
export async function getMyQuizzes(): Promise<MyQuizzesResponse> {
  const { data } = await api.get<MyQuizzesResponse>("/api/dashboard/my-quizzes/");
  return data;
}

export async function getQuizResults(jobId: number): Promise<QuizResultsResponse> {
  const { data } = await api.get<QuizResultsResponse>(
    `/api/dashboard/quiz-results/${jobId}/?format=json`
  );
  return data;
}

// ----------------------------------------------------------------
// Dashboard – Exams
// ----------------------------------------------------------------
export async function startExam(jobId: number): Promise<StartExamResponse> {
  const { data } = await api.post<StartExamResponse>(
    `/api/dashboard/exam/start/${jobId}/`
  );
  return data;
}

export async function getExamSession(sessionId: string): Promise<ExamSessionResponse> {
  const { data } = await api.get<ExamSessionResponse>(
    `/api/dashboard/exam/session/${sessionId}/`
  );
  return data;
}

export async function answerQuestion(
  sessionId: string,
  answer: string,
  action: "next" | "previous" | "submit"
): Promise<AnswerResponse> {
  const { data } = await api.post<AnswerResponse>(
    `/api/dashboard/exam/answer/${sessionId}/`,
    { answer, action }
  );
  return data;
}

export async function submitExam(sessionId: string): Promise<SubmitExamResponse> {
  const { data } = await api.post<SubmitExamResponse>(
    `/api/dashboard/exam/submit/${sessionId}/`
  );
  return data;
}

export async function getExamResult(sessionId: string): Promise<ExamResultResponse> {
  const { data } = await api.get<ExamResultResponse>(
    `/api/dashboard/exam/result/${sessionId}/`
  );
  return data;
}

// ----------------------------------------------------------------
// Dashboard – Flashcards
// ----------------------------------------------------------------
export async function startFlashcard(jobId: number): Promise<StartFlashcardResponse> {
  const { data } = await api.post<StartFlashcardResponse>(
    `/api/dashboard/flashcard/start/${jobId}/`
  );
  return data;
}

export async function getFlashcardSession(sessionId: string): Promise<FlashcardSessionResponse> {
  const { data } = await api.get<FlashcardSessionResponse>(
    `/api/dashboard/flashcard/session/${sessionId}/`
  );
  return data;
}

export async function advanceFlashcard(
  sessionId: string,
  action: "next" | "skip"
): Promise<AdvanceFlashcardResponse> {
  const { data } = await api.post<AdvanceFlashcardResponse>(
    `/api/dashboard/flashcard/advance/${sessionId}/`,
    { action }
  );
  return data;
}

// ----------------------------------------------------------------
// Dashboard – Leaderboard
// ----------------------------------------------------------------
export async function getLeaderboard(
  filter: "all" | "week" | "month" | "year" = "all"
): Promise<LeaderboardResponse> {
  const { data } = await api.get<LeaderboardResponse>(
    `/api/dashboard/leaderboard/?filter=${filter}`
  );
  return data;
}
