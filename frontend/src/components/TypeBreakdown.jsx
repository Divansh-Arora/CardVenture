import { motion } from "framer-motion";
import { CARD_TYPE_ORDER, cardTypeMeta } from "../lib/taxonomy";

export default function TypeBreakdown({ breakdown }) {
  const counts = Object.fromEntries((breakdown || []).map((b) => [b.card_type, b.count]));
  const max = Math.max(1, ...Object.values(counts));

  return (
    <div className="card-surface p-5 sm:p-7">
      <p className="label-eyebrow">What's Inside</p>
      <h3 className="text-lg font-display font-bold mt-0.5 mb-5">Card mix</h3>

      <div className="space-y-4">
        {CARD_TYPE_ORDER.map((type, i) => {
          const meta = cardTypeMeta(type);
          const count = counts[type] || 0;
          const width = count === 0 ? 0 : Math.max((count / max) * 100, 6);
          const Icon = meta.icon;

          return (
            <div key={type} className="flex items-center gap-3">
              <div className="w-32 sm:w-40 flex items-center gap-1.5 shrink-0 text-xs sm:text-sm font-bold text-ink-700">
                <span
                  className="w-6 h-6 rounded-lg flex items-center justify-center shrink-0"
                  style={{ backgroundColor: meta.dim }}
                >
                  <Icon size={13} style={{ color: meta.color }} />
                </span>
                <span className="truncate">{meta.label}</span>
              </div>
              <div className="flex-1 h-3 rounded-full bg-cream-200 overflow-hidden">
                <motion.div
                  className="h-full rounded-full"
                  style={{ backgroundColor: meta.color }}
                  initial={{ width: 0 }}
                  animate={{ width: `${width}%` }}
                  transition={{ duration: 0.7, delay: i * 0.05, ease: [0.16, 1, 0.3, 1] }}
                />
              </div>
              <span className="w-6 text-right text-sm font-display font-extrabold text-ink-900 shrink-0">
                {count}
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
}
