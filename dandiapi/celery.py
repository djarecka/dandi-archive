import os

from celery import Celery, signals
import configurations.importer

os.environ['DJANGO_SETTINGS_MODULE'] = 'dandiapi.settings'
if not os.environ.get('DJANGO_CONFIGURATION'):
    raise ValueError('The environment variable "DJANGO_CONFIGURATION" must be set.')
configurations.importer.install()

# Using a string config_source means the worker doesn't have to serialize
# the configuration object to child processes.
app = Celery(config_source='django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django app configs.
app.autodiscover_tasks()


@signals.import_modules.connect
def _register_scheduled_tasks(sender, **kwargs):
    from dandiapi.api.scheduled_tasks import register_scheduled_tasks

    register_scheduled_tasks(sender, **kwargs)
