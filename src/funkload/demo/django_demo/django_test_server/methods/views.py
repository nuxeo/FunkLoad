# Create your views here.

from django.http import HttpResponse,HttpResponseRedirect
import django.http

def getter(request):
    return HttpResponseRedirect("/fltest/_getter/")
def poster(request):
    return HttpResponseRedirect("/fltest/_poster")
def putter(request):
    return HttpResponseRedirect("/fltest/_putter")
def deleter(request):
    return HttpResponseRedirect("/fltest/_deleter")


