from django.urls import path
from . import views

urlpatterns = [
    path('payment/', views.payment, name='lipa-payment'),
    path('processing/<str:transaction_id>/', views.processing_payment, name='lipa-processing'),
    path('callback/', views.daraja_callback, name='daraja-callback'),
]