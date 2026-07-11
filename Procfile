web: gunicorn -c gunicorn_conf.py wsgi:app
release: flask --app wsgi db upgrade
