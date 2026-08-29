import { Link } from "react-router-dom";
import Mascot from "../components/Mascot";
import MadeByBadge from "../components/MadeByBadge";

export default function NotFoundPage() {
  return (
    <div className="min-h-screen flex items-center justify-center px-4 bg-sky bg-fixed">
      <div className="text-center">
        <Mascot mood="sleepy" size={120} />
        <h1 className="text-4xl font-display font-extrabold text-ink-900 mt-4">
          Uh-oh, lost trail!
        </h1>
        <p className="text-ink-700 font-semibold mt-2 max-w-sm mx-auto">
          We looked everywhere but couldn't find that page. Let's head back to safety.
        </p>
        <Link to="/" className="btn-primary mt-6 inline-flex">
          Take me home
        </Link>
      </div>
      <MadeByBadge />
    </div>
  );
}
