"""
WSGI entry point — the single source of truth for both local development
and production.

Why this file (and not a root-level app.py):
Having a file named app.py sitting next to a package directory named app/
in the same folder is ambiguous to Python's import system — which is
exactly what caused the "Failed to find attribute 'app' in 'app'" error on
Render. Gunicorn's `app:app` target tried to import a module called `app`
and got a confusing mix of the file and the package depending on import
order/caching. Naming this file wsgi.py instead removes the collision
entirely: `app` always refers unambiguously to the app/ package, and
`wsgi` always refers to this file.

Local development:
    $ flask --app wsgi run --debug
    or
    $ python wsgi.py

Production (gunicorn — see Procfile / render.yaml):
    $ gunicorn wsgi:app
"""
import os

from app import create_app

app = create_app(os.environ.get("FLASK_ENV", "production"))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=app.config.get("DEBUG", False))
