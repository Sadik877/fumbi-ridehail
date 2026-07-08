"""
Entry point for local development.

    $ python app.py

The application factory lives in app/__init__.py so it can be reused
by WSGI servers (gunicorn), test suites, and the CLI the same way.
"""
from app import create_app

app = create_app()

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
