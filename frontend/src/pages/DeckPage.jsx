import { useEffect, useState, useCallback } from "react";
import { useParams, useNavigate, Link } from "react-router-dom";
import { motion, AnimatePresence } from "framer-motion";
import { ArrowLeft, Search, Play, X } from "lucide-react";
import {
  getDeck,
  getDeckProgress,
  getDeckBreakdown,
  searchDeckCards,
} from "../lib/api";
import { cardTypeMeta, difficultyMeta } from "../lib/taxonomy";
import NavBar from "../components/NavBar";
import Mascot from "../components/Mascot";
import Loader from "../components/Loader";
import ProgressRing from "../components/ProgressRing";
import TypeBreakdown from "../components/TypeBreakdown";
import HorizonStrip from "../components/HorizonStrip";
import MadeByBadge from "../components/MadeByBadge";

export default function DeckPage() {
  const { deckId } = useParams();
  const navigate = useNavigate();

  const [deck, setDeck] = useState(null);
  const [progress, setProgress] = useState(null);
  const [breakdown, setBreakdown] = useState(null);
  const [error, setError] = useState("");

  const [query, setQuery] = useState("");
  const [searchResults, setSearchResults] = useState(null);
  const [peekCard, setPeekCard] = useState(null);

  const load = useCallback(async () => {
    try {
      const [d, p, b] = await Promise.all([
        getDeck(deckId),
        getDeckProgress(deckId),
        getDeckBreakdown(deckId),
      ]);
      setDeck(d);
      setProgress(p);
      setBreakdown(b);
    } catch (err) {
      setError(err.message);
    }
  }, [deckId]);

  useEffect(() => {
    load();
  }, [load]);

  useEffect(() => {
    if (!query.trim()) {
      setSearchResults(null);
      return;
    }
    const t = setTimeout(async () => {
      try {
        const results = await searchDeckCards(deckId, query.trim());
        setSearchResults(results);
      } catch {
        setSearchResults([]);
      }
    }, 300);
    return () => clearTimeout(t);
  }, [query, deckId]);

  if (error) {
    return (
      <div className="min-h-screen">
        <NavBar />
        <main className="max-w-3xl mx-auto px-4 py-16 text-center">
          <Mascot mood="sleepy" size={96} />
          <h2 className="font-display font-extrabold text-xl mt-4">Hmm, couldn't find that deck</h2>
          <p className="text-ink-700 font-semibold mt-1">{error}</p>
          <Link to="/" className="btn-primary mt-5 inline-flex">
            Back to your decks
          </Link>
        </main>
      </div>
    );
  }

  if (!deck) {
    return (
      <div className="min-h-screen">
        <NavBar />
        <div className="py-24 flex justify-center">
          <Loader label="Opening your deck…" />
        </div>
      </div>
    );
  }

  const dueCount = progress ? progress.shaky + progress.upcoming : 0;
  const displayedCards = searchResults !== null ? searchResults : deck.cards;

  return (
    <div className="min-h-screen">
      <NavBar />
      <main className="max-w-6xl mx-auto px-4 sm:px-8 py-8 sm:py-12">
        <button
          onClick={() => navigate("/")}
          className="inline-flex items-center gap-1.5 text-sm font-display font-bold text-ink-700 hover:text-ink-900 mb-6"
        >
          <ArrowLeft size={16} />
          All decks
        </button>

        <motion.div
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          className="flex flex-col lg:flex-row lg:items-end justify-between gap-6 mb-8"
        >
          <div className="flex items-start gap-4">
            <span className="text-5xl">📚</span>
            <div>
              <h1 className="text-2xl sm:text-3xl font-display font-extrabold text-ink-900">
                {deck.title}
              </h1>
              <p className="text-ink-700 font-semibold mt-1">
                {deck.card_count} {deck.card_count === 1 ? "card" : "cards"} in this deck
              </p>
            </div>
          </div>

          <motion.button
            whileHover={{ y: -3 }}
            whileTap={{ scale: 0.96 }}
            disabled={dueCount === 0}
            onClick={() => navigate(`/decks/${deckId}/study`)}
            className="btn-pink !py-4 !px-7 text-base shrink-0 self-start lg:self-auto"
          >
            <Play size={18} />
            {dueCount === 0 ? "All caught up!" : `Study now (${dueCount})`}
          </motion.button>
        </motion.div>

        <div className="grid lg:grid-cols-2 gap-5 mb-6">
          <motion.div
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.05 }}
            className="card-surface p-5 sm:p-7 flex items-center justify-center"
          >
            {progress && <ProgressRing progress={progress} />}
          </motion.div>
          <motion.div initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 }}>
            {breakdown && <TypeBreakdown breakdown={breakdown} />}
          </motion.div>
        </div>

        {deck.cards?.length > 0 && (
          <motion.div initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.15 }} className="mb-6">
            <HorizonStrip cards={deck.cards} onSelectCard={setPeekCard} />
          </motion.div>
        )}

        {/* Card search / browse */}
        <motion.div initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.2 }} className="card-surface p-5 sm:p-7">
          <div className="flex items-center justify-between mb-4 flex-wrap gap-3">
            <div>
              <p className="label-eyebrow">Browse</p>
              <h3 className="text-lg font-display font-bold mt-0.5">Peek at any card</h3>
            </div>
            <div className="relative w-full sm:w-64">
              <Search size={16} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-ink-700/40" />
              <input
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="Search this deck…"
                className="field !py-2.5 pl-9 text-sm"
              />
            </div>
          </div>

          {searchResults !== null && searchResults.length === 0 ? (
            <p className="text-sm font-semibold text-ink-700/60 py-6 text-center">
              No cards match "{query}" — try another word!
            </p>
          ) : (
            <div className="grid sm:grid-cols-2 gap-3">
              {displayedCards?.slice(0, 20).map((card) => (
                <CardRow key={card.id} card={card} onClick={() => setPeekCard(card)} />
              ))}
            </div>
          )}
          {displayedCards?.length > 20 && (
            <p className="text-xs font-semibold text-ink-700/50 text-center mt-4">
              +{displayedCards.length - 20} more — search to narrow it down
            </p>
          )}
        </motion.div>

        <MadeByBadge variant="inline" />
      </main>

      <CardPeekModal card={peekCard} onClose={() => setPeekCard(null)} />
      <MadeByBadge />
    </div>
  );
}

