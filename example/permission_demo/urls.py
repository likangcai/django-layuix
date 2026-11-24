from django.urls import path

from . import views_api

urlpatterns = [
    path('orders/', views_api.order_list, name='permission_demo_order_list'),
]
