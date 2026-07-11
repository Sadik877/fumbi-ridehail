# MoveX — Move Smarter. Deliver Faster.

Production-architecture ride-hailing and delivery platform for Nigeria/Africa,
built with **Flask, SQLAlchemy, Jinja, Tailwind CSS, and vanilla JavaScript.**

## What changed in this rebuild (from the earlier "Fumbi" prototype)

- **Fixed the Render deploy failure.** The root cause of `Failed to find
  attribute "app" in "app"` was a naming collision: a file `app.py` sitting
  next to a package directory `app/` is ambiguous to Python's import
  system. That root-level `app.py` is gone — `wsgi.py` is now the single,
  unambiguous entry point for both `flask run` and gunicorn.
- **Real database layer.** `mock_data.py` is gone. Every entity in the spec
  (Users, Passengers, Drivers, Businesses, Vehicles, RideBooking,
  DeliveryBooking, Trips, Wallet, Transactions, Notifications, Ratings,
  Reviews, PromoCodes, SupportTickets, SavedLocations, EmergencyContacts) is
  a real SQLAlchemy model in `app/models/`.
- **Real authentication.** Flask-Login sessions, Werkzeug password hashing,
  role-based accounts (passenger/driver/business/admin), email verification
  and password reset via signed, expiring tokens, CSRF protection on every
  form, and rate limiting on auth endpoints.
- **Four real dashboards**: passenger (`/dashboard`), driver (`/driver`),
  business (`/business`), and admin (`/admin`) — each gated by role.
- **OpenStreetMap integration** (`app/services/maps.py`): Nominatim
  geocoding + OSRM routing, with a haversine-distance fallback if the
  routing engine is unreachable.
- **REST API** (`/api/v1`) for the future Android/iOS apps, authenticated
  with JWT bearer tokens.
- **SEO/PWA basics**: robots.txt, sitemap.xml, Open Graph/Twitter meta,
  a web manifest, and a minimal service worker.

## Honest limitations — please read before treating this as "done"

- **Flutterwave/Paystack are not live.** `app/services/payments.py` contains
  real, correct client code against both providers' actual REST APIs — but
  a working payment flow needs a real merchant account and API keys that
  only you can obtain. Until then, wallet top-ups work via a manual/cash
  flow; card top-up buttons are wired to the real service functions and
  will work the moment you add `FLUTTERWAVE_SECRET_KEY` /
  `PAYSTACK_SECRET_KEY` to your environment.
- **Email is not actually sent anywhere yet.** `MAIL_SUPPRESS_SEND=true` by
  default, so verification/reset emails are logged instead of delivered.
  Set real SMTP credentials to turn this on — no code changes needed.
- **No database migration files are included.** I can't install
  Flask-Migrate/SQLAlchemy in this sandbox (no network access to PyPI), so
  I could not run `flask db migrate` to generate real, verified migration
  files — and I won't hand-write fake ones. Run the commands below once
  after installing dependencies; it's a one-time step.
- **I could not execute-test this app end-to-end.** The sandbox this was
  built in has no network access, so `pip install` fails for
  Flask-SQLAlchemy, Flask-Login, Flask-WTF, Flask-Limiter, and Flask-Mail.
  I syntax-checked every Python file (`py_compile`), and manually verified
  every template's `{% extends %}`/`{% include %}` targets exist, every
  `url_for()` matches a real registered route, and every POST form carries
  a CSRF token — but I have not seen this app boot and serve a page. Please
  run it locally before deploying and tell me what breaks; I'll fix it fast.
- **Admin/driver/business UI is functional, not exhaustively polished.**
  You get real CRUD (approve drivers, resolve tickets, manage coupons,
  accept/complete trips, bulk delivery, invoices, reports) — but it's one
  focused pass, not weeks of design iteration. Tell me which screen to
  refine first.
- **No file uploads yet.** Driver document upload (license, ID, insurance)
  is deferred to "after your account is created" in the UI rather than
  silently accepting files nothing processes — wiring real storage (e.g.
  S3-compatible bucket) is a clear next step.

## Getting started (local development)

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env          # then edit SECRET_KEY, etc.

flask --app wsgi db init       # first time only
flask --app wsgi db migrate -m "Initial schema"
flask --app wsgi db upgrade

flask --app wsgi seed-db       # vehicle pricing tiers + admin account
flask --app wsgi run --debug
```

Visit `http://localhost:5000`.

## Deploying to Render

1. Push this repo to GitHub/GitLab.
2. In Render, "New +" → "Blueprint" → point at this repo. `render.yaml`
   provisions a web service and a managed Postgres database automatically.
3. Render generates `SECRET_KEY`/`JWT_SECRET_KEY` for you. Manually set
   `ADMIN_EMAIL`, `ADMIN_PASSWORD`, and (when ready) the mail/payment keys
   in the dashboard — they're marked `sync: false` in `render.yaml` so
   Render prompts for them instead of committing them to source control.
4. The `preDeployCommand` runs `flask db upgrade` automatically on every
   deploy once migrations exist locally and are committed.

## Project structure

```
movex/
├── wsgi.py                  # Single entry point (gunicorn wsgi:app)
├── render.yaml, Procfile, runtime.txt, gunicorn_conf.py
├── requirements.txt
├── .env.example
└── app/
    ├── __init__.py            # App factory, extensions, blueprints, security headers
    ├── config.py               # Dev/Prod/Testing config, env-driven secrets
    ├── extensions.py            # db, migrate, login_manager, csrf, limiter, mail
    ├── content.py                # Static marketing copy (not app data)
    ├── forms.py                   # Flask-WTF forms (validation + CSRF)
    ├── seed.py                     # flask seed-db — vehicle tiers, admin, sample reviews
    ├── models/                      # SQLAlchemy models (see list above)
    ├── services/                     # maps.py, payments.py, pricing.py, wallet.py, email.py, notifications.py
    ├── utils/                         # decorators.py (role guards), jwt_auth.py (API auth)
    ├── routes/                         # main, auth, booking, dashboard, driver, business, admin, api, seo
    ├── templates/                       # Jinja templates, one folder per area
    └── static/                            # css/main.css, js/, manifest, service worker, images
```

## Design system

Emerald green / charcoal black / white, Inter for body text with Space
Grotesk for display headings, defined once in `templates/base.html` via
Tailwind's `@layer components` (buttons, cards, inputs, badges) so every
page shares one source of truth. Dark mode is class-based and persisted in
`localStorage`. The signature visual motif is the "route thread" — a
dashed, animated line used in the hero and as section dividers.