function CardRow({ card, onClick }) {
  const meta = cardTypeMeta(card.card_type);
  const Icon = meta.icon;
  return (
    <button
      onClick={onClick}
      className="text-left rounded-2xl border-2 border-ink-900/8 hover:border-sky bg-white p-4 transition-colors"
    >
      <span
        className="inline-flex items-center gap-1 text-[10px] font-display font-bold uppercase px-2 py-0.5 rounded-full mb-2"
        style={{ backgroundColor: meta.dim, color: meta.color }}
      >
        <Icon size={10} />
        {meta.label}
      </span>
      <p className="text-sm font-bold text-ink-900 line-clamp-2">{card.question}</p>
    </button>
  );
}

function CardPeekModal({ card, onClose }) {
  if (!card) return null;
  const meta = cardTypeMeta(card.card_type);
  const diff = difficultyMeta(card.difficulty);
  const Icon = meta.icon;

  return (
    <AnimatePresence>
      {card && (
        <motion.div
          className="fixed inset-0 z-50 flex items-center justify-center p-4"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
        >
          <motion.div className="absolute inset-0 bg-ink-900/60 backdrop-blur-sm" onClick={onClose} />
          <motion.div
            initial={{ opacity: 0, y: 24, scale: 0.95 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 12, scale: 0.97 }}
            transition={{ duration: 0.3, ease: [0.34, 1.2, 0.4, 1] }}
            className="relative w-full max-w-lg card-surface p-6 sm:p-8"
          >
            <button
              onClick={onClose}
              className="absolute top-4 right-4 text-ink-700/50 hover:text-ink-900"
              aria-label="Close"
            >
              <X size={20} />
            </button>
            <span
              className="inline-flex items-center gap-1.5 text-xs font-display font-bold uppercase px-3 py-1.5 rounded-full mb-4"
              style={{ backgroundColor: meta.dim, color: meta.color }}
            >
              <Icon size={13} />
              {meta.label}
            </span>
            <p className="font-display text-xl font-bold text-ink-900 mb-4">{card.question}</p>
            <div className="rounded-2xl bg-grass/10 border-2 border-grass/30 p-4 mb-3">
              <p className="font-display font-extrabold text-grass">{card.answer}</p>
            </div>
            {card.explanation && (
              <p className="text-sm font-semibold text-ink-700">{card.explanation}</p>
            )}
            <div className="flex items-center gap-2 mt-4">
              <span
                className="text-[11px] font-display font-bold uppercase px-2.5 py-1 rounded-full border-2"
                style={{ borderColor: `${diff.color}66`, color: diff.color }}
              >
                {diff.label}
              </span>
              {card.source_page && (
                <span className="text-[11px] font-bold text-ink-700/50">📖 Page {card.source_page}</span>
              )}
            </div>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
