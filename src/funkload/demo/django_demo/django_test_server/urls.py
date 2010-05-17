from django.conf.urls.defaults import *
from django.http import HttpResponse,HttpResponseNotAllowed
import datetime

def _getter( request ):
    if request.method == "GET":
        now = datetime.datetime.now()
        html = "<html><body>It is now %s.</body></html>" % now
        return HttpResponse(html)
    else:
        return HttpResponseNotAllowed("only gets")

def _poster( request ):
    if request.method == "POST":
        now = datetime.datetime.now()
        html = "<html><body>It is now %s.</body></html>" % now
        return HttpResponse(html)
    else:
        return HttpResponseNotAllowed("only posts")

def _deleter( request ):
    if request.method == "DELETE":
        now = datetime.datetime.now()
        html = "<html><body>It is now %s.</body></html>" % now
        return HttpResponse(html)
    else:
        return HttpResponseNotAllowed("only deletes")

def _putter( request ):
    if request.method == "PUT":
        now = datetime.datetime.now()
        html = "<html><body>It is now %s.</body></html>" % now
        return HttpResponse(html)
    else:
        return HttpResponseNotAllowed("only puts")


urlpatterns = patterns('',
    # Example:
    (r'^site_media/(?P<path>.*)$', 'django.views.static.serve',
        {'document_root': '/tmp/snapshots'}),

    (r'^fltest/methods',include('fltest.methods.urls')),
    (r'^fltest/_getter', _getter),
    (r'^fltest/_putter', _putter),
    (r'^fltest/_deleter',_deleter),
    (r'^fltest/_poster', _poster),
)
