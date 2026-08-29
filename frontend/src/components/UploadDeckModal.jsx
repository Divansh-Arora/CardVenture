import { useCallback, useRef, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { FileText, UploadCloud, X, Loader2 } from "lucide-react";
import { uploadDeck } from "../lib/api";
import Mascot from "./Mascot";

export default function UploadDeckModal({ open, onClose, onUploaded }) {
  const [title, setTitle] = useState("");
  const [file, setFile] = useState(null);
  const [dragging, setDragging] = useState(false);
  const [progress, setProgress] = useState(0);
  const [phase, setPhase] = useState("idle"); // idle | uploading | generating
  const [error, setError] = useState("");
  const inputRef = useRef(null);

  const reset = () => {
    setTitle("");
    setFile(null);
    setProgress(0);
    setPhase("idle");
    setError("");
  };

  const close = () => {
    if (phase === "uploading" || phase === "generating") return; // don't interrupt the magic
    reset();
    onClose();
  };

  const pickFile = (f) => {
    if (!f) return;
    if (f.type !== "application/pdf") {
      setError("Oops — that's not a PDF! Please pick a .pdf file.");
      return;
    }
    setError("");
    setFile(f);
    if (!title) setTitle(f.name.replace(/\.pdf$/i, ""));
  };

  const onDrop = useCallback((e) => {
    e.preventDefault();
    setDragging(false);
    pickFile(e.dataTransfer.files?.[0]);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [title]);

  const submit = async (e) => {
    e.preventDefault();
    if (!file || !title.trim()) return;
    setError("");
    setPhase("uploading");
    try {
      const deck = await uploadDeck(title.trim(), file, (pct) => {
        setProgress(pct);
        if (pct >= 100) setPhase("generating");
      });
      reset();
      onUploaded(deck);
    } catch (err) {
      setPhase("idle");
      setError(err.message);
    }
  };

  const busy = phase === "uploading" || phase === "generating";

  return (
    <AnimatePresence>
      {open && (
        <motion.div
          className="fixed inset-0 z-50 flex items-center justify-center p-4"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
        >
          <motion.div
            className="absolute inset-0 bg-ink-900/60 backdrop-blur-sm"
            onClick={close}
          />

          <motion.form
            onSubmit={submit}
            initial={{ opacity: 0, y: 30, scale: 0.95 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 16, scale: 0.97 }}
            transition={{ duration: 0.35, ease: [0.34, 1.2, 0.4, 1] }}
            className="relative w-full max-w-lg card-surface p-6 sm:p-8"
          >
            <div className="flex items-start justify-between mb-5">
              <div className="flex items-center gap-3">
                <Mascot mood="excited" size={48} floating={false} />
                <div>
                  <p className="label-eyebrow">New Adventure</p>
                  <h2 className="text-lg sm:text-xl font-display font-extrabold mt-0.5">
                    Turn a PDF into flashcards!
                  </h2>
                </div>
              </div>
              <button
                type="button"
                onClick={close}
                className="text-ink-700/50 hover:text-ink-900 transition-colors disabled:opacity-30 shrink-0"
                disabled={busy}
                aria-label="Close"
              >
                <X size={20} />
              </button>
            </div>

            <label className="block mb-4">
              <span className="text-sm font-display font-bold text-ink-700 mb-1.5 block">
                What should we call this deck?
              </span>
              <input
                className="field"
                placeholder="e.g. Dinosaurs & Fossils 🦕"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                disabled={busy}
                required
              />
            </label>

            <div
              onDragOver={(e) => {
                e.preventDefault();
                setDragging(true);
              }}
              onDragLeave={() => setDragging(false)}
              onDrop={onDrop}
              onClick={() => !busy && inputRef.current?.click()}
              className={`rounded-4xl border-4 border-dashed p-8 flex flex-col items-center justify-center text-center cursor-pointer transition-colors ${
                dragging ? "border-bubblegum bg-bubblegum/5" : "border-ink-900/15 hover:border-sky"
              } ${busy ? "pointer-events-none opacity-70" : ""}`}
            >
              <input
                ref={inputRef}
                type="file"
                accept="application/pdf"
                className="hidden"
                onChange={(e) => pickFile(e.target.files?.[0])}
              />
              {file ? (
                <>
                  <FileText size={32} className="text-grass mb-2" />
                  <p className="text-sm font-bold text-ink-900 truncate max-w-full">{file.name}</p>
                  <p className="text-xs text-ink-700/50 mt-0.5 font-semibold">
                    {(file.size / 1024 / 1024).toFixed(1)} MB
                  </p>
                </>
              ) : (
                <>
                  <UploadCloud size={32} className="text-sky mb-2" />
                  <p className="text-sm sm:text-base font-bold text-ink-900">
                    Drop a PDF here, or click to browse
                  </p>
                  <p className="text-xs text-ink-700/50 mt-1 font-semibold">
                    Notes, chapters, worksheets — anything!
                  </p>
                </>
              )}
            </div>

            {error && <p className="text-sm font-bold text-bubblegum mt-3">{error}</p>}

            <AnimatePresence>
              {busy && (
                <motion.div
                  initial={{ opacity: 0, height: 0 }}
                  animate={{ opacity: 1, height: "auto" }}
                  exit={{ opacity: 0, height: 0 }}
                  className="mt-4 overflow-hidden"
                >
                  <div className="flex items-center gap-2 text-xs sm:text-sm font-bold text-ink-700 mb-1.5">
                    <Loader2 size={14} className="animate-spin" />
                    {phase === "uploading" ? `Uploading… ${progress}%` : "Sprinkling magic on your flashcards…"}
                  </div>
                  <div className="h-2.5 rounded-full bg-cream-200 overflow-hidden">
                    <motion.div
                      className="h-full bg-gradient-to-r from-bubblegum via-sunshine to-grass rounded-full"
                      initial={{ width: 0 }}
                      animate={{ width: phase === "uploading" ? `${progress}%` : "100%" }}
                      transition={phase === "generating" ? { duration: 6, ease: "easeOut" } : { duration: 0.2 }}
                    />
                  </div>
                  {phase === "generating" && (
                    <p className="text-[11px] sm:text-xs text-ink-700/50 mt-2 font-semibold">
                      This can take a minute for longer documents. Hang tight!
                    </p>
                  )}
                </motion.div>
              )}
            </AnimatePresence>

            <div className="flex justify-end gap-3 mt-6">
              <button type="button" onClick={close} className="btn-ghost" disabled={busy}>
                Cancel
              </button>
              <button type="submit" className="btn-pink" disabled={busy || !file || !title.trim()}>
                {busy ? "Working…" : "Let's go! 🚀"}
              </button>
            </div>
          </motion.form>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
