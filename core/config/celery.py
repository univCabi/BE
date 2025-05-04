from __future__ import absolute_import, unicode_literals
import os
from celery import Celery
from datetime import timedelta

# Django 설정 모듈 지정
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'univ_cabi.settings')

app = Celery('univ_cabi')

# Django 설정에서 Celery 구성 가져오기
app.config_from_object('django.conf:settings', namespace='CELERY')

# 등록된 모든 Django 앱 설정에서 작업 모듈을 자동으로 불러오기
app.autodiscover_tasks(['cabinet'])

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')

# 기존 스케줄 유지 (필요한 경우)
app.conf.beat_schedule.update({
    'process-cabinet-rental': {
        'task': 'cabinet.util.cabinet_celery_task.process_cabinet_rental',
        'schedule': timedelta(seconds=10),
        'options': {
            'queue': 'cabinet_operations',
        }
    },
})

# 5초마다 북마크 동기화 실행 스케줄 설정
app.conf.beat_schedule = {
    'sync-bookmarks-every-5-seconds': {
        'task': 'cabinet.util.cabinet_celery_task.sync_bookmarks_to_database',
        'schedule': timedelta(seconds=5),
    },
}

# 기존 작업 유지
app.conf.task_routes = {
    'cabinet.util.cabinet_celery_task.process_cabinet_rental': {'queue': 'cabinet_operations'},
    'cabinet.util.cabinet_celery_task.sync_bookmarks_to_database': {'queue': 'cabinet_operations'},
}