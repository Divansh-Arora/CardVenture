import { motion, AnimatePresence } from "framer-motion";

const RATINGS = [
  { quality: 1, label: "Oops!", emoji: "😅", hint: "1", color: "#FF6FA5" },
  { quality: 3, label: "Tricky", emoji: "🤔", hint: "2", color: "#FF8A3D" },
  { quality: 4, label: "Got it!", emoji: "😊", hint: "3", color: "#5FD36B" },
  { quality: 5, label: "Easy!", emoji: "🤩", hint: "4", color: "#9B6BFF" },
];

export default function RatingBar({ visible, onRate }) {
  return (
    <AnimatePresence>
      {visible && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: 20 }}
          transition={{ duration: 0.3, ease: [0.16, 1, 0.3, 1] }}
          className="grid grid-cols-2 sm:grid-cols-4 gap-2.5 sm:gap-3 w-full max-w-2xl mx-auto"
        >
          {RATINGS.map((r) => (
            <motion.button
              key={r.quality}
              onClick={() => onRate(r.quality)}
              whileHover={{ y: -4, scale: 1.03 }}
              whileTap={{ scale: 0.94, y: 2 }}
              className="rounded-2xl border-2 py-3.5 flex flex-col items-center gap-1 font-display font-bold shadow-pop-sm active:shadow-none active:translate-y-1 transition-shadow"
              style={{
                borderColor: `${r.color}55`,
                backgroundColor: `${r.color}18`,
                color: r.color,
              }}
            >
              <span className="text-xl">{r.emoji}</span>
              <span className="text-sm">{r.label}</span>
              <span className="text-[10px] font-bold opacity-50">key {r.hint}</span>
            </motion.button>
          ))}
        </motion.div>
      )}
    </AnimatePresence>
  );
}

export { RATINGS };
