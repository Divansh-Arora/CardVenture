import { useState } from "react";
import { Link, useNavigate, useLocation } from "react-router-dom";
import { motion } from "framer-motion";
import { Eye, EyeOff, LogIn } from "lucide-react";
import { useAuth } from "../context/AuthContext";
import Mascot from "../components/Mascot";
import MadeByBadge from "../components/MadeByBadge";

export default function LoginPage() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPw, setShowPw] = useState(false);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  const submit = async (e) => {
    e.preventDefault();
    setError("");
    setBusy(true);
    try {
      await login(email.trim(), password);
      navigate(location.state?.from?.pathname || "/", { replace: true });
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center px-4 py-10 bg-sky bg-fixed">
      <motion.div
        initial={{ opacity: 0, y: 24 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5, ease: [0.16, 1, 0.3, 1] }}
        className="w-full max-w-md"
      >
        <div className="flex flex-col items-center mb-6 text-center">
          <Mascot mood="happy" size={92} />
          <h1 className="text-3xl font-display font-extrabold text-ink-900 mt-2">Cardventure</h1>
          <p className="text-ink-700 font-semibold mt-1">Welcome back, explorer!</p>
        </div>

        <form onSubmit={submit} className="card-surface p-6 sm:p-8 space-y-4">
          <label className="block">
            <span className="text-sm font-display font-bold text-ink-700 mb-1.5 block">
              Your email
            </span>
            <input
              type="email"
              className="field"
              placeholder="you@example.com"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              autoComplete="email"
              required
            />
          </label>

          <label className="block">
            <span className="text-sm font-display font-bold text-ink-700 mb-1.5 block">
              Your password
            </span>
            <div className="relative">
              <input
                type={showPw ? "text" : "password"}
                className="field pr-12"
                placeholder="••••••••"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                autoComplete="current-password"
                required
                minLength={8}
              />
              <button
                type="button"
                onClick={() => setShowPw((s) => !s)}
                className="absolute right-4 top-1/2 -translate-y-1/2 text-ink-700/50 hover:text-ink-900"
                aria-label={showPw ? "Hide password" : "Show password"}
              >
                {showPw ? <EyeOff size={18} /> : <Eye size={18} />}
              </button>
            </div>
          </label>

          {error && (
            <motion.p
              initial={{ opacity: 0, y: -4 }}
              animate={{ opacity: 1, y: 0 }}
              className="text-sm font-bold text-bubblegum bg-bubblegum/10 rounded-xl px-3 py-2"
            >
              {error}
            </motion.p>
          )}

          <button type="submit" className="btn-primary w-full !py-3.5 text-base" disabled={busy}>
            <LogIn size={18} />
            {busy ? "Logging you in…" : "Let's go!"}
          </button>
        </form>

        <p className="text-center text-sm font-semibold text-ink-700 mt-5">
          New here?{" "}
          <Link to="/register" className="text-bubblegum font-display font-extrabold hover:underline">
            Join the adventure
          </Link>
        </p>
      </motion.div>
      <MadeByBadge />
    </div>
  );
}
