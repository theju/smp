import urllib
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
    media_objs = json.loads(post.attached_media)
    media = []
    for med in media_objs:
        try:
            med_file = open(med, "rb")
        except IOError:
            continue
        response = requests.post(
            "https://graph.facebook.com/{0}/photos?{1}".format(
                account.uid,
                urllib.urlencode(params)
            ),
            files={"source": med_file}
        )
        if response.ok:
            media.append(response.json()["id"])

    if media:
        params["object_attachment"] = media[0]

    message = post.status.encode("utf-8")
    params["message"] = message
    link = re.findall("https?://[^\s]+", post.status)
    if link:
        params["link"] = link[0]

    response = requests.post(
        "https://graph.facebook.com/{0}/feed?{1}".format(
            account.uid,
            urllib.urlencode(params)
        ))
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
    media_objs = json.loads(post.attached_media)
    if media_objs:
        media = []
        twt_up = Twitter(
            domain='upload.twitter.com',
            auth=OAuth(token, token_secret, app.client_id, app.secret)
        )
        for med in media_objs:
            try:
                med_file = open(med, "rb")
            except IOError:
                pass
            media.append(twt_up.media.upload(media=med_file)["media_id_string"])
            med_file.close()
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
                post_to_facebook(post)
            elif post.service == "twitter":
                post_to_twitter(post)
