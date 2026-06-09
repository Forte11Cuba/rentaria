from django.urls import path
from . import views

urlpatterns = [
    path('<slug:slug>/account/', views.dashboard, name='customer_dashboard'),
    path('<slug:slug>/account/login/', views.login, name='customer_login'),
    path('<slug:slug>/account/logout/', views.logout, name='customer_logout'),
    path('<slug:slug>/account/activate/<str:token>/', views.activate, name='customer_activate'),
    path('<slug:slug>/account/recover/', views.recover, name='customer_recover'),
]
