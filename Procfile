release: python manage.py migrate && python manage.py collectstatic --noinput
web: gunicorn twenty_one_tech_pocs.twenty_one_tech_pocs.wsgi:application --bind 0.0.0.0:$PORT 