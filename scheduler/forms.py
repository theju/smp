import pytz
import json
import os
import mimetypes
import requests
import tempfile

from django import forms
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _
from django.core.exceptions import ValidationError
from django.core.files.images import ImageFile, get_image_dimensions
from django.conf import settings

from allauth.socialaccount.models import SocialAccount

from .models import User, ScheduledPost


class SplitDateTimeWidget(forms.SplitDateTimeWidget):
    def __init__(self, *args, **kwargs):
        super(SplitDateTimeWidget, self).__init__(*args, **kwargs)
        self.widgets[0].input_type = "date"
        self.widgets[1].input_type = "time"


class ScheduledPostAddForm(forms.ModelForm):
    scheduled_datetime = forms.SplitDateTimeField(
        widget=SplitDateTimeWidget
    )
    scheduled_tz = forms.CharField(widget=forms.HiddenInput,
                                   initial="UTC", required=False)
    status = forms.CharField(
        widget=forms.Textarea(attrs={"rows": None, "cols": None})
    )
    attached_media = forms.ImageField(required=False)
    media_url = forms.URLField(required=False)

    def __init__(self, *args, **kwargs):
        user = kwargs.pop("user")
        super(ScheduledPostAddForm, self).__init__(*args, **kwargs)
        one_hour_hence = timezone.now() + timezone.timedelta(hours=1)
        self.fields["scheduled_datetime"].initial = one_hour_hence
        self.fields["service"].choices = []
        if SocialAccount.objects.filter(user=user, provider="facebook").count():
            self.fields["service"].choices.append(
                ("facebook", "Facebook"),
            )
        if SocialAccount.objects.filter(user=user, provider="twitter").count():
            self.fields["service"].choices.append(
                ("twitter", "Twitter"),
            )

    class Meta:
        model = ScheduledPost
        fields = ("scheduled_datetime", "service", "status", "attached_media")

    def clean_scheduled_datetime(self):
        scheduled_datetime = self.cleaned_data["scheduled_datetime"]
        if scheduled_datetime < timezone.now():
            raise forms.ValidationError(_("Time cannot be in the past"))
        return scheduled_datetime

    def clean(self):
        data = self.cleaned_data

        if data.get("scheduled_datetime"):
            sched_dt = data["scheduled_datetime"]
            sched_tz = timezone.pytz.timezone(data.get("scheduled_tz"))
            sched_dt = sched_tz.localize(sched_dt.replace(tzinfo=None))
            data["scheduled_datetime"] = timezone.localtime(sched_dt)

        if data.get("attached_media") and data.get("media_url"):
            raise forms.ValidationError(_("Only one of media URL or "
                                          "attached media may be provided"))

        if data.get("media_url"):
            response = requests.get(data["media_url"])
            if not response.ok:
                raise forms.ValidationError(_("An error occurred while "
                                              "downloading the media from the URL"))
            ext = mimetypes.guess_extension(response.headers['content-type'])
            ff = tempfile.NamedTemporaryFile(suffix=ext)
            ff.write(response.content)
            img_file = ImageFile(ff, name=ff.name)
            height, width = get_image_dimensions(img_file)
            if height is None or width is None:
                ff.close()
                raise forms.ValidationError(_("Invalid image"))
            data["attached_media"] = img_file
        return data
