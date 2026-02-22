import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { cn } from "@/utils";
import { login as apiLogin, signup as apiSignup, sendOtp, verifyOtp } from "@/services/api";
import { useAuth } from "@/contexts/AuthContext";
import { useToast } from "@/components/ui/ToastProvider";

type Mode = "login" | "signup";
type OtpStep = "idle" | "sent" | "verified";

/* ─── Page-level styles injected once ─────────────────────────── */
const PAGE_STYLE = `
  .sisimpur-bg {
    background-color: #0B0C15;
    font-family: 'Inter', sans-serif;
  }
  .bg-grid {
    background-size: 40px 40px;
    background-image:
      linear-gradient(to right,  rgba(255,255,255,0.05) 1px, transparent 1px),
      linear-gradient(to bottom, rgba(255,255,255,0.05) 1px, transparent 1px);
    mask-image: radial-gradient(circle at center, black, transparent 80%);
    -webkit-mask-image: radial-gradient(circle at center, black, transparent 80%);
  }
  .glass-card {
    background: rgba(22, 24, 34, 0.75);
    backdrop-filter: blur(14px);
    -webkit-backdrop-filter: blur(14px);
    border: 1px solid rgba(255,255,255,0.09);
    box-shadow: 0 8px 32px 0 rgba(0,0,0,0.45);
  }
  .text-glow { text-shadow: 0 0 20px rgba(124,58,237,0.5); }
  .logo-glow { filter: drop-shadow(0 0 10px rgba(6,182,212,0.4)); }
  .particle-blob {
    position: absolute;
    border-radius: 50%;
    filter: blur(40px);
    z-index: 0;
  }
  .top-bar-gradient {
    background: linear-gradient(to right, transparent, #7C3AED, transparent);
  }
`;

