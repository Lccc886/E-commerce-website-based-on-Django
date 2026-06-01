from django.urls import path
from . import views

app_name = 'points'

urlpatterns = [
    path('', views.points_overview, name='points_overview'),
    path('history/', views.points_history, name='points_history'),
    path('checkin/', views.checkin, name='checkin'),
    path('exchange/', views.exchange_list, name='exchange_list'),
    path('exchange/<int:item_id>/', views.exchange_item, name='exchange_item'),
]
