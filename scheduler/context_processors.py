from django.utils import timezone

def current_time(request):
    return {"current_time": timezone.now()}
