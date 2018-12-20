CELERY_TASK_SERIALIZER='pickle'
CELERY_ACCEPT_CONTENT=['json','yaml', 'pickle']
CELERY_TASK_RESULT_EXPIRES=None
CELERY_RESULT_SERIALIZER='pickle'
CELERY_IMPORTS=("evaluation2.pipeline2","evaluation2.report_gen_run", "evaluation.evaluate_ground_truth")

BROKER_TRANSPORT = "amqp"
BROKER_HOST = "127.0.0.1" #IP address of the server running RabbitMQ and Celery
BROKER_PORT = 5672
BROKER_URL= "amqp://"

CELERY_RESULT_BACKEND = "redis"
CELERY_REDIS_HOST = "localhost"
CELERY_REDIS_PORT = 6379
CELERY_REDIS_PASSWORD = "trackt1cs_redis"
CELERY_REDIS_DB = 0
CELERY_IGNORE_RESULT = False
