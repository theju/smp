from datetime import datetime
import base64

from django.test import TestCase

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
            "scheduled_datetime": self.dt
        })
        self.assertEqual(response.status_code, 401)
        response = self.client.post("/api/post/add/", {
            "status": "Hello World",
            "service": "facebook",
            "scheduled_datetime": self.dt
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
            "scheduled_datetime": self.dt
        }, HTTP_AUTHORIZATION="Basic x{0}".format(auth_str))
        self.assertEqual(response.status_code, 401)

    def testPostAdd(self):
        response = self.client.post("/api/post/add/", {
            "status": "Hello World",
            "service": "facebook",
            "scheduled_datetime": self.dt
        }, HTTP_AUTHORIZATION="Basic {0}".format(self.auth_str))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(ScheduledPost.objects.count(), 1)

    def testPostMisconfiguredService(self):
        response = self.client.post("/api/post/add/", {
            "status": "Hello World",
            "service": "twitter",
            "scheduled_datetime": self.dt
        }, HTTP_AUTHORIZATION="Basic {0}".format(self.auth_str))
        self.assertEqual(response.status_code, 400)
