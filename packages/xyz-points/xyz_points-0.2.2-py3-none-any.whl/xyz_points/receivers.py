# -*- coding:utf-8 -*- 
# author = 'denishuang'
from __future__ import unicode_literals
from django.dispatch import receiver
from django.db.models.signals import pre_delete, post_save, pre_save
from .models import Item, Point, Session
from django.db.models import Sum
from xyz_dailylog.signals import user_log
from datetime import datetime


@receiver(post_save, sender=Item)
def update_points(sender, **kwargs):
    item = kwargs.get('instance')
    point = item.point
    s = point.items.aggregate(s=Sum('value'))['s']
    Point.objects.filter(id=point.id).update(value=s)


@receiver(user_log)
def update_session_log(sender, **kwargs):
    user_id = kwargs.get('user_id')
    metics = kwargs.get('metics')
    delta = kwargs.get('delta')
    model = kwargs.get('model')
    score = 0
    if isinstance(metics, str):
        metics = {metics: delta}
    # print(f'update_session_log {metics}')
    for metic, delta in metics.items():
        if metic in ['answer_right_count', 'right_answer_questions']:
            score = delta * 1
        elif metic == 'video_watch_minutes':
            score = (delta or 1) * 5
        if not score:
            continue
        from .stores import PointsSession, PointsSessionDaily
        st = PointsSession()
        std = PointsSessionDaily()
        now = datetime.now()
        for s in Session.objects.filter(is_active=True, end_time__gt=now):
            st.log(s.id, user_id, model, delta=score)
            std.log(s.id, user_id, delta=score)
