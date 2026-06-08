from django.urls import path
from . import views

urlpatterns = [
    path('<slug:slug>/catalog/', views.catalog, name='api_catalog'),
]
