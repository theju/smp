from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from scheduler.models import ScheduledPost
from scheduler.utils import post_to_facebook, post_to_twitter


class Command(BaseCommand):
    help = 'Autopost to the social platforms'

    def handle(self, *args, **kwargs):
        now = timezone.now()
        next_min = now + timezone.timedelta(minutes=1)
        scheduled_posts = ScheduledPost.objects.filter(
            is_posted=False,
            scheduled_datetime__gte=now,
            scheduled_datetime__lt=next_min
        )
        for post in scheduled_posts:
            if post.service == "facebook":
                try:
                    post_to_facebook(post)
                except Exception:
                    pass
            elif post.service == "twitter":
                try:
                    post_to_twitter(post)
                except Exception:
                    pass
