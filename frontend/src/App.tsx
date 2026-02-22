import { Routes, Route, Navigate } from "react-router-dom";
import ProtectedRoute from "@/layouts/ProtectedRoute";
import AuthLayout from "@/layouts/AuthLayout";
import DashboardLayout from "@/layouts/DashboardLayout";

import SignInPage from "@/pages/SignInPage";
import DashboardPage from "@/pages/DashboardPage";
import GiveExamPage from "@/pages/GiveExamPage";
import ExamPage from "@/pages/ExamPage";
import ExamResultPage from "@/pages/ExamResultPage";
import FlashcardPage from "@/pages/FlashcardPage";
import FlashcardCompletePage from "@/pages/FlashcardCompletePage";
import MyQuizzesPage from "@/pages/MyQuizzesPage";
import QuizResultsPage from "@/pages/QuizResultsPage";
import LeaderboardPage from "@/pages/LeaderboardPage";
import ProfilePage from "@/pages/ProfilePage";
import SettingsPage from "@/pages/SettingsPage";
import HelpPage from "@/pages/HelpPage";

export default function App() {
  return (
    <Routes>
      {/* Auth routes */}
      <Route element={<AuthLayout />}>
        <Route path="/signin" element={<SignInPage />} />
      </Route>

      {/* Protected dashboard routes */}
      <Route element={<ProtectedRoute />}>
        <Route element={<DashboardLayout />}>
          <Route path="/dashboard" element={<DashboardPage />} />
          <Route path="/give-exam" element={<GiveExamPage />} />
          <Route path="/exam/:sessionId" element={<ExamPage />} />
          <Route path="/exam/result/:sessionId" element={<ExamResultPage />} />
          <Route path="/flashcard/:sessionId" element={<FlashcardPage />} />
          <Route path="/flashcard/complete/:sessionId" element={<FlashcardCompletePage />} />
          <Route path="/my-quizzes" element={<MyQuizzesPage />} />
          <Route path="/quiz-results/:jobId" element={<QuizResultsPage />} />
          <Route path="/leaderboard" element={<LeaderboardPage />} />
          <Route path="/profile" element={<ProfilePage />} />
          <Route path="/settings" element={<SettingsPage />} />
          <Route path="/help" element={<HelpPage />} />
        </Route>
      </Route>

      {/* Redirect root to dashboard */}
      <Route path="/" element={<Navigate to="/dashboard" replace />} />

      {/* Catch-all redirect */}
      <Route path="*" element={<Navigate to="/dashboard" replace />} />
    </Routes>
  );
}
