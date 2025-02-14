# This project module is imported for us when Django starts. To ensure that Celery app is always
# defined prior to any shared_task definitions (so those tasks will bind to the app), import
# the Celery module here for side effects.
from pkg_resources import get_distribution

from .celery import app as _celery_app  # noqa: F401

__version__ = get_distribution('dandiapi').version
