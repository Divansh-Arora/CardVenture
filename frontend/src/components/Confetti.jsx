import { motion } from "framer-motion";

const COLORS = ["#FF6FA5", "#FFC93C", "#3EC6E0", "#5FD36B", "#9B6BFF", "#FF8A3D"];

function pieces(count) {
  return Array.from({ length: count }, (_, i) => ({
    id: i,
    x: (Math.random() - 0.5) * 320,
    rotate: Math.random() * 360,
    delay: Math.random() * 0.15,
    color: COLORS[i % COLORS.length],
    size: 6 + Math.random() * 6,
    shape: Math.random() > 0.5 ? "circle" : "square",
  }));
}

export default function Confetti({ count = 26 }) {
  const bits = pieces(count);
  return (
    <div className="pointer-events-none absolute inset-0 overflow-hidden">
      {bits.map((p) => (
        <motion.span
          key={p.id}
          className="absolute left-1/2 top-1/3"
          style={{
            width: p.size,
            height: p.size,
            backgroundColor: p.color,
            borderRadius: p.shape === "circle" ? "50%" : "3px",
          }}
          initial={{ x: 0, y: 0, opacity: 1, rotate: 0 }}
          animate={{ x: p.x, y: 160 + Math.random() * 80, opacity: 0, rotate: p.rotate }}
          transition={{ duration: 1.1, delay: p.delay, ease: "easeOut" }}
        />
      ))}
    </div>
  );
}
