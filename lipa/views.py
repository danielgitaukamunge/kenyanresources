from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.contrib import messages
from django.urls import reverse
from .models import Transaction
from .utils import get_access_token
from django.views.decorators.csrf import csrf_exempt
import json
import requests

@login_required
def payment(request):
    amount = request.GET.get('amount', '30')
    success_url = request.GET.get('success_url')
    
    if request.method == 'POST':
        phone_number = request.POST.get('phone_number')
        amount = request.GET.get('amount')
        
        if phone_number and amount:
            access_token = get_access_token()
            stk_push_url = f"{settings.MPESA_API_URL}/mpesa/stkpush/v1/processrequest"
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json",
            }
            payload = {
                "BusinessShortCode": settings.MPESA_EXPRESS_SHORTCODE,
                "Password": generate_password(),
                "Timestamp": get_timestamp(),
                "TransactionType": "CustomerPayBillOnline",
                "Amount": amount,
                "PartyA": phone_number,
                "PartyB": settings.MPESA_EXPRESS_SHORTCODE,
                "PhoneNumber": phone_number,
                "CallBackURL": "https://5978-102-0-7-14.ngrok-free.app/callback/",
                "AccountReference": "SchemePayment",
                "TransactionDesc": "Payment for schemes",
            }

            response = requests.post(stk_push_url, json=payload, headers=headers)
            if response.status_code == 200:
                transaction = Transaction.objects.create(
                    user=request.user,
                    phone_number=phone_number,
                    amount=amount,
                    status='pending',
                    checkout_request_id=response.json().get('CheckoutRequestID'),
                    success_url=success_url
                )
                messages.success(request, 'Payment initiated successfully!')
                return redirect('lipa-processing', transaction_id=transaction.id)
            else:
                messages.error(request, 'Failed to initiate payment. Please try again.')
        else:
            messages.error(request, 'Please fill in all fields correctly.')

    context = {
        'predefined_amount': amount,
        'success_url': success_url
    }
    return render(request, 'lipa/payment.html', context)

def generate_password():
    from base64 import b64encode
    from datetime import datetime
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    return b64encode(f"{settings.MPESA_EXPRESS_SHORTCODE}{settings.MPESA_PASSKEY}{timestamp}".encode()).decode()

def get_timestamp():
    from datetime import datetime
    return datetime.now().strftime("%Y%m%d%H%M%S")

@login_required
def processing_payment(request, transaction_id):
    transaction = get_object_or_404(Transaction, id=transaction_id)

    if request.method == 'POST':
        access_token = get_access_token()
        query_url = f"{settings.MPESA_API_URL}/mpesa/stkpushquery/v1/query"
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        }
        payload = {
            "BusinessShortCode": settings.MPESA_EXPRESS_SHORTCODE,
            "Password": generate_password(),
            "Timestamp": get_timestamp(),
            "CheckoutRequestID": transaction.checkout_request_id,
        }

        response = requests.post(query_url, json=payload, headers=headers)
        if response.status_code == 200:
            result_code = response.json().get('ResultCode')
            if result_code == '0':
                transaction.status = 'success'
                transaction.save()
                return redirect(transaction.success_url)
            else:
                transaction.status = 'failed'
                transaction.save()
                messages.error(request, 'Payment failed. Please try again.')
        else:
            messages.error(request, 'Failed to check payment status. Please try again.')

    context = {
        'transaction': transaction,
    }
    return render(request, 'lipa/processing.html', context)

@csrf_exempt
def daraja_callback(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        checkout_request_id = data.get('Body').get('stkCallback').get('CheckoutRequestID')
        result_code = data.get('Body').get('stkCallback').get('ResultCode')

        transaction = Transaction.objects.get(checkout_request_id=checkout_request_id)
        if result_code == 0:
            transaction.status = 'success'
            transaction.receipt_no = data.get('Body').get('stkCallback').get('CallbackMetadata').get('Item')[1].get('Value')
        else:
            transaction.status = 'failed'
            transaction.error_message = data.get('Body').get('stkCallback').get('ResultDesc')
        transaction.save()

    return HttpResponse(status=200)