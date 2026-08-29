import { NavLink, useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import { LogOut } from "lucide-react";
import { useAuth } from "../context/AuthContext";
import Mascot from "./Mascot";

export default function NavBar() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  return (
    <header className="sticky top-0 z-40 bg-cream-100/85 backdrop-blur-md border-b-2 border-ink-900/5">
      <div className="max-w-6xl mx-auto px-4 sm:px-8 h-16 sm:h-20 flex items-center justify-between">
        <NavLink to="/" className="flex items-center gap-2 sm:gap-3 group">
          <motion.div whileHover={{ rotate: [0, -8, 8, 0] }} transition={{ duration: 0.5 }}>
            <Mascot size={38} floating={false} />
          </motion.div>
          <span className="font-display font-extrabold text-xl sm:text-2xl tracking-tight text-ink-900">
            Cardventure
          </span>
        </NavLink>

        <div className="flex items-center gap-2 sm:gap-3">
          {user && (
            <div className="hidden md:flex items-center gap-2 mr-1 px-3 py-1.5 rounded-full bg-white border-2 border-ink-900/10">
              <span className="w-2 h-2 rounded-full bg-grass" />
              <span className="text-xs font-bold text-ink-700">{user.email}</span>
            </div>
          )}
          <button
            onClick={() => {
              logout();
              navigate("/login");
            }}
            className="btn-ghost !px-3 !py-2 !text-xs sm:!text-sm"
            aria-label="Log out"
          >
            <LogOut size={14} />
            <span className="hidden sm:inline">Bye for now!</span>
          </button>
        </div>
      </div>
    </header>
  );
}
