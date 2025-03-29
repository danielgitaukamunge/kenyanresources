from django.conf import settings
from django.conf.urls.static import static
from django.urls import path
from . import views

urlpatterns = [
    path('resources/', views.home, name='resources-home'),
    path('schemes-of-work/', views.schemes_of_work, name='schemes-of-work'),
    path('generate_schemes/', views.generate_schemes, name='generate_schemes'),
    path('generate/success/', views.generate_schemes_success, name='generate-schemes-success'),
    path('resources-history/', views.resources_history, name='resources-history'),
    path('download/<str:filename>/', views.download_resource, name='download-resource'),
    path('delete-resource/<str:filename>/', views.delete_resource, name='delete-resource'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)