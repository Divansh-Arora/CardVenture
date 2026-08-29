import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import { Eye, EyeOff, Sparkles } from "lucide-react";
import { useAuth } from "../context/AuthContext";
import Mascot from "../components/Mascot";
import MadeByBadge from "../components/MadeByBadge";

export default function RegisterPage() {
  const { register } = useAuth();
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPw, setShowPw] = useState(false);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  const submit = async (e) => {
    e.preventDefault();
    setError("");
    if (password.length < 8) {
      setError("Your password needs at least 8 characters — pick something you'll remember!");
      return;
    }
    setBusy(true);
    try {
      await register(email.trim(), password);
      navigate("/", { replace: true });
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
          <Mascot mood="excited" size={92} />
          <h1 className="text-3xl font-display font-extrabold text-ink-900 mt-2">Cardventure</h1>
          <p className="text-ink-700 font-semibold mt-1">Let's start your learning adventure!</p>
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
              Pick a password
            </span>
            <div className="relative">
              <input
                type={showPw ? "text" : "password"}
                className="field pr-12"
                placeholder="At least 8 characters"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                autoComplete="new-password"
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

          <button type="submit" className="btn-pink w-full !py-3.5 text-base" disabled={busy}>
            <Sparkles size={18} />
            {busy ? "Setting things up…" : "Join the fun!"}
          </button>
        </form>

        <p className="text-center text-sm font-semibold text-ink-700 mt-5">
          Already have an account?{" "}
          <Link to="/login" className="text-sky font-display font-extrabold hover:underline">
            Log back in
          </Link>
        </p>
      </motion.div>
      <MadeByBadge />
    </div>
  );
}
