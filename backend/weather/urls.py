from django.urls import path
from . import views

urlpatterns = [
    # path('', views.index, name='index'),
    # path('weather/', views.weather, name='weather'),
    path('location/', views.location_page, name='location'),
    path('get_weather/', views.get_weather, name='get_weather'),
]