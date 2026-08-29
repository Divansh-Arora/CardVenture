import { motion } from "framer-motion";

/**
 * A small original SVG fox mascot ("Pip") used throughout the app to keep
 * things feeling friendly rather than clinical. `mood` swaps expression:
 * - "happy": default, gentle smile, used almost everywhere
 * - "excited": open smile + sparkle eyes, used on success/celebration
 * - "sleepy": closed eyes, used on empty states / "nothing due" moments
 * - "thinking": tilted head, used while content is loading
 */
export default function Mascot({ mood = "happy", size = 96, floating = true, className = "" }) {
  const Wrapper = floating ? motion.div : "div";
  const wrapperProps = floating
    ? { className: "animate-bob", style: { width: size, height: size } }
    : { style: { width: size, height: size } };

  return (
    <Wrapper {...wrapperProps} className={`${floating ? "animate-bob" : ""} ${className}`}>
      <svg viewBox="0 0 120 120" width={size} height={size} role="img" aria-label="Pip the fox">
        {/* ears */}
        <path d="M28 40 L18 10 L46 28 Z" fill="#FF8A3D" />
        <path d="M92 40 L102 10 L74 28 Z" fill="#FF8A3D" />
        <path d="M30 38 L24 20 L42 30 Z" fill="#FFD7B0" />
        <path d="M90 38 L96 20 L78 30 Z" fill="#FFD7B0" />

        {/* head */}
        <ellipse cx="60" cy="62" rx="42" ry="38" fill="#FF8A3D" />
        <path d="M60 96 C44 96 34 84 34 72 C34 88 48 96 60 96 C72 96 86 88 86 72 C86 84 76 96 60 96 Z" fill="#FFF3E4" />
        <path d="M60 60 C48 60 41 70 46 84 C50 94 70 94 74 84 C79 70 72 60 60 60 Z" fill="#FFF3E4" />

        {/* eyes */}
        {mood === "sleepy" ? (
          <>
            <path d="M42 58 Q48 62 54 58" stroke="#2E2A4A" strokeWidth="3" fill="none" strokeLinecap="round" />
            <path d="M66 58 Q72 62 78 58" stroke="#2E2A4A" strokeWidth="3" fill="none" strokeLinecap="round" />
          </>
        ) : (
          <>
            <circle cx="48" cy="58" r={mood === "excited" ? 6 : 5} fill="#2E2A4A" />
            <circle cx="72" cy="58" r={mood === "excited" ? 6 : 5} fill="#2E2A4A" />
            <circle cx="50" cy="56" r="1.6" fill="#fff" />
            <circle cx="74" cy="56" r="1.6" fill="#fff" />
          </>
        )}

        {/* nose + mouth */}
        <ellipse cx="60" cy="74" rx="4.5" ry="3.5" fill="#2E2A4A" />
        {mood === "excited" ? (
          <path d="M48 78 Q60 92 72 78" stroke="#2E2A4A" strokeWidth="3" fill="none" strokeLinecap="round" />
        ) : (
          <path d="M52 80 Q60 86 68 80" stroke="#2E2A4A" strokeWidth="3" fill="none" strokeLinecap="round" />
        )}

        {/* cheeks */}
        <circle cx="38" cy="72" r="6" fill="#FF6FA5" opacity="0.5" />
        <circle cx="82" cy="72" r="6" fill="#FF6FA5" opacity="0.5" />

        {mood === "excited" && (
          <>
            <motion.g
              animate={{ opacity: [0.4, 1, 0.4], scale: [0.9, 1.15, 0.9] }}
              transition={{ repeat: Infinity, duration: 1.4 }}
            >
              <path d="M14 30 l3 7 7 3 -7 3 -3 7 -3 -7 -7 -3 7 -3 Z" fill="#FFC93C" />
            </motion.g>
            <motion.g
              animate={{ opacity: [0.4, 1, 0.4], scale: [1, 1.2, 1] }}
              transition={{ repeat: Infinity, duration: 1.6, delay: 0.3 }}
            >
              <path d="M104 46 l2.5 6 6 2.5 -6 2.5 -2.5 6 -2.5 -6 -6 -2.5 6 -2.5 Z" fill="#3EC6E0" />
            </motion.g>
          </>
        )}
      </svg>
    </Wrapper>
  );
}
