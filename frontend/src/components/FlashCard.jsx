import { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { cardTypeMeta, difficultyMeta } from "../lib/taxonomy";

export default function FlashCard({ card, revealed, onReveal }) {
  const meta = cardTypeMeta(card.card_type);
  const diff = difficultyMeta(card.difficulty);
  const Icon = meta.icon;
  const [internalFlip, setInternalFlip] = useState(false);

  useEffect(() => setInternalFlip(revealed), [revealed, card.id]);

  return (
    <div className="w-full max-w-2xl mx-auto" style={{ perspective: 1600 }}>
      <motion.div
        role="button"
        tabIndex={0}
        aria-label={revealed ? "Card answer shown" : "Tap to see the answer"}
        onClick={() => !revealed && onReveal()}
        onKeyDown={(e) => {
          if ((e.key === "Enter" || e.key === " ") && !revealed) {
            e.preventDefault();
            onReveal();
          }
        }}
        className="relative w-full min-h-[320px] sm:min-h-[400px] cursor-pointer select-none"
        style={{ transformStyle: "preserve-3d" }}
        animate={{ rotateY: internalFlip ? 180 : 0 }}
        transition={{ duration: 0.55, ease: [0.34, 1.2, 0.4, 1] }}
        whileHover={{ scale: revealed ? 1 : 1.015 }}
      >
        {/* Front — question */}
        <div
          className="absolute inset-0 rounded-5xl card-surface p-7 sm:p-10 flex flex-col border-4"
          style={{ backfaceVisibility: "hidden", borderColor: meta.color + "55" }}
        >
          <CardHeader meta={meta} Icon={Icon} diff={diff} card={card} />
          <div className="flex-1 flex items-center justify-center text-center px-2">
            <p className="font-display text-xl sm:text-3xl leading-snug text-ink-900 font-bold">
              {card.question}
            </p>
          </div>
          <p className="text-center text-xs sm:text-sm font-display font-bold text-ink-700/50 tracking-wide">
            👉 Tap the card (or press Space) to peek!
          </p>
        </div>

        {/* Back — answer */}
        <div
          className="absolute inset-0 rounded-5xl p-7 sm:p-10 flex flex-col border-4"
          style={{
            backfaceVisibility: "hidden",
            transform: "rotateY(180deg)",
            background: "linear-gradient(160deg, #E5F9E6 0%, #FFFFFF 100%)",
            borderColor: "#5FD36B",
          }}
        >
          <CardHeader meta={meta} Icon={Icon} diff={diff} card={card} />
          <div className="flex-1 flex flex-col items-center justify-center text-center gap-4 px-2">
            <span className="text-3xl">🎉</span>
            <p className="font-display text-lg sm:text-2xl leading-snug text-grass font-extrabold">
              {card.answer}
            </p>
            <AnimatePresence>
              {card.explanation && (
                <motion.p
                  initial={{ opacity: 0, y: 6 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.15 }}
                  className="text-sm sm:text-base text-ink-700 font-semibold max-w-md"
                >
                  {card.explanation}
                </motion.p>
              )}
            </AnimatePresence>
          </div>
          {card.source_page && (
            <p className="text-center text-xs font-bold text-ink-700/50">
              📖 From page {card.source_page}
            </p>
          )}
        </div>
      </motion.div>
    </div>
  );
}

function CardHeader({ meta, Icon, diff, card }) {
  return (
    <div className="flex items-center justify-between mb-4 flex-wrap gap-2">
      <span
        className="inline-flex items-center gap-1.5 text-[11px] sm:text-xs font-display font-bold uppercase tracking-wide px-3 py-1.5 rounded-full"
        style={{ backgroundColor: meta.dim, color: meta.color }}
      >
        <Icon size={13} />
        {meta.label}
      </span>
      <div className="flex items-center gap-2">
        {card.topic && (
          <span className="hidden sm:inline text-[11px] font-bold text-ink-700/60">
            {card.topic}
          </span>
        )}
        <span
          className="text-[11px] sm:text-xs font-display font-bold uppercase tracking-wide px-2.5 py-1.5 rounded-full border-2"
          style={{ borderColor: `${diff.color}66`, color: diff.color }}
        >
          {diff.label}
        </span>
      </div>
    </div>
  );
}
