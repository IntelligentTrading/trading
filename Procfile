release: python manage.py migrate
web: gunicorn webserver.wsgi --log-file -
worker: celery worker --app=tasks.app
