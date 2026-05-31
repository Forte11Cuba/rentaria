from django.urls import path

from . import dueno_views as views

urlpatterns = [
    path('', views.mis_tiendas, name='owner_my_shops'),
    path('settings/', views.cuenta, name='owner_settings'),
    path('shops/create/', views.tienda_crear, name='owner_shop_create'),
    path('shop/<slug:slug>/inventory/', views.inventario, name='owner_inventory'),
    path('shop/<slug:slug>/inventory/models/create/', views.modelo_crear, name='owner_model_create'),
    path('shop/<slug:slug>/inventory/models/<int:pk>/edit/', views.modelo_editar, name='owner_model_edit'),
    path('shop/<slug:slug>/inventory/models/<int:pk>/toggle/', views.modelo_toggle, name='owner_model_toggle'),
    path('shop/<slug:slug>/inventory/models/<int:pk>/photos/upload/', views.foto_subir, name='owner_photo_upload'),
    path('shop/<slug:slug>/inventory/models/<int:pk>/photos/<int:foto_pk>/delete/', views.foto_eliminar, name='owner_photo_delete'),
    path('shop/<slug:slug>/inventory/models/<int:pk>/photos/<int:foto_pk>/reorder/', views.foto_reordenar, name='owner_photo_reorder'),
    path('shop/<slug:slug>/inventory/units/add/', views.moto_agregar, name='owner_unit_add'),
    path('shop/<slug:slug>/inventory/units/<str:chapa>/toggle/', views.moto_toggle, name='owner_unit_toggle'),
    path('shop/<slug:slug>/inventory/units/<str:chapa>/delete/', views.moto_eliminar, name='owner_unit_delete'),
    path('shop/<slug:slug>/form/', views.formulario, name='owner_form'),
    path('shop/<slug:slug>/form/fields/create/', views.campo_crear, name='owner_field_create'),
    path('shop/<slug:slug>/form/fields/<int:pk>/edit/', views.campo_editar, name='owner_field_edit'),
    path('shop/<slug:slug>/form/fields/<int:pk>/delete/', views.campo_eliminar, name='owner_field_delete'),
    path('shop/<slug:slug>/form/fields/reorder/', views.campo_reordenar, name='owner_field_reorder'),
    path('shop/<slug:slug>/contract/', views.contrato, name='owner_contract'),
    path('shop/<slug:slug>/contract/save/', views.contrato_guardar, name='owner_contract_save'),
    path('shop/<slug:slug>/accounts/', views.cuentas_lista, name='owner_accounts'),
    path('shop/<slug:slug>/accounts/create/', views.cuenta_crear, name='owner_account_create'),
    path('shop/<slug:slug>/accounts/transfer/', views.transferencia_nueva, name='owner_transfer_new'),
    path('shop/<slug:slug>/accounts/<int:pk>/', views.cuenta_detalle, name='owner_account_detail'),
    path('shop/<slug:slug>/accounts/<int:pk>/edit/', views.cuenta_editar, name='owner_account_edit'),
    path('shop/<slug:slug>/accounts/<int:pk>/new/', views.operacion_nueva, name='owner_operation_new'),
    path('shop/<slug:slug>/accounts/operations/<int:op_pk>/delete/', views.operacion_eliminar, name='owner_operation_delete'),
    path('shop/<slug:slug>/settings/', views.configuracion, name='owner_shop_settings'),
    # Dashboard
    path('shop/<slug:slug>/', views.dashboard, name='owner_dashboard'),
    # Orders
    path('shop/<slug:slug>/orders/', views.ordenes_lista, name='owner_orders'),
    path('shop/<slug:slug>/orders/<str:orden_id>/', views.orden_detalle, name='owner_order_detail'),
    path('shop/<slug:slug>/orders/<str:orden_id>/confirm/', views.orden_confirmar, name='owner_order_confirm'),
    path('shop/<slug:slug>/orders/<str:orden_id>/cancel/', views.orden_cancelar, name='owner_order_cancel'),
    path('shop/<slug:slug>/orders/<str:orden_id>/reassign/', views.orden_reasignar, name='owner_order_reassign'),
    path('shop/<slug:slug>/orders/<str:orden_id>/contract.pdf', views.orden_contrato_pdf, name='owner_order_pdf'),
    # Calendar
    path('shop/<slug:slug>/calendar/', views.calendario, name='owner_calendar'),
    path('shop/<slug:slug>/calendar/events/', views.calendario_eventos, name='owner_calendar_events'),
    path('shop/<slug:slug>/calendar/day/<str:dia>/', views.calendario_dia, name='owner_calendar_day'),
]
