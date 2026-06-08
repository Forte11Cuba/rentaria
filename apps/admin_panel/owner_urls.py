from django.urls import path

from . import owner_views as views

urlpatterns = [
    path('', views.my_shops, name='owner_my_shops'),
    path('settings/', views.settings, name='owner_settings'),
    path('shops/create/', views.shop_create, name='owner_shop_create'),
    path('shop/<slug:slug>/inventory/', views.inventory, name='owner_inventory'),
    path('shop/<slug:slug>/inventory/models/create/', views.model_create, name='owner_model_create'),
    path('shop/<slug:slug>/inventory/models/<int:pk>/edit/', views.model_edit, name='owner_model_edit'),
    path('shop/<slug:slug>/inventory/models/<int:pk>/toggle/', views.model_toggle, name='owner_model_toggle'),
    path('shop/<slug:slug>/inventory/models/<int:pk>/photos/upload/', views.photo_upload, name='owner_photo_upload'),
    path('shop/<slug:slug>/inventory/models/<int:pk>/photos/<int:foto_pk>/delete/', views.photo_delete, name='owner_photo_delete'),
    path('shop/<slug:slug>/inventory/models/<int:pk>/photos/<int:foto_pk>/reorder/', views.photo_reorder, name='owner_photo_reorder'),
    path('shop/<slug:slug>/inventory/units/add/', views.unit_add, name='owner_unit_add'),
    path('shop/<slug:slug>/inventory/units/<str:chapa>/toggle/', views.unit_toggle, name='owner_unit_toggle'),
    path('shop/<slug:slug>/inventory/units/<str:chapa>/delete/', views.unit_delete, name='owner_unit_delete'),
    path('shop/<slug:slug>/form/', views.form, name='owner_form'),
    path('shop/<slug:slug>/form/fields/create/', views.field_create, name='owner_field_create'),
    path('shop/<slug:slug>/form/fields/<int:pk>/edit/', views.field_edit, name='owner_field_edit'),
    path('shop/<slug:slug>/form/fields/<int:pk>/delete/', views.field_delete, name='owner_field_delete'),
    path('shop/<slug:slug>/form/fields/reorder/', views.field_reorder, name='owner_field_reorder'),
    path('shop/<slug:slug>/contract/', views.contract, name='owner_contract'),
    path('shop/<slug:slug>/contract/save/', views.contract_save, name='owner_contract_save'),
    path('shop/<slug:slug>/accounts/', views.accounts_list, name='owner_accounts'),
    path('shop/<slug:slug>/accounts/create/', views.account_create, name='owner_account_create'),
    path('shop/<slug:slug>/accounts/transfer/', views.transfer_new, name='owner_transfer_new'),
    path('shop/<slug:slug>/accounts/<int:pk>/', views.account_detail, name='owner_account_detail'),
    path('shop/<slug:slug>/accounts/<int:pk>/edit/', views.account_edit, name='owner_account_edit'),
    path('shop/<slug:slug>/accounts/<int:pk>/new/', views.operation_new, name='owner_operation_new'),
    path('shop/<slug:slug>/accounts/operations/<int:op_pk>/delete/', views.operation_delete, name='owner_operation_delete'),
    path('shop/<slug:slug>/settings/', views.shop_settings, name='owner_shop_settings'),
    # Dashboard
    path('shop/<slug:slug>/', views.dashboard, name='owner_dashboard'),
    # Orders
    path('shop/<slug:slug>/orders/', views.orders_list, name='owner_orders'),
    path('shop/<slug:slug>/orders/<str:orden_id>/', views.order_detail, name='owner_order_detail'),
    path('shop/<slug:slug>/orders/<str:orden_id>/confirm/', views.order_confirm, name='owner_order_confirm'),
    path('shop/<slug:slug>/orders/<str:orden_id>/cancel/', views.order_cancel, name='owner_order_cancel'),
    path('shop/<slug:slug>/orders/<str:orden_id>/reassign/', views.order_reassign, name='owner_order_reassign'),
    path('shop/<slug:slug>/orders/<str:orden_id>/contract.pdf', views.order_contract_pdf, name='owner_order_pdf'),
    # Customers
    path('shop/<slug:slug>/customers/', views.customers_list, name='owner_customers'),
    # Calendar
    path('shop/<slug:slug>/calendar/', views.calendar, name='owner_calendar'),
    path('shop/<slug:slug>/calendar/events/', views.calendar_events, name='owner_calendar_events'),
    path('shop/<slug:slug>/calendar/day/<str:dia>/', views.calendar_day, name='owner_calendar_day'),
]
