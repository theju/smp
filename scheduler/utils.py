import re
import json

import requests

from django.contrib.sites.models import Site

from allauth.socialaccount.models import SocialApp, SocialAccount, SocialToken
from twitter import Twitter, OAuth


GRAPH_API_BASE_URL = "https://graph.facebook.com"

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
        site = Site.objects.get_current()
        params["picture"] = "https://{0}{1}".format(
            site.domain,
            post.attached_media.url
        )

    message = post.status.encode("utf-8")
    params["message"] = message
    link = re.findall("https?://[^\s]+", post.status)
    if link:
        params["link"] = link[0]

    response = requests.post(
        "{0}/{1}/feed".format(GRAPH_API_BASE_URL, account.uid),
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
