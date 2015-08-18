from __future__ import absolute_import
from django.conf.urls.defaults import *
from . import views
from django.views.generic.simple import direct_to_template
from django.http import HttpResponse

urlpatterns = patterns('',
    # Example:
    (r'get', views.getter),
    (r'put', views.putter),
    (r'delete', views.deleter),
    (r'post', views.poster))
