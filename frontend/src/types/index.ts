// ============================================================
// TypeScript types matching the Django API responses
// ============================================================

export interface User {
  id: string | number; // string UUID from Supabase, number from legacy Django auth
  username: string;
  email: string;
  first_name: string;
  last_name: string;
  full_name?: string;
}

export interface AuthState {
  user: User | null;
  isLoading: boolean;
  isAuthenticated: boolean;
}

// ------------------------------------------------------------
// Brain / Processing Jobs
// ------------------------------------------------------------
export type JobStatus = "pending" | "processing" | "completed" | "failed";
export type QuestionType = "MULTIPLECHOICE" | "SHORT";
export type Language = "auto" | "english" | "bengali";

export interface ProcessingJob {
  id: number;
  original_filename: string;
  status: JobStatus;
  language: Language;
  question_type: QuestionType;
  num_questions: number;
  created_at: string;
  completed_at: string | null;
  latest_exam_session_id: string | null;
  error_message?: string;
  document_name?: string;
}

export interface ProcessDocumentResponse {
  success: boolean;
  job_id: number;
  qa_count: number;
  message: string;
}

export interface JobStatusResponse {
  success: boolean;
  job_id: number;
  status: JobStatus;
  qa_count?: number;
  error?: string;
}

// ------------------------------------------------------------
// Questions & Quizzes
// ------------------------------------------------------------
export interface QAPair {
  id?: number;
  question: string;
  answer: string;
  question_type: QuestionType;
  options?: Record<string, string>;
  correct_option?: string;
  confidence_score?: number;
}

export interface QuizResultsResponse {
  success: boolean;
  job_id: number;
  questions_generated: number;
  qa_pairs: QAPair[];
  form_settings: {
    selected_language: string;
    selected_question_type: string;
    selected_num_questions: number;
    selected_language_display: string;
    selected_question_type_display: string;
  };
  detected_values: {
    detected_language: string;
    detected_language_display: string;
    detected_document_type: string;
    detected_is_question_paper: boolean;
    file_size?: number;
    file_extension?: string;
  };
  generated_values: {
    generated_num_questions: number;
    generated_question_types: string[];
    processing_status: string;
    processing_time?: number;
  };
}

export interface MyQuizzesResponse {
  success: boolean;
  jobs: ProcessingJob[];
}

// ------------------------------------------------------------
// Exam Session
// ------------------------------------------------------------
export interface StartExamResponse {
  success: boolean;
  session_id: string;
  error?: string;
}

export interface ExamQuestion {
  id: number;
  question: string;
  question_type: QuestionType;
  options?: Record<string, string>;
}

export interface ExamSessionResponse {
  success: boolean;
  session_status: "active" | "completed" | "expired";
  current_index: number;
  total_questions: number;
  question: ExamQuestion;
  existing_answer: string | null;
  remaining_time: number;
  can_go_back: boolean;
  can_go_next: boolean;
  is_last_question: boolean;
  error?: string;
  status?: string;
}

export interface AnswerResponse {
  success: boolean;
  current_index: number;
  completed: boolean;
  error?: string;
}

export interface ExamAnswerItem {
  question_index: number;
  question: string;
  question_type: QuestionType;
  user_answer: string;
  correct_answer: string;
  is_correct: boolean;
}

export interface ShortAnswerEval {
  question_index: number;
  score: number;
  max_score: number;
  feedback: string;
  accuracy_score: number;
  completeness_score: number;
  clarity_score: number;
}

export interface ExamResultResponse {
  success: boolean;
  session_id: string;
  status: string;
  total_questions: number;
  answered_questions: number;
  correct_answers: number;
  incorrect_answers: number;
  percentage_score: number;
  answers: ExamAnswerItem[];
  short_answer_evaluations: ShortAnswerEval[];
  error?: string;
}

// ------------------------------------------------------------
// Flashcards
// ------------------------------------------------------------
export interface FlashcardItem {
  id: number;
  question: string;
  answer: string;
  question_type: QuestionType;
}

export interface FlashcardSessionResponse {
  success: boolean;
  current_index: number;
  total_cards: number;
  progress_percentage: number;
  is_last_card: boolean;
  card: FlashcardItem;
  error?: string;
  status?: string;
}

export interface StartFlashcardResponse {
  success: boolean;
  session_id: string;
  error?: string;
}

export interface AdvanceFlashcardResponse {
  success: boolean;
  completed: boolean;
  current_index: number;
  error?: string;
}

// ------------------------------------------------------------
// Leaderboard
// ------------------------------------------------------------
export interface LeaderboardEntry {
  rank: number;
  username: string;
  full_name: string;
  total_score: number;
  total_exams: number;
  avg_percentage: number;
  total_credit_points: number;
  is_current_user: boolean;
}

export interface LeaderboardResponse {
  success: boolean;
  leaderboard: LeaderboardEntry[];
  current_user_rank: number | null;
  filter: string;
}

// ------------------------------------------------------------
// OTP / Auth
// ------------------------------------------------------------
export interface OtpResponse {
  success: boolean;
  message: string;
}

/** Returned by Django /api/auth/login/ and /api/auth/signup/ */
export interface AuthTokenResponse {
  success: boolean;
  message?: string;
  token: string;       // Supabase JWT issued by Django backend
  user: User;
}

export interface SubmitExamResponse {
  success: boolean;
  session_id: string;
  error?: string;
}
