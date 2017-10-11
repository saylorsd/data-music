from django.conf.urls import url
from . import views

urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r'^neighborhood-music/$', views.neighborhood_music, name='neighborhood_music')
]
