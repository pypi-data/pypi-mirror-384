"""Url Django vertify VAT number."""
from django.urls import path

from .views.verifiers import GetFromAres, GetFromVies

urlpatterns = [
    path('verify-vat-id-number/', GetFromAres.as_view(), name='verify_vat_id_number'),
    path('verify-vat-reg-number/', GetFromVies.as_view(), name='verify_vat_reg_number'),
]
