from django.urls import path

from . import views

app_name = 'reservas'

urlpatterns = [
    # payment and confirmation first — before the <slug> catch-all
    path('payment/webhook/btcpay/', views.webhook_btcpay, name='webhook_btcpay'),
    path('payment/<str:orden_id>/', views.payment_bitcoin, name='payment_bitcoin'),
    path('payment/<str:orden_id>/status/', views.payment_status, name='payment_status'),
    path('confirmation/<str:orden_id>/', views.confirmation, name='confirmation'),
    path('confirmation/<str:orden_id>/contract.pdf', views.confirmation_contract_pdf, name='confirmation_contract_pdf'),

    # booking flow per shop
    path('<slug:slug>/', views.step1_dates, name='step1_dates'),
    path('<slug:slug>/models/', views.step2_models, name='step2_models'),
    path('<slug:slug>/availability/', views.availability, name='availability'),
    path('<slug:slug>/data/', views.step3_form, name='step3_form'),
    path('<slug:slug>/payment/', views.step4_payment, name='step4_payment'),
    path('<slug:slug>/book/create/', views.book_create, name='book_create'),
]
