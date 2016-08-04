from django.shortcuts import render
from django.http import HttpResponseRedirect, Http404
from django.core.urlresolvers import reverse_lazy
from django.contrib.auth import login as django_login, authenticate
from django.contrib.auth.decorators import login_required
from django.conf import settings

from .forms import ScheduledPostAddForm
from .models import User, ScheduledPost, AuthenticationToken


@login_required
def scheduled_posts_list(request):
    posts = ScheduledPost.objects.filter(
        user=request.user,
        is_posted=False
    ).order_by('scheduled_datetime')
    api_keys = AuthenticationToken.objects.filter(user=request.user)
    return render(request, 'list.html', {
        "posts": posts,
        "api_keys": api_keys
    })


@login_required
def scheduled_posts_add(request):
    form = ScheduledPostAddForm(user=request.user)
    if request.method == "POST":
        form = ScheduledPostAddForm(
            request.POST,
            request.FILES,
            user=request.user
        )
        if form.is_valid():
            instance = form.save(commit=False)
            instance.user = request.user
            instance.save()
            dashboard_url = reverse_lazy("scheduled_posts_list")
            return HttpResponseRedirect(dashboard_url)
    return render(request, 'add.html', {
        "form": form
    })


@login_required
def scheduled_posts_copy(request, id=None):
    try:
        instance = ScheduledPost.objects.get(id=id)
    except ScheduledPost.DoesNotExist:
        raise Http404
    if instance.user != request.user:
        raise Http404
    instance.id = None
    form = ScheduledPostAddForm(user=request.user, instance=instance)
    if request.method == "POST":
        form = ScheduledPostAddForm(
            request.POST,
            request.FILES,
            user=request.user,
            instance=instance
        )
        if form.is_valid():
            instance = form.save(commit=False)
            instance.user = request.user
            instance.save()
            dashboard_url = reverse_lazy("scheduled_posts_list")
            return HttpResponseRedirect(dashboard_url)
    return render(request, 'add.html', {
        "form": form
    })


@login_required
def scheduled_posts_edit(request, id=None):
    try:
        instance = ScheduledPost.objects.get(id=id)
    except ScheduledPost.DoesNotExist:
        raise Http404
    if instance.user != request.user:
        raise Http404
    form = ScheduledPostAddForm(user=request.user, instance=instance)
    if request.method == "POST":
        form = ScheduledPostAddForm(
            request.POST,
            request.FILES,
            user=request.user,
            instance=instance
        )
        if form.is_valid():
            instance = form.save(commit=False)
            instance.user = request.user
            instance.save()
            dashboard_url = reverse_lazy("scheduled_posts_list")
            return HttpResponseRedirect(dashboard_url)
    return render(request, 'add.html', {
        "form": form
    })


@login_required
def scheduled_posts_delete(request, id=None):
    try:
        instance = ScheduledPost.objects.get(id=id)
    except ScheduledPost.DoesNotExist:
        raise Http404
    if instance.user != request.user:
        raise Http404
    instance.delete()
    dashboard_url = reverse_lazy("scheduled_posts_list")
    return HttpResponseRedirect(dashboard_url)
