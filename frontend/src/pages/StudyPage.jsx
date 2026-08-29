import { useEffect, useState, useCallback } from "react";
import { useParams, useNavigate, Link } from "react-router-dom";
import { motion, AnimatePresence } from "framer-motion";
import { X, ArrowLeft } from "lucide-react";
import { getDeck, getDueCards, submitReview } from "../lib/api";
import NavBar from "../components/NavBar";
import Mascot from "../components/Mascot";
import Loader from "../components/Loader";
import FlashCard from "../components/FlashCard";
import RatingBar from "../components/RatingBar";
import Confetti from "../components/Confetti";
import MadeByBadge from "../components/MadeByBadge";

const ENCOURAGEMENTS = [
  "You've got this! 🌟",
  "Keep going, superstar! ✨",
  "Nice work! 🎈",
  "Brain power, activate! 🧠",
  "Almost there! 🚀",
];

export default function StudyPage() {
  const { deckId } = useParams();
  const navigate = useNavigate();

  const [deckTitle, setDeckTitle] = useState("");
  const [queue, setQueue] = useState(null);
  const [index, setIndex] = useState(0);
  const [revealed, setRevealed] = useState(false);
  const [error, setError] = useState("");
  const [tally, setTally] = useState({ done: 0, correct: 0 });
  const [submitting, setSubmitting] = useState(false);
  const [burst, setBurst] = useState(false);

  const load = useCallback(async () => {
    try {
      const [deck, due] = await Promise.all([getDeck(deckId), getDueCards(deckId)]);
      setDeckTitle(deck.title);
      setQueue(due);
    } catch (err) {
      setError(err.message);
    }
  }, [deckId]);

  useEffect(() => {
    load();
  }, [load]);

  const currentCard = queue?.[index];
  const total = queue?.length || 0;
  const finished = queue !== null && index >= total;

  const rate = async (quality) => {
    if (!currentCard || submitting) return;
    setSubmitting(true);
    if (quality >= 4) {
      setBurst(true);
      setTimeout(() => setBurst(false), 900);
    }
    try {
      await submitReview(currentCard.id, quality);
      setTally((t) => ({ done: t.done + 1, correct: t.correct + (quality >= 3 ? 1 : 0) }));
      setRevealed(false);
      setTimeout(() => setIndex((i) => i + 1), 180);
    } catch (err) {
      setError(err.message);
    } finally {
      setSubmitting(false);
    }
  };

  // Keyboard shortcuts: space to reveal, 1-4 to rate.
  useEffect(() => {
    const onKey = (e) => {
      if (!currentCard || finished) return;
      if (e.code === "Space") {
        e.preventDefault();
        if (!revealed) setRevealed(true);
      } else if (revealed && ["1", "2", "3", "4"].includes(e.key)) {
        const map = { 1: 1, 2: 3, 3: 4, 4: 5 };
        rate(map[e.key]);
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [currentCard, revealed, finished, submitting]);

  if (error) {
    return (
      <div className="min-h-screen">
        <NavBar />
        <main className="max-w-lg mx-auto px-4 py-20 text-center">
          <Mascot mood="sleepy" size={90} />
          <p className="font-display font-bold text-lg mt-4">{error}</p>
          <Link to={`/decks/${deckId}`} className="btn-primary mt-5 inline-flex">
            Back to deck
          </Link>
        </main>
      </div>
    );
  }

  if (queue === null) {
    return (
      <div className="min-h-screen">
        <NavBar />
        <div className="py-24 flex justify-center">
          <Loader label="Lining up your cards…" />
        </div>
      </div>
    );
  }

  if (total === 0) {
    return (
      <div className="min-h-screen">
        <NavBar />
        <main className="max-w-lg mx-auto px-4 py-20 text-center">
          <Mascot mood="sleepy" size={110} />
          <h2 className="font-display font-extrabold text-2xl mt-4">Nothing to study right now!</h2>
          <p className="text-ink-700 font-semibold mt-2">
            Every card in "{deckTitle}" is resting. Come back later!
          </p>
          <Link to={`/decks/${deckId}`} className="btn-primary mt-6 inline-flex">
            <ArrowLeft size={16} />
            Back to deck
          </Link>
        </main>
      </div>
    );
  }

  if (finished) {
    const pct = tally.done ? Math.round((tally.correct / tally.done) * 100) : 0;
    return (
      <div className="min-h-screen relative overflow-hidden">
        <NavBar />
        <Confetti count={60} />
        <main className="max-w-lg mx-auto px-4 py-20 text-center relative">
          <Mascot mood="excited" size={130} />
          <h2 className="font-display font-extrabold text-3xl mt-4">Session complete! 🎉</h2>
          <p className="text-ink-700 font-bold mt-2">
            You reviewed {tally.done} {tally.done === 1 ? "card" : "cards"} — {pct}% felt right!
          </p>
          <div className="flex gap-3 justify-center mt-7">
            <Link to={`/decks/${deckId}`} className="btn-ghost">
              Back to deck
            </Link>
            <Link to="/" className="btn-primary">
              All decks
            </Link>
          </div>
        </main>
        <MadeByBadge />
      </div>
    );
  }

  return (
    <div className="min-h-screen relative">
      <header className="sticky top-0 z-40 bg-cream-100/85 backdrop-blur-md border-b-2 border-ink-900/5">
        <div className="max-w-3xl mx-auto px-4 sm:px-8 h-16 flex items-center justify-between gap-4">
          <button
            onClick={() => navigate(`/decks/${deckId}`)}
            className="text-ink-700 hover:text-ink-900"
            aria-label="Exit study session"
          >
            <X size={22} />
          </button>
          <div className="flex-1 max-w-xs">
            <div className="h-3 rounded-full bg-cream-200 overflow-hidden">
              <motion.div
                className="h-full rounded-full bg-gradient-to-r from-bubblegum via-sunshine to-grass"
                animate={{ width: `${(index / total) * 100}%` }}
                transition={{ duration: 0.4, ease: [0.16, 1, 0.3, 1] }}
              />
            </div>
          </div>
          <span className="text-sm font-display font-extrabold text-ink-900 shrink-0">
            {index + 1}/{total}
          </span>
        </div>
      </header>

      <main className="max-w-3xl mx-auto px-4 py-10 sm:py-16 flex flex-col items-center gap-8 relative">
        <AnimatePresence>{burst && <Confetti count={24} />}</AnimatePresence>

        <motion.p
          key={`enc-${index}`}
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="text-sm font-display font-bold text-grape"
        >
          {ENCOURAGEMENTS[index % ENCOURAGEMENTS.length]}
        </motion.p>

        <AnimatePresence mode="wait">
          <motion.div
            key={currentCard.id}
            initial={{ opacity: 0, x: 40 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -40 }}
            transition={{ duration: 0.3, ease: [0.16, 1, 0.3, 1] }}
            className="w-full"
          >
            <FlashCard card={currentCard} revealed={revealed} onReveal={() => setRevealed(true)} />
          </motion.div>
        </AnimatePresence>

        <RatingBar visible={revealed} onRate={rate} />
      </main>
      <MadeByBadge />
    </div>
  );
}
