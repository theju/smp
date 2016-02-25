import pytz
import json
import os

from django import forms
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _
from django.core.exceptions import ValidationError
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
    scheduled_tz = forms.CharField(widget=forms.HiddenInput)
    attached_media = forms.ImageField(required=False)

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
        fields = ("status", "service", "scheduled_datetime", "attached_media")

    def clean_scheduled_datetime(self):
        scheduled_datetime = self.cleaned_data["scheduled_datetime"]
        if scheduled_datetime < timezone.now():
            raise forms.ValidationError("Time cannot be in the past")
        return scheduled_datetime

    def clean(self):
        data = self.cleaned_data
        if data.get("scheduled_datetime"):
            sched_dt = data["scheduled_datetime"]
            tz = pytz.timezone(data.get("scheduled_tz", "UTC"))
            sched_dt = tz.localize(sched_dt.replace(tzinfo=None))
            data["scheduled_datetime"] = timezone.localtime(sched_dt)
        return data
