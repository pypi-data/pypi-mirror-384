"""Django vertify VAT number views ARES/VIES."""
import logging
from dataclasses import asdict
from typing import Any

from django.http import HttpRequest, JsonResponse
from django.utils.translation import get_language, gettext_lazy as _
from django.views import View

from ..fetchers import fetch_from_ares, fetch_from_vies
from ..response import StatusCode, VerifiedCompanyResponse
from ..settings import VERIFY_VAT_SETTINGS

LOGGER = logging.getLogger(__name__)


class GetJsonResponseView(View):
    """View GET returns JsonResponse."""

    def get(self, request: HttpRequest, *args: Any, **kwargs: Any) -> JsonResponse:
        """Get JSON response with data from ARES."""
        number = request.GET.get('number')
        if number is None:
            response = VerifiedCompanyResponse(status=StatusCode.ERROR, message=_("Parameter 'number' missing."))
        else:
            response = self.fetch_from_source(request, number)
        return JsonResponse(asdict(response))


class GetFromAres(GetJsonResponseView):
    """Get data of VAT from ARES."""

    def fetch_from_source(self, request: HttpRequest, vat_id_number: str) -> VerifiedCompanyResponse:
        """Fetch data from the source."""
        return fetch_from_ares(vat_id_number, VERIFY_VAT_SETTINGS.keep_in_cache, get_language())


class GetFromVies(GetJsonResponseView):
    """Get data of VAT from VIES."""

    def fetch_from_source(self, request: HttpRequest, vat_reg_number: str) -> VerifiedCompanyResponse:
        """Fetch data from the source."""
        return fetch_from_vies(vat_reg_number, VERIFY_VAT_SETTINGS.keep_in_cache, get_language())
