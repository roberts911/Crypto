from django.urls import path
from . import views

urlpatterns = [
    path('', views.crypto_list, name='crypto_list'),
    path('convert/', views.crypto_convert, name='crypto_convert'),
    path('chart', views.crypto_chart, name='crypto_chart'),
]