export default function SignInPage() {
  const [mode, setMode] = useState<Mode>("login");
  const [otpStep, setOtpStep] = useState<OtpStep>("idle");
  const [loading, setLoading] = useState(false);

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [passwordConfirm, setPasswordConfirm] = useState("");
  const [otp, setOtp] = useState("");

  const { login: storeAuth } = useAuth();
  const { toast } = useToast();
  const navigate = useNavigate();

  function switchMode(m: Mode) {
    setMode(m);
    setOtpStep("idle");
    setOtp("");
    setEmail("");
    setPassword("");
    setPasswordConfirm("");
  }

  /** Send OTP to email � Django calls Supabase Admin to generate + mail it */
  async function handleSendOtp() {
    if (!email) return toast("Enter your email first", "error");
    setLoading(true);
    try {
      await sendOtp(email);
      setOtpStep("sent");
      toast("OTP sent to your email", "success");
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : "Failed to send OTP";
      toast(msg, "error");
    } finally {
      setLoading(false);
    }
  }

  /** Verify OTP with Django */
  async function handleVerifyOtp() {
    if (!otp) return toast("Enter the OTP", "error");
    setLoading(true);
    try {
      await verifyOtp(email, otp);
      setOtpStep("verified");
      toast("Email verified!", "success");
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : "Invalid OTP";
      toast(msg, "error");
    } finally {
      setLoading(false);
    }
  }

  /**
   * Sign in via Django ? Supabase Admin SDK ? MongoDB metadata stored.
   * Django returns a Supabase JWT + user profile; we store it in localStorage.
   */
  async function handleLogin(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    try {
      const { token, user } = await apiLogin(email, password);
      storeAuth(token, user);
      navigate("/dashboard");
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : "Login failed";
      toast(msg, "error");
    } finally {
      setLoading(false);
    }
  }

  /**
   * Sign up via Django ? Supabase Admin SDK creates user ? metadata stored in MongoDB.
   * Django returns a Supabase JWT + user profile.
   */
  async function handleSignup(e: React.FormEvent) {
    e.preventDefault();
    if (otpStep !== "verified") return toast("Verify your email first", "error");
    if (password !== passwordConfirm) return toast("Passwords do not match", "error");
    setLoading(true);
    try {
      const { token, user } = await apiSignup(email, password, passwordConfirm);
      storeAuth(token, user);
      navigate("/dashboard");
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : "Signup failed";
      toast(msg, "error");
    } finally {
      setLoading(false);
    }
  }

  return (
    <>
      {/* Inject page-scoped styles */}
      <style>{PAGE_STYLE}</style>

      <div className="sisimpur-bg min-h-screen flex relative overflow-hidden text-gray-200">
        {/* Grid overlay */}
        <div className="absolute inset-0 z-0 bg-grid opacity-100 pointer-events-none" />

        {/* Particle blobs */}
        <div
          className="particle-blob opacity-40"
          style={{ width: 384, height: 384, background: "#7C3AED", top: -100, left: -100 }}
        />
        <div
          className="particle-blob opacity-20"
          style={{ width: 256, height: 256, background: "#06B6D4", bottom: -50, right: -50 }}
        />
        <div
          className="particle-blob opacity-20"
          style={{ width: 320, height: 320, background: "#581C87", top: "20%", right: "30%" }}
        />

        {/* -- Left Branding Panel --------------------------------------- */}
        <div className="hidden lg:flex w-1/2 min-h-screen flex-col justify-center px-16 xl:px-24 relative z-10 space-y-10">

            <div className="flex flex-col items-start text-left space-y-8">
              {/* Logo + Title */}
              <div className="flex items-center gap-4 mb-4">
                <div
                  className="w-16 h-16 rounded-2xl flex items-center justify-center shadow-lg logo-glow"
                  style={{
                    background: "linear-gradient(135deg, #7C3AED 0%, #5B21B6 100%)",
                    boxShadow: "0 10px 30px rgba(124,58,237,0.3)",
                  }}
                >
                  <svg
                    className="h-10 w-10 text-white"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                    xmlns="http://www.w3.org/2000/svg"
                  >
                    <path
                      d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253"
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth="2"
                    />
                  </svg>
                </div>
                <h1 className="text-5xl font-bold tracking-tight text-white">
                  <span style={{ color: "#06B6D4" }}>SIS</span>IMPUR
                </h1>
              </div>

              {/* Tagline + Quote */}
              <div className="space-y-6 max-w-lg">
                <h2 className="text-3xl lg:text-4xl font-semibold leading-tight text-gray-100">
                  Transform your study material into{" "}
                  <span style={{ color: "#7C3AED" }} className="text-glow">
                    mastery.
                  </span>
                </h2>

                <blockquote
                  className="relative pl-6 italic text-lg text-gray-400"
                  style={{ borderLeft: "4px solid rgba(124,58,237,0.5)" }}
                >
                  "Learning is not attained by chance, it must be sought for with ardor and attended to with diligence."
                  <footer className="mt-2 text-sm font-semibold not-italic" style={{ color: "#06B6D4" }}>
                    � Abigail Adams
                  </footer>
                </blockquote>

                {/* Animated dots */}
                <div className="flex gap-2 pt-4 justify-center lg:justify-start">
                  <div
                    className="w-2 h-2 rounded-full animate-bounce"
                    style={{ background: "#06B6D4", animationDelay: "0ms" }}
                  />
                  <div
                    className="w-2 h-2 rounded-full animate-bounce"
                    style={{ background: "#7C3AED", animationDelay: "150ms" }}
                  />
                  <div
                    className="w-2 h-2 rounded-full animate-bounce"
                    style={{ background: "#C084FC", animationDelay: "300ms" }}
                  />
                </div>
              </div>
            </div>

        </div>

        {/* Right Form Panel */}
        <div className="flex-1 flex items-center justify-center px-6 py-12 relative z-10">
          <div className="w-full max-w-[480px]">
              <div className="glass-card rounded-3xl p-8 shadow-2xl relative overflow-hidden">
                {/* Top gradient bar */}
                <div className="absolute top-0 left-0 w-full h-0.5 top-bar-gradient opacity-50" />

                {/* Card header */}
                <div className="mb-7 text-center">
                  <h3 className="text-2xl font-bold text-white mb-1.5">
                    {mode === "login" ? "Welcome Back" : "Create Account"}
                  </h3>
                  <p className="text-gray-400 text-sm">
                    {mode === "login"
                      ? "Please enter your details to sign in."
                      : "Join Sisimpur � it's free to get started."}
                  </p>
                </div>

                {/* ── LOGIN FORM ── */}
                {mode === "login" && (
                  <form onSubmit={handleLogin} className="space-y-5">
                    <FaInputField
                      icon="fa-envelope"
                      type="email"
                      id="email"
                      label="Email Address"
                      placeholder="you@example.com"
                      value={email}
                      onChange={setEmail}
                      autoComplete="email"
                    />
                    <FaInputField
                      icon="fa-lock"
                      type="password"
                      id="password"
                      label="Password"
                      placeholder="��������"
                      value={password}
                      onChange={setPassword}
                      autoComplete="current-password"
                      labelRight={
                        <button
                          type="button"
                          className="text-sm font-medium transition-colors"
                          style={{ color: "#06B6D4" }}
                          onMouseEnter={(e) => ((e.currentTarget as HTMLElement).style.color = "#67E8F9")}
                          onMouseLeave={(e) => ((e.currentTarget as HTMLElement).style.color = "#06B6D4")}
                        >
                          Forgot Password?
                        </button>
                      }
                    />
                    <PrimaryBtn loading={loading}>Sign In</PrimaryBtn>
                  </form>
                )}

                {/* ── SIGNUP FORM ── */}
                {mode === "signup" && (
                  <form onSubmit={handleSignup} className="space-y-4">
                    {/* Email row + Send OTP */}
                    <div>
                      <label className="block text-sm font-medium text-gray-300 mb-1.5 ml-1">
                        Email Address
                      </label>
                      <div className="flex gap-2">
                        <div className="relative flex-1">
                          <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                            <i className="fas fa-envelope text-gray-500 text-sm" />
                          </div>
                          <input
                            type="email"
                            placeholder="you@example.com"
                            value={email}
                            onChange={(e) => setEmail(e.target.value)}
                            autoComplete="email"
                            className="block w-full pl-10 pr-3 py-3 rounded-xl text-sm text-gray-100 placeholder-gray-500 outline-none transition-all"
                            style={{
                              background: "rgba(255,255,255,0.06)",
                              border: "1px solid rgba(255,255,255,0.12)",
                            }}
                            onFocus={(e) => {
                              e.currentTarget.style.border = "1px solid rgba(124,58,237,0.6)";
                              e.currentTarget.style.boxShadow = "0 0 0 3px rgba(124,58,237,0.12)";
                            }}
                            onBlur={(e) => {
                              e.currentTarget.style.border = "1px solid rgba(255,255,255,0.12)";
                              e.currentTarget.style.boxShadow = "none";
                            }}
                          />
                        </div>
                        <button
                          type="button"
                          onClick={handleSendOtp}
                          disabled={loading || otpStep === "verified"}
                          className={cn(
                            "flex-shrink-0 px-3.5 py-3 rounded-xl text-xs font-semibold transition-all border",
                            otpStep === "verified"
                              ? "bg-emerald-500/15 text-emerald-400 border-emerald-500/30 cursor-default"
                              : "bg-violet-600/20 text-violet-300 border-violet-500/30 hover:bg-violet-600/35 disabled:opacity-40"
                          )}
                        >
                          {otpStep === "verified" ? (
                            <span className="flex items-center gap-1">
                              <i className="fas fa-check" /> Done
                            </span>
                          ) : loading && otpStep === "idle" ? (
                            <i className="fas fa-spinner fa-spin" />
                          ) : (
                            "Send OTP"
                          )}
                        </button>
                      </div>
                    </div>

                    {/* OTP verify row */}
                    {otpStep === "sent" && (
                      <div className="flex gap-2">
                        <div className="relative flex-1">
                          <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                            <i className="fas fa-shield-halved text-gray-500 text-sm" />
                          </div>
                          <input
                            type="text"
                            placeholder="6-digit OTP"
                            value={otp}
                            onChange={(e) => setOtp(e.target.value)}
                            maxLength={6}
                            className="block w-full pl-10 pr-3 py-3 rounded-xl text-sm text-gray-100 placeholder-gray-500 outline-none transition-all"
                            style={{
                              background: "rgba(255,255,255,0.06)",
                              border: "1px solid rgba(255,255,255,0.12)",
                            }}
                            onFocus={(e) => {
                              e.currentTarget.style.border = "1px solid rgba(59,130,246,0.6)";
                              e.currentTarget.style.boxShadow = "0 0 0 3px rgba(59,130,246,0.12)";
                            }}
                            onBlur={(e) => {
                              e.currentTarget.style.border = "1px solid rgba(255,255,255,0.12)";
                              e.currentTarget.style.boxShadow = "none";
                            }}
                          />
                        </div>
                        <button
                          type="button"
                          onClick={handleVerifyOtp}
                          disabled={loading}
                          className="flex-shrink-0 px-3.5 py-3 rounded-xl text-xs font-semibold border bg-blue-600/20 text-blue-300 border-blue-500/30 hover:bg-blue-600/35 transition disabled:opacity-40"
                        >
                          Verify
                        </button>
                      </div>
                    )}

                    <FaInputField
                      icon="fa-lock"
                      type="password"
                      id="password"
                      label="Password"
                      placeholder="��������"
                      value={password}
                      onChange={setPassword}
                      autoComplete="new-password"
                    />
                    <FaInputField
                      icon="fa-lock"
                      type="password"
                      id="password_confirm"
                      label="Confirm Password"
                      placeholder="��������"
                      value={passwordConfirm}
                      onChange={setPasswordConfirm}
                      autoComplete="new-password"
                    />

                    {otpStep !== "verified" && (
                      <p className="text-xs text-amber-400/70 flex items-center gap-1.5">
                        <i className="fas fa-circle-info" />
                        Verify your email before creating account
                      </p>
                    )}

                    <PrimaryBtn loading={loading} disabled={otpStep !== "verified"}>
                      Create Account
                    </PrimaryBtn>
                  </form>
                )}

                {/* OR divider */}
                <div className="relative py-4 mt-1">
                  <div className="absolute inset-0 flex items-center">
                    <div className="w-full border-t border-gray-700" />
                  </div>
                  <div className="relative flex justify-center text-sm">
                    <span
                      className="px-2 text-gray-500"
                      style={{ background: "rgba(22,24,34,0.9)" }}
                    >
                      Or continue with
                    </span>
                  </div>
                </div>

                {/* Google OAuth */}
                <a
                  href="/api/auth/google/login/"
                  className="w-full flex justify-center items-center py-3 px-4 rounded-xl text-sm font-medium text-gray-200 transition-colors duration-200"
                  style={{
                    background: "rgba(255,255,255,0.05)",
                    border: "1px solid rgba(255,255,255,0.12)",
                  }}
                  onMouseEnter={(e) =>
                    ((e.currentTarget as HTMLElement).style.background = "rgba(255,255,255,0.09)")
                  }
                  onMouseLeave={(e) =>
                    ((e.currentTarget as HTMLElement).style.background = "rgba(255,255,255,0.05)")
                  }
                >
                  <svg aria-hidden="true" className="h-5 w-5 mr-2" viewBox="0 0 24 24">
                    <path
                      d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
                      fill="#4285F4"
                    />
                    <path
                      d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
                      fill="#34A853"
                    />
                    <path
                      d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"
                      fill="#FBBC05"
                    />
                    <path
                      d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"
                      fill="#EA4335"
                    />
                  </svg>
                  Sign in with Google
                </a>

                {/* Switch mode link */}
                <div className="mt-7 text-center">
                  <p className="text-sm text-gray-500">
                    {mode === "login" ? "Don't have an account? " : "Already have an account? "}
                    <button
                      type="button"
                      onClick={() => switchMode(mode === "login" ? "signup" : "login")}
                      className="font-medium transition-colors"
                      style={{ color: "#7C3AED" }}
                      onMouseEnter={(e) =>
                        ((e.currentTarget as HTMLElement).style.color = "#A78BFA")
                      }
                      onMouseLeave={(e) =>
                        ((e.currentTarget as HTMLElement).style.color = "#7C3AED")
                      }
                    >
                      {mode === "login" ? "Create an account" : "Sign in"}
                    </button>
                  </p>
                </div>
              </div>
            </div>
          </div>

        {/* Footer */}
        <div className="absolute bottom-4 left-0 w-full text-center pointer-events-none">
          <p className="text-xs text-gray-600">&copy; 2025 SISIMPUR. All rights reserved.</p>
        </div>
      </div>
    </>
  );
}

