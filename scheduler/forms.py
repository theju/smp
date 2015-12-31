from django import forms
from django.utils import timezone

from allauth.socialaccount.models import SocialAccount

from .models import User, ScheduledPost


class SplitDateTimeWidget(forms.SplitDateTimeWidget):
    def __init__(self, *args, **kwargs):
        super(SplitDateTimeWidget, self).__init__(*args, **kwargs)
        self.widgets[0].input_type = "date"
        self.widgets[1].input_type = "time"


class ScheduledPostAddForm(forms.ModelForm):
    scheduled_datetime = forms.SplitDateTimeField(
        widget=SplitDateTimeWidget,
        initial=timezone.now() + timezone.timedelta(hours=1)
    )

    def __init__(self, *args, **kwargs):
        user = kwargs.pop("user")
        super(ScheduledPostAddForm, self).__init__(*args, **kwargs)
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
        fields = ("status", "service", "scheduled_datetime")

    def clean_scheduled_datetime(self):
        scheduled_datetime = self.cleaned_data["scheduled_datetime"]
        if scheduled_datetime < timezone.now():
            raise forms.ValidationError("Time cannot be in the past")
        return scheduled_datetime
