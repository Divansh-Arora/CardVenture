import { motion } from "framer-motion";

const SEGMENTS = [
  { key: "mastered", color: "#9B6BFF", label: "Superstar!" },
  { key: "upcoming", color: "#5FD36B", label: "Getting there" },
  { key: "shaky", color: "#FF6FA5", label: "Needs practice" },
];

export default function ProgressRing({ progress, size = 156 }) {
  const total = Math.max(progress?.total || 0, 1);
  const stroke = 16;
  const r = (size - stroke) / 2;
  const circumference = 2 * Math.PI * r;

  let offsetAcc = 0;
  const arcs = SEGMENTS.map((seg) => {
    const value = progress?.[seg.key] || 0;
    const fraction = value / total;
    const length = fraction * circumference;
    const arc = { ...seg, value, length, offset: offsetAcc };
    offsetAcc += length;
    return arc;
  });

  return (
    <div className="flex items-center gap-6 flex-wrap justify-center sm:justify-start">
      <div className="relative shrink-0" style={{ width: size, height: size }}>
        <svg width={size} height={size} className="-rotate-90">
          <circle cx={size / 2} cy={size / 2} r={r} fill="none" stroke="#FFF3D2" strokeWidth={stroke} />
          {arcs.map((arc, i) => (
            <motion.circle
              key={arc.key}
              cx={size / 2}
              cy={size / 2}
              r={r}
              fill="none"
              stroke={arc.color}
              strokeWidth={stroke}
              strokeLinecap="round"
              strokeDasharray={`${circumference} ${circumference}`}
              initial={{ strokeDashoffset: circumference }}
              animate={{ strokeDashoffset: circumference - arc.length }}
              transition={{ duration: 1, delay: 0.15 * i, ease: [0.16, 1, 0.3, 1] }}
              style={{ transform: `rotate(${(arc.offset / circumference) * 360}deg)`, transformOrigin: "50% 50%" }}
            />
          ))}
        </svg>
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <motion.span
            initial={{ opacity: 0, scale: 0.7 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: 0.5, type: "spring", stiffness: 260, damping: 14 }}
            className="font-display text-3xl font-extrabold text-ink-900"
          >
            {progress?.total || 0}
          </motion.span>
          <span className="text-[10px] font-display font-bold uppercase tracking-wider text-ink-700/60">
            cards
          </span>
        </div>
      </div>

      <div className="flex flex-col gap-2.5">
        {SEGMENTS.map((seg) => (
          <div key={seg.key} className="flex items-center gap-2">
            <span className="w-3 h-3 rounded-full" style={{ backgroundColor: seg.color }} />
            <span className="text-sm font-bold text-ink-700">{seg.label}</span>
            <span className="text-sm font-display font-extrabold text-ink-900 ml-auto pl-4">
              {progress?.[seg.key] || 0}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}
