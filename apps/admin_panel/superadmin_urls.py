from django.urls import path

from . import superadmin_views as views

urlpatterns = [
    path('', views.dashboard, name='superadmin_dashboard'),
    path('users/', views.users, name='superadmin_users'),
    path('users/<int:pk>/approve/', views.user_approve, name='superadmin_user_approve'),
    path('users/<int:pk>/reject/', views.user_reject, name='superadmin_user_reject'),
    path('users/<int:pk>/delete/', views.user_delete, name='superadmin_user_delete'),
    path('users/<int:pk>/change-password/', views.user_change_password, name='superadmin_user_change_password'),
    path('shops/', views.shops, name='superadmin_shops'),
    path('shops/create/', views.shop_create, name='superadmin_shop_create'),
    path('orders/', views.orders, name='superadmin_orders'),
    path('smtp/', views.smtp_settings, name='superadmin_smtp'),
]
