import { useEffect, useState, useCallback } from "react";
import { Link } from "react-router-dom";
import { motion, AnimatePresence } from "framer-motion";
import { Plus, Search, Flame, Target, Trophy, BookOpen } from "lucide-react";
import { listDecks, getTodayAnalytics, deleteDeck } from "../lib/api";
import { formatDate } from "../lib/time";
import { useAuth } from "../context/AuthContext";
import NavBar from "../components/NavBar";
import Mascot from "../components/Mascot";
import Loader from "../components/Loader";
import UploadDeckModal from "../components/UploadDeckModal";
import MadeByBadge from "../components/MadeByBadge";
import Confetti from "../components/Confetti";

export default function DashboardPage() {
  const { user } = useAuth();
  const [decks, setDecks] = useState(null);
  const [stats, setStats] = useState(null);
  const [query, setQuery] = useState("");
  const [sort, setSort] = useState("recent");
  const [uploadOpen, setUploadOpen] = useState(false);
  const [error, setError] = useState("");
  const [celebrate, setCelebrate] = useState(false);

  const load = useCallback(async (opts = {}) => {
    try {
      const [d, s] = await Promise.all([
        listDecks({ q: opts.q ?? query, sort: opts.sort ?? sort }),
        getTodayAnalytics(),
      ]);
      setDecks(d);
      setStats(s);
    } catch (err) {
      setError(err.message);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    const t = setTimeout(() => load({ q: query, sort }), 300);
    return () => clearTimeout(t);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [query, sort]);

  const handleUploaded = (deck) => {
    setUploadOpen(false);
    setCelebrate(true);
    setTimeout(() => setCelebrate(false), 1300);
    load();
    // Nudge the new deck to the top visually by resetting sort/search.
    setQuery("");
    setSort("recent");
  };

  const handleDelete = async (deckId, title) => {
    if (!window.confirm(`Remove "${title}"? This can't be undone.`)) return;
    try {
      await deleteDeck(deckId);
      setDecks((prev) => prev.filter((d) => d.id !== deckId));
    } catch (err) {
      setError(err.message);
    }
  };

  const firstName = user?.email?.split("@")[0] || "explorer";

  return (
    <div className="min-h-screen">
      <NavBar />

      <main className="max-w-6xl mx-auto px-4 sm:px-8 py-8 sm:py-12 relative">
        <AnimatePresence>{celebrate && <Confetti count={40} />}</AnimatePresence>

        {/* Hero */}
        <motion.div
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.45 }}
          className="flex flex-col sm:flex-row sm:items-center justify-between gap-6 mb-8"
        >
          <div className="flex items-center gap-4">
            <Mascot mood="happy" size={72} />
            <div>
              <h1 className="text-2xl sm:text-3xl font-display font-extrabold text-ink-900 capitalize">
                Hey {firstName}! 👋
              </h1>
              <p className="text-ink-700 font-semibold mt-0.5">Ready for today's adventure?</p>
            </div>
          </div>
          <motion.button
            whileHover={{ y: -3 }}
            whileTap={{ scale: 0.96, y: 2 }}
            onClick={() => setUploadOpen(true)}
            className="btn-pink !py-4 !px-6 text-base self-start sm:self-auto"
          >
            <Plus size={20} />
            New deck
          </motion.button>
        </motion.div>

        {/* Today stats */}
        {stats && (
          <motion.div
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.45, delay: 0.05 }}
            className="grid grid-cols-2 sm:grid-cols-4 gap-3 sm:gap-4 mb-8"
          >
            <StatChip icon={Flame} color="#FF6FA5" label="Reviews today" value={stats.reviews_today} />
            <StatChip icon={Target} color="#5FD36B" label="Accuracy" value={`${Math.round(stats.accuracy_pct)}%`} />
            <StatChip icon={Trophy} color="#9B6BFF" label="Mastered" value={stats.cards_mastered} />
            <StatChip icon={BookOpen} color="#3EC6E0" label="Total cards" value={stats.total_cards} />
          </motion.div>
        )}

        {/* Search + sort */}
        <div className="flex flex-col sm:flex-row gap-3 mb-6">
          <div className="relative flex-1">
            <Search size={18} className="absolute left-4 top-1/2 -translate-y-1/2 text-ink-700/40" />
            <input
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Search your decks…"
              className="field pl-11"
            />
          </div>
          <div className="flex gap-2 bg-white rounded-2xl border-2 border-ink-900/10 p-1.5 shrink-0">
            <SortButton active={sort === "recent"} onClick={() => setSort("recent")}>
              Newest
            </SortButton>
            <SortButton active={sort === "last_studied"} onClick={() => setSort("last_studied")}>
              Continue
            </SortButton>
          </div>
        </div>

        {error && (
          <p className="text-sm font-bold text-bubblegum bg-bubblegum/10 rounded-xl px-4 py-3 mb-6">
            {error}
          </p>
        )}

        {/* Deck grid */}
        {decks === null ? (
          <div className="py-20 flex justify-center">
            <Loader label="Fetching your decks…" />
          </div>
        ) : decks.length === 0 ? (
          <EmptyState hasQuery={!!query} onUpload={() => setUploadOpen(true)} />
        ) : (
          <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4 sm:gap-5">
            <AnimatePresence>
              {decks.map((deck, i) => (
                <DeckCard key={deck.id} deck={deck} index={i} onDelete={handleDelete} />
              ))}
            </AnimatePresence>
          </div>
        )}

        <MadeByBadge variant="inline" />
      </main>

      <UploadDeckModal open={uploadOpen} onClose={() => setUploadOpen(false)} onUploaded={handleUploaded} />
      <MadeByBadge />
    </div>
  );
}

