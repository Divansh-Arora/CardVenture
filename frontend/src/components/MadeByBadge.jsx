import { motion } from "framer-motion";
import { Heart } from "lucide-react";

/**
 * "variant" controls placement/sizing:
 * - "corner": small pill, fixed bottom-right, present on every screen
 * - "inline": bigger, used once in the dashboard footer
 */
export default function MadeByBadge({ variant = "corner" }) {
  if (variant === "inline") {
    return (
      <div className="flex flex-col items-center gap-2 py-10 text-center">
        <motion.div
          whileHover={{ rotate: [0, -6, 6, -3, 0] }}
          transition={{ duration: 0.5 }}
          className="inline-flex items-center gap-2 bg-white rounded-full px-5 py-2.5 shadow-pop-sm border-2 border-ink-900/10"
        >
          <span className="font-display font-bold text-ink-900 text-sm">
            Made with
          </span>
          <Heart size={16} className="fill-bubblegum text-bubblegum" />
          <span className="font-display font-bold text-ink-900 text-sm">
            by Divansh
          </span>
        </motion.div>
        <p className="text-xs text-ink-700/60 font-semibold">
          Cardventure · turning PDFs into learning adventures
        </p>
      </div>
    );
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: 0.6 }}
      whileHover={{ scale: 1.06, rotate: -2 }}
      className="fixed bottom-4 right-4 z-30 hidden sm:inline-flex items-center gap-1.5 bg-white/95 backdrop-blur border-2 border-ink-900/10 rounded-full pl-3 pr-3.5 py-1.5 shadow-pop-sm text-xs font-display font-bold text-ink-900"
    >
      <Heart size={12} className="fill-bubblegum text-bubblegum" />
      by Divansh
    </motion.div>
  );
}
