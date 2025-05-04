from __future__ import absolute_import, unicode_literals

# Celery 앱 초기화
from core.config.celery import app as celery_app

__all__ = ('celery_app',)