function StatChip({ icon: Icon, color, label, value }) {
  return (
    <div className="card-surface p-4 flex items-center gap-3">
      <span
        className="w-10 h-10 rounded-xl flex items-center justify-center shrink-0"
        style={{ backgroundColor: `${color}22` }}
      >
        <Icon size={18} style={{ color }} />
      </span>
      <div className="min-w-0">
        <p className="text-lg font-display font-extrabold text-ink-900 leading-none">{value}</p>
        <p className="text-[11px] sm:text-xs font-bold text-ink-700/60 truncate">{label}</p>
      </div>
    </div>
  );
}

function SortButton({ active, onClick, children }) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={`px-3 sm:px-4 py-2 rounded-xl text-xs sm:text-sm font-display font-bold transition-colors ${
        active ? "bg-sunshine text-ink-900" : "text-ink-700/60 hover:text-ink-900"
      }`}
    >
      {children}
    </button>
  );
}

function DeckCard({ deck, index, onDelete }) {
  return (
    <motion.div
      layout
      initial={{ opacity: 0, y: 20, scale: 0.95 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      exit={{ opacity: 0, scale: 0.9 }}
      transition={{ duration: 0.35, delay: Math.min(index * 0.05, 0.3), ease: [0.16, 1, 0.3, 1] }}
      whileHover={{ y: -4 }}
      className="card-surface p-5 flex flex-col relative group"
    >
      <button
        onClick={(e) => {
          e.preventDefault();
          onDelete(deck.id, deck.title);
        }}
        className="absolute top-3 right-3 text-ink-700/30 hover:text-bubblegum text-xs font-bold opacity-0 group-hover:opacity-100 transition-opacity"
        aria-label={`Delete ${deck.title}`}
      >
        Remove
      </button>

      <Link to={`/decks/${deck.id}`} className="flex-1 flex flex-col">
        <div className="flex items-center gap-2 mb-3">
          <span className="text-2xl">📚</span>
          <span className="text-[11px] font-display font-bold text-ink-700/50 uppercase tracking-wide">
            {deck.card_count} {deck.card_count === 1 ? "card" : "cards"}
          </span>
        </div>
        <h3 className="font-display font-extrabold text-lg text-ink-900 leading-snug mb-2 line-clamp-2">
          {deck.title}
        </h3>
        <p className="text-xs font-semibold text-ink-700/50 mt-auto pt-3">
          {deck.last_studied_at
            ? `Last studied ${formatDate(deck.last_studied_at)}`
            : `Created ${formatDate(deck.created_at)}`}
        </p>
      </Link>
    </motion.div>
  );
}

function EmptyState({ hasQuery, onUpload }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      className="card-surface py-16 px-6 flex flex-col items-center text-center"
    >
      <Mascot mood="sleepy" size={100} />
      {hasQuery ? (
        <>
          <h3 className="font-display font-extrabold text-xl text-ink-900 mt-4">No decks match that search</h3>
          <p className="text-ink-700 font-semibold mt-1">Try a different word, or clear your search.</p>
        </>
      ) : (
        <>
          <h3 className="font-display font-extrabold text-xl text-ink-900 mt-4">
            No decks yet — let's fix that!
          </h3>
          <p className="text-ink-700 font-semibold mt-1 max-w-sm">
            Upload any PDF and Cardventure will turn it into a set of fun flashcards for you.
          </p>
          <button onClick={onUpload} className="btn-primary mt-5">
            <Plus size={18} />
            Create your first deck
          </button>
        </>
      )}
    </motion.div>
  );
}
