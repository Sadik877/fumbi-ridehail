web: gunicorn -c gunicorn_conf.py wsgi:app
# The "release" line below only applies on Heroku (Render doesn't read
# Procfile at all — it uses the Build/Start Command from render.yaml or
# the dashboard instead). Requires real Flask-Migrate migrations to exist
# (flask db init && flask db migrate), which this project doesn't ship
# with yet — see render.yaml's comments for the current bootstrap path.
release: flask --app wsgi db upgrade
