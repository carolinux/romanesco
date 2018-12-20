from celery import Celery


celeryapp = Celery('tasks')
celeryapp.config_from_object('evaluation2.celery_config')

