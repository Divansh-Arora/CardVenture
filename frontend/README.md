# Cardventure 🦊✨

Turn any PDF into a fun, colorful flashcard adventure — built with React +
Vite for a FastAPI + spaced-repetition backend.

## What's in here

- **React 19 + Vite** — fast dev server, small production build
- **Tailwind CSS** — bright, kid-friendly "Cardventure" design system
  (see `tailwind.config.js` for the full color palette)
- **Framer Motion** — every interaction has a bouncy, springy animation:
  card flips, confetti bursts, sticker-style buttons that "press down"
- **React Router** — auth-gated routes (`/`, `/decks/:id`, `/decks/:id/study`)
- Fully responsive — works from a small phone up to a wide desktop screen

## Pages

| Route | What it does |
|---|---|
| `/login`, `/register` | Sign in / sign up |
| `/` | Dashboard — today's stats, deck grid, search, "New deck" upload |
| `/decks/:id` | Deck detail — progress ring, category mix, learning trail, card browser |
| `/decks/:id/study` | Study session — flip cards, rate with 4 big buttons or keys 1–4 |

## Running it locally

1. **Start the backend first** (see the backend's own README). By default
   it runs on `http://localhost:8000` and already allows requests from
   `http://localhost:5173` (Vite's default dev port) via CORS.

2. Install dependencies:
   ```bash
   npm install
   ```

3. Copy the env file and adjust if your backend runs somewhere else:
   ```bash
   cp .env.example .env
   ```
   ```
   VITE_API_URL=http://localhost:8000
   ```

4. Start the dev server:
   ```bash
   npm run dev
   ```
   Open the printed local URL (usually `http://localhost:5173`).

5. Register an account from the app, upload a PDF, and start studying!

## Building for production

```bash
npm run build   # outputs to dist/
npm run preview # serve the production build locally to sanity-check it
```

`VITE_API_URL` is baked in at build time — set it in your hosting
provider's environment variables (or in `.env.production`) before running
`npm run build` if the backend lives somewhere other than
`http://localhost:8000`.

## Design notes

- The color system, fonts (`Baloo 2` for headings, `Nunito` for body text),
  and animation tokens all live in `tailwind.config.js` — tweak them there
  to reskin the whole app at once.
- `src/lib/taxonomy.js` maps the backend's 7 card categories (definition,
  formula, relationship, method, worked_example, misconception, edge_case)
  to kid-friendly labels/colors/icons. The **keys** must stay in sync with
  the backend's `CardType` enum; only labels/colors are cosmetic.
- `src/components/Mascot.jsx` is an original SVG fox ("Pip") with a few
  moods (`happy`, `excited`, `sleepy`, `thinking`) reused across empty
  states, auth screens, and celebrations.

---

Made with 💛 by **Divansh**
