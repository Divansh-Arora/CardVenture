import { motion } from "framer-motion";

const DOT_COLORS = ["#FF6FA5", "#FFC93C", "#3EC6E0"];

export default function Loader({ label = "One sec…", size = "md" }) {
  const dot = size === "sm" ? 8 : size === "lg" ? 16 : 12;
  return (
    <div className="flex flex-col items-center gap-3 text-ink-700">
      <div className="flex items-end gap-1.5" style={{ height: dot * 2 }}>
        {DOT_COLORS.map((color, i) => (
          <motion.span
            key={color}
            className="rounded-full"
            style={{ width: dot, height: dot, backgroundColor: color }}
            animate={{ y: [0, -dot * 1.4, 0] }}
            transition={{ repeat: Infinity, duration: 0.9, delay: i * 0.15, ease: "easeInOut" }}
          />
        ))}
      </div>
      {label && <span className="font-display font-semibold text-sm">{label}</span>}
    </div>
  );
}
