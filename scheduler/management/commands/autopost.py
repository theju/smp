import re
import json
import requests

from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from allauth.socialaccount.models import SocialApp, SocialAccount, SocialToken
from twitter import Twitter, OAuth

from scheduler.models import ScheduledPost


def post_to_facebook(post):
    try:
        account = SocialAccount.objects.get(user=post.user,
                                            provider=post.service)
    except SocialAccount.DoesNotExist:
        return None
    try:
        access_token = account.socialtoken_set.get().token
    except SocialToken.DoesNotExist:
        return None

    params = {
        "access_token": access_token
    }
    if post.attached_media:
        params.update({"no_story": True})
        response = requests.post(
            "https://graph.facebook.com/{0}/photos".format(
                account.uid
            ),
            data=params,
            files={"source": post.attached_media}
        )
        if response.ok:
            photo_id = response.json()["id"]
            params["object_attachment"] = photo_id
            params.pop("no_story", None)

    message = post.status.encode("utf-8")
    params["message"] = message
    link = re.findall("https?://[^\s]+", post.status)
    if link:
        params["link"] = link[0]

    response = requests.post(
        "https://graph.facebook.com/{0}/feed".format(
            account.uid
        ),
        data=params
    )
    if response.ok:
        post.is_posted = True
        post.save()


def post_to_twitter(post):
    app = SocialApp.objects.get(provider=post.service)
    try:
        account = SocialAccount.objects.get(user=post.user,
                                            provider=post.service)
    except SocialAccount.DoesNotExist:
        return None
    try:
        token = account.socialtoken_set.get().token
        token_secret = account.socialtoken_set.get().token_secret
    except SocialToken.DoesNotExist:
        return None

    kwargs = {
        "status": post.status.encode("utf-8"),
    }
    if post.attached_media:
        twt_up = Twitter(
            domain='upload.twitter.com',
            auth=OAuth(token, token_secret, app.client_id, app.secret)
        )
        media = []
        contents = post.attached_media.read()
        media.append(twt_up.media.upload(media=contents)["media_id_string"])
        kwargs["media_ids"] = ",".join(media)
    twt = Twitter(auth=OAuth(token, token_secret, app.client_id, app.secret))
    twt.statuses.update(**kwargs)
    post.is_posted = True
    post.save()


class Command(BaseCommand):
    help = 'Autopost to the social platforms'

    def handle(self, *args, **kwargs):
        now = timezone.now()
        next_min = now + timezone.timedelta(minutes=1)
        for post in ScheduledPost.objects.filter(is_posted=False,
                                                 scheduled_datetime__gte=now,
                                                 scheduled_datetime__lt=next_min):
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
