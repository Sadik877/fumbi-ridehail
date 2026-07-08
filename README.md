# Fumbi — Ride-hailing & Delivery Web App

A production-quality, mobile-first ride-hailing and delivery platform built with **Flask, Jinja, Tailwind CSS, and vanilla JavaScript** — no React, no template kits.

## Quick start

```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

Visit `http://localhost:5000`.

## Project structure

```
ridehail/
├── app.py                     # Entry point
├── requirements.txt
└── app/
    ├── __init__.py             # App factory, blueprint registration, error handlers
    ├── config.py                # Config classes (dev/prod), env-driven secrets
    ├── mock_data.py             # Stand-in "database" — isolated so real models/queries
    │                             swap in without touching routes or templates
    ├── routes/
    │   ├── main.py               # Landing, About, Contact, FAQ
    │   ├── auth.py                # Login, Register, Driver registration
    │   ├── booking.py             # Ride/Delivery booking, history, fare estimate API
    │   └── dashboard.py            # Dashboard, Wallet, Notifications, Profile
    ├── templates/
    │   ├── base.html              # Design tokens, fonts, dark mode, Tailwind config
    │   ├── partials/               # navbar, mobile nav, footer, dashboard sidebar
    │   ├── auth/, booking/, dashboard/, errors/
    │   └── landing.html, about.html, contact.html, faq.html
    └── static/
        ├── css/main.css            # Keyframes, skeletons, signature "route-thread" motif
        └── js/                      # app.js (global), booking.js (booking flows)
```

## Design system

- **Typography** — Space Grotesk (display), Inter (body), IBM Plex Mono (data/prices)
- **Color** — Canopy green (primary), Ink (grayscale), Sand (warm neutral background)
- **Components** — buttons, cards, inputs, badges defined once in `base.html` via
  Tailwind's `@layer components`, so every page shares one source of truth
- **Signature motif** — the "route thread": a dashed line with a travelling pulse,
  used in the hero and as section dividers, echoing both a live GPS route and the
  stitched lines of African textile weaving
- **Dark mode** — class-based (`.dark`), toggled and persisted via `localStorage`
- **Motion** — scroll-reveal via `IntersectionObserver`, respects `prefers-reduced-motion`

## Notes on backend integration

Everything currently reads from `app/mock_data.py` and simulates network delay in
`static/js/booking.js`. To wire up a real backend:

1. Replace `mock_data.py` reads in `routes/*.py` with real queries (SQLAlchemy, an ORM, or an API client).
2. Replace `/book/estimate` with a real pricing/dispatch service call.
3. Add session/auth handling in `routes/auth.py` (the `# Placeholder` comments mark exactly where).
4. Swap the SVG map mock for a real maps SDK (Mapbox/Google Maps) — markup is isolated to one `<svg>` block per page for easy replacement.
