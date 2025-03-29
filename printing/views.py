from django.shortcuts import render


def home(request):
     return render(request, 'printing/home.html', {'title': 'Printing'})
