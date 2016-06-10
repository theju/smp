import base64
import datetime

from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import login, authenticate
from django.conf import settings

from .models import ScheduledPost, User, AuthenticationToken
from .forms import ScheduledPostAddForm


def validate_basic_auth(fn):
    def wrapper(request, **kwargs):
        authorization_str = request.META.get("HTTP_AUTHORIZATION")
        if not authorization_str:
            return JsonResponse({"error": "Invalid Authentication"}, status=401)
        scheme, encoded = authorization_str.split(" ", 1)
        if scheme.lower() != "basic":
            return JsonResponse({"error": "Invalid authentication scheme"}, status=401)
        try:
            token, _ = base64.b64decode(encoded.encode().strip()).decode().split(":")
        except (TypeError, ValueError):
            return JsonResponse({"error": "Invalid token"}, status=401)
        try:
            token_obj = AuthenticationToken.objects.get(token=token)
        except AuthenticationToken.DoesNotExist:
            return JsonResponse({"error": "Invalid token"}, status=401)
        backend = settings.AUTHENTICATION_BACKENDS[0]
        user = token_obj.user
        user.backend = backend
        login(request, user)
        return fn(request, **kwargs)
    return wrapper


@require_POST
@csrf_exempt
@validate_basic_auth
def post_add(request, **kwargs):
    data = request.POST.copy()
    scheduled_datetime = data.get("scheduled_datetime", "")
    try:
        scheduled_datetime = datetime.datetime.strptime(scheduled_datetime,
                                                        "%Y-%m-%dT%H:%M:%SZ")
    except ValueError:
        return JsonResponse({"error": ("Invalid datetime format. "
                                       "Should be yyyy-mm-ddTHH:MM:SSZ")},
                            status=400)
    data["scheduled_datetime_0"] = scheduled_datetime.strftime("%Y-%m-%d")
    data["scheduled_datetime_1"] = scheduled_datetime.strftime("%H:%M")
    form = ScheduledPostAddForm(data, request.FILES, user=request.user)
    if form.is_valid():
        instance = form.save(commit=False)
        instance.user = request.user
        instance.save()
        return JsonResponse({"success": True})
    return JsonResponse({"error": dict(form.errors)}, status=400)
