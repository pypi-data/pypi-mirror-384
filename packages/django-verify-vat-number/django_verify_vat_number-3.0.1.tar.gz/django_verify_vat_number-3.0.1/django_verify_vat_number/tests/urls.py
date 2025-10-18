"""Test urls."""

from django.urls import include, path

urlpatterns = [
    path('verify-vat/', include('django_verify_vat_number.urls')),
]
