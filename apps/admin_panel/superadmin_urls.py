from django.urls import path

from . import superadmin_views as views

urlpatterns = [
    path('', views.dashboard, name='superadmin_dashboard'),
    path('users/', views.usuarios, name='superadmin_users'),
    path('users/<int:pk>/approve/', views.usuario_aprobar, name='superadmin_user_approve'),
    path('users/<int:pk>/reject/', views.usuario_rechazar, name='superadmin_user_reject'),
    path('users/<int:pk>/delete/', views.usuario_eliminar, name='superadmin_user_delete'),
    path('users/<int:pk>/change-password/', views.usuario_cambiar_password, name='superadmin_user_change_password'),
    path('shops/', views.tiendas, name='superadmin_shops'),
    path('shops/create/', views.tienda_crear, name='superadmin_shop_create'),
    path('orders/', views.ordenes, name='superadmin_orders'),
]
