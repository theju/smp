import datetime
import pytz

from django import forms
from django.forms.utils import from_current_timezone
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _
from django.core.exceptions import ValidationError

from allauth.socialaccount.models import SocialAccount

from .models import User, ScheduledPost


class SplitDateTimeField(forms.SplitDateTimeField):
    def __init__(self, *args, **kwargs):
        super(SplitDateTimeField, self).__init__(*args, **kwargs)
        self.default_error_messages['invalid_tz'] = _('Enter a valid tz')
        self.fields = self.fields + (
            # TZ field
            forms.CharField(),
        )

    def compress(self, data_list):
        if data_list:
            # Raise a validation error if time or date is empty
            # (possible if SplitDateTimeField has required=False).
            if data_list[0] in self.empty_values:
                raise ValidationError(self.error_messages['invalid_date'], code='invalid_date')
            if data_list[1] in self.empty_values:
                raise ValidationError(self.error_messages['invalid_time'], code='invalid_time')
            if data_list[2] in self.empty_values:
                raise ValidationError(self.error_messages['invalid_tz'], code='invalid_tz')
            result = datetime.datetime.combine(data_list[0], data_list[1])
            timezone.activate(pytz.timezone(data_list[2]))
            tz_aware_datetime = from_current_timezone(result)
            timezone.deactivate()
            return tz_aware_datetime
        return None

class SplitDateTimeWidget(forms.SplitDateTimeWidget):
    def __init__(self, *args, **kwargs):
        super(SplitDateTimeWidget, self).__init__(*args, **kwargs)
        self.widgets[0].input_type = "date"
        self.widgets[1].input_type = "time"
        self.widgets.append(forms.HiddenInput())


class ScheduledPostAddForm(forms.ModelForm):
    scheduled_datetime = SplitDateTimeField(
        widget=SplitDateTimeWidget
    )

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
        fields = ("status", "service", "scheduled_datetime")

    def clean_scheduled_datetime(self):
        scheduled_datetime = self.cleaned_data["scheduled_datetime"]
        if scheduled_datetime < timezone.now():
            raise forms.ValidationError("Time cannot be in the past")
        return scheduled_datetime