/* ── Font-Awesome-based labeled input field ──────────────────────── */

function FaInputField({
  icon,
  type,
  id,
  label,
  placeholder,
  value,
  onChange,
  autoComplete,
  labelRight,
}: {
  icon: string;
  type: string;
  id: string;
  label: string;
  placeholder: string;
  value: string;
  onChange: (v: string) => void;
  autoComplete?: string;
  labelRight?: React.ReactNode;
}) {
  return (
    <div>
      <div className="flex items-center justify-between mb-1.5 ml-1">
        <label htmlFor={id} className="block text-sm font-medium text-gray-300">
          {label}
        </label>
        {labelRight}
      </div>
      <div className="relative">
        <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
          <i className={`fas ${icon} text-gray-500 text-sm`} />
        </div>
        <input
          id={id}
          type={type}
          placeholder={placeholder}
          value={value}
          onChange={(e) => onChange(e.target.value)}
          autoComplete={autoComplete}
          required
          className="block w-full pl-10 pr-3 py-3 rounded-xl text-sm text-gray-100 placeholder-gray-500 outline-none transition-all"
          style={{
            background: "rgba(255,255,255,0.06)",
            border: "1px solid rgba(255,255,255,0.12)",
          }}
          onFocus={(e) => {
            e.currentTarget.style.border = "1px solid rgba(124,58,237,0.6)";
            e.currentTarget.style.boxShadow = "0 0 0 3px rgba(124,58,237,0.12)";
          }}
          onBlur={(e) => {
            e.currentTarget.style.border = "1px solid rgba(255,255,255,0.12)";
            e.currentTarget.style.boxShadow = "none";
          }}
        />
      </div>
    </div>
  );
}

/* ── Primary Submit Button ──────────────────────────────────────── */

function PrimaryBtn({
  loading,
  disabled,
  children,
}: {
  loading: boolean;
  disabled?: boolean;
  children: React.ReactNode;
}) {
  return (
    <button
      type="submit"
      disabled={loading || disabled}
      className={cn(
        "w-full flex justify-center py-3.5 px-4 rounded-xl text-sm font-semibold text-white transition-all duration-200",
        "hover:-translate-y-0.5 focus:outline-none focus:ring-2 focus:ring-violet-600 focus:ring-offset-2 focus:ring-offset-gray-900",
        "disabled:opacity-40 disabled:cursor-not-allowed disabled:hover:translate-y-0"
      )}
      style={{
        background: loading || disabled ? "#7C3AED" : "linear-gradient(to right, #7C3AED, #6D28D9)",
        boxShadow: loading || disabled ? "none" : "0 4px 20px rgba(124,58,237,0.4)",
      }}
    >
      {loading ? (
        <span className="flex items-center gap-2">
          <i className="fas fa-spinner fa-spin" /> Processing...
        </span>
      ) : (
        children
      )}
    </button>
  );
}
