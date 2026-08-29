import { motion } from "framer-motion";
import { cardTypeMeta } from "../lib/taxonomy";
import { daysUntil, horizonLabel } from "../lib/time";

// Maps a days-until value onto a 0..1 position along the trail, with a
// square-root curve so "ready now / coming up soon" cards (the ones that
// matter most) get proportionally more visual room than the long tail of
// cards a kid has already mastered, drifting months into the future.
function positionFor(days) {
  const clamped = Math.max(days, -1);
  const t = Math.sqrt(Math.min(clamped, 180) / 180);
  return Math.min(Math.max(t, 0), 1);
}

function colorFor(days) {
  if (days <= 0) return "#FF6FA5";
  if (days < 3) return "#FF8A3D";
  if (days < 14) return "#FFC93C";
  if (days < 45) return "#5FD36B";
  return "#9B6BFF";
}

export default function HorizonStrip({ cards, onSelectCard, maxDots = 60 }) {
  const sample = cards.slice(0, maxDots);

  return (
    <div className="card-surface p-5 sm:p-7">
      <div className="flex items-center justify-between mb-6 flex-wrap gap-3">
        <div>
          <p className="label-eyebrow">Your Trail</p>
          <h3 className="text-lg font-display font-bold mt-0.5">Every card's next stop!</h3>
        </div>
        <div className="hidden sm:flex items-center gap-3 text-[11px] font-bold text-ink-700">
          <LegendDot color="#FF6FA5" label="ready" />
          <LegendDot color="#FFC93C" label="soon" />
          <LegendDot color="#5FD36B" label="learning" />
          <LegendDot color="#9B6BFF" label="mastered" />
        </div>
      </div>

      <div className="relative h-20">
        {/* base path */}
        <div className="absolute left-0 right-0 top-1/2 -translate-y-1/2 h-1.5 rounded-full bg-gradient-to-r from-bubblegum/30 via-sunshine/30 to-grape/30" />

        {sample.map((card, i) => {
          const days = daysUntil(card.next_review_date);
          const left = `${positionFor(days) * 96 + 2}%`;
          const meta = cardTypeMeta(card.card_type);
          const isDue = days <= 0;

          return (
            <motion.button
              key={card.id}
              type="button"
              onClick={() => onSelectCard?.(card)}
              title={`${card.question} — ${horizonLabel(card.next_review_date)}`}
              className="group absolute top-1/2 -translate-y-1/2 -translate-x-1/2 outline-none"
              style={{ left }}
              initial={{ opacity: 0, y: 10, scale: 0.6 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              transition={{ delay: Math.min(i * 0.015, 0.5), duration: 0.45, ease: [0.34, 1.56, 0.64, 1] }}
              whileHover={{ scale: 1.7, zIndex: 10 }}
            >
              <span
                className={`block rounded-full border-2 border-white ${isDue ? "animate-wiggle" : ""}`}
                style={{
                  width: 14,
                  height: 14,
                  backgroundColor: colorFor(days),
                  boxShadow: `0 2px 0 rgba(46,42,74,0.15)`,
                }}
              />
              <span className="pointer-events-none absolute left-1/2 -translate-x-1/2 -top-10 whitespace-nowrap rounded-xl bg-ink-900 px-2.5 py-1.5 text-[10px] font-bold text-white opacity-0 group-hover:opacity-100 transition-opacity shadow-pop-sm">
                <meta.icon size={10} className="inline mr-1 -mt-0.5" style={{ color: meta.color }} />
                {horizonLabel(card.next_review_date)}
              </span>
            </motion.button>
          );
        })}
      </div>

      <div className="flex justify-between mt-3 text-[10px] sm:text-xs font-display font-bold text-ink-700/70 uppercase tracking-wide">
        <span>Now</span>
        <span>1 week</span>
        <span>1 month</span>
        <span>6mo+</span>
      </div>
    </div>
  );
}

function LegendDot({ color, label }) {
  return (
    <span className="flex items-center gap-1.5">
      <span className="w-2 h-2 rounded-full" style={{ backgroundColor: color }} />
      {label}
    </span>
  );
}
