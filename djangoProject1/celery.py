# djangoProject1/celery.py

import os
from celery import Celery

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'djangoProject1.settings')

app = Celery('djangoProject1')


app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django app configs.
app.conf.imports = (
    'inventory.tasks',
    # Add other task modules here
)


# Optional: Define a debug task to verify Celery is working
@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')
