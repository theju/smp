import json

from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from scheduler.models import ScheduledPost
from scheduler.utils import post_to_facebook, post_to_twitter, post_to_linkedin


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
        services = {
            "facebook": post_to_facebook,
            "twitter": post_to_twitter,
            "linkedin_oauth2": post_to_linkedin,
        }
        for post in scheduled_posts:
            post_to_service = services.get(post.service)
            try:
                post_to_service(post)
            except Exception as ex:
                post.extra = json.dumps({
                    "error": str(ex)
                })
                post.save()
