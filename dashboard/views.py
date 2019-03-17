from urllib.parse import urlparse

from django.urls import resolve
from django.shortcuts import render, redirect
from django.http import HttpResponse, Http404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate
from django.contrib.auth import login as django_login
from django.contrib.auth import logout as django_logout

from .forms import UploadFileForm

@login_required
def index(request):
    # form = UploadFileForm()
    return render(request, 'dashboard/index.html')


@login_required
def logout(request):
    django_logout(request)

    return redirect('dashboard:login')

def login(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        next = request.POST['next']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            django_login(request, user)
            try:
                resolve(urlparse(next))
            except Http404:
                return redirect('dashboard:index')

        return redirect(next)

    next = request.GET['next'] if 'next' in request.GET else None
    return render(request, 'dashboard/login.html', {'next': next})
