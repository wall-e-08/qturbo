web: gunicorn core.wsgi
worker: celery -A core worker -l info -Q stm,lim,anc,esign_check -c 4
beat: celery -A core beat -l info
