import { Navigate, useLocation } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import Mascot from "./Mascot";
import Loader from "./Loader";

export default function ProtectedRoute({ children }) {
  const { isAuthed, initializing } = useAuth();
  const location = useLocation();

  if (initializing) {
    return (
      <div className="min-h-screen flex flex-col items-center justify-center gap-4 bg-sky bg-fixed">
        <Mascot mood="thinking" size={80} />
        <Loader label="Getting your adventure ready…" />
      </div>
    );
  }

  if (!isAuthed) {
    return <Navigate to="/login" replace state={{ from: location }} />;
  }

  return children;
}
