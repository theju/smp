from datetime import datetime
import base64
import json
import os
import StringIO

from django.test import TestCase
from django.core.files.images import ImageFile
from django.conf import settings

from allauth.socialaccount.models import SocialApp, SocialAccount

from .models import ScheduledPost, AuthenticationToken, User


class APITestCase(TestCase):
    dt = datetime(2020, 01, 01, 00, 01, 00).strftime("%Y-%m-%dT%H:%M:%SZ")

    def setUp(self):
        uu = User.objects.create(username="example", email="foo@example.com")

        SocialApp.objects.create(
            name="SMPTestFB", provider="facebook", client_id="123", secret="def"
        )
        SocialAccount.objects.create(user=uu, provider="facebook", uid="abc")

        token = AuthenticationToken.objects.get(user=uu).token
        self.auth_str = str(base64.b64encode("{0}:".format(token)))

    def testInvalidAuth(self):
        auth_str = str(base64.b64encode("123:"))
        response = self.client.post("/api/post/add/", {
            "status": "Hello World",
            "service": "facebook",
            "scheduled_datetime": self.dt,
            "scheduled_tz": "UTC"
        })
        self.assertEqual(response.status_code, 401)
        response = self.client.post("/api/post/add/", {
            "status": "Hello World",
            "service": "facebook",
            "scheduled_datetime": self.dt,
            "scheduled_tz": "UTC"            
        }, HTTP_AUTHORIZATION="Fancy {0}".format(auth_str))
        self.assertEqual(response.status_code, 401)
        response = self.client.post("/api/post/add/", {
            "status": "Hello World",
            "service": "facebook",
            "scheduled_datetime": self.dt
        }, HTTP_AUTHORIZATION="Basic {0}".format(auth_str))
        self.assertEqual(response.status_code, 401)
        response = self.client.post("/api/post/add/", {
            "status": "Hello World",
            "service": "facebook",
            "scheduled_datetime": self.dt,
            "scheduled_tz": "UTC"            
        }, HTTP_AUTHORIZATION="Basic x{0}".format(auth_str))
        self.assertEqual(response.status_code, 401)

    def testPostMisconfiguredService(self):
        response = self.client.post("/api/post/add/", {
            "status": "Hello World",
            "service": "twitter",
            "scheduled_datetime": self.dt,
            "scheduled_tz": "UTC"            
        }, HTTP_AUTHORIZATION="Basic {0}".format(self.auth_str))
        self.assertEqual(response.status_code, 400)

    def testPostAdd(self):
        response = self.client.post("/api/post/add/", {
            "status": "Hello World",
            "service": "facebook",
            "scheduled_datetime": self.dt,
            "scheduled_tz": "UTC"            
        }, HTTP_AUTHORIZATION="Basic {0}".format(self.auth_str))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(ScheduledPost.objects.count(), 1)

    def testPostAddWithMedia(self):
        # Invalid PNG
        onepx_png = StringIO.StringIO(
            "\x89PAG\r\n\x1a\n\x00\x00\x00\rIHDR\x00"
            "\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00"
            "\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\rIDAT"
            "\x08\xd7c````\x00\x00\x00\x05\x00\x01^\xf3*"
            ":\x00\x00\x00\x00IEND\xaeB`\x82"
        )
        response = self.client.post("/api/post/add/", {
            "status": "Hello World",
            "service": "facebook",
            "attached_media": onepx_png,
            "scheduled_datetime": self.dt,
            "scheduled_tz": "UTC"            
        }, HTTP_AUTHORIZATION="Basic {0}".format(self.auth_str))
        self.assertEqual(response.status_code, 400)

        # Valid PNG
        onepx_png = StringIO.StringIO(
            "\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00"
            "\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00"
            "\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\rIDAT"
            "\x08\xd7c````\x00\x00\x00\x05\x00\x01^\xf3*"
            ":\x00\x00\x00\x00IEND\xaeB`\x82"
        )
        response = self.client.post("/api/post/add/", {
            "status": "Hello World",
            "service": "facebook",
            "attached_media": onepx_png,
            "scheduled_datetime": self.dt,
            "scheduled_tz": "UTC"            
        }, HTTP_AUTHORIZATION="Basic {0}".format(self.auth_str))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(ScheduledPost.objects.count(), 1)
        post = ScheduledPost.objects.get()
        file_path = [os.path.join(settings.MEDIA_ROOT, "attached_media")]
        self.assertEqual(json.loads(post.attached_media), file_path)
