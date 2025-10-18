"""Django vertify VAT number views ARES/VIES."""
import logging
from typing import cast

from django.core.cache import cache
from django.utils.translation import gettext_lazy as _
from verify_vat_number.ares import get_from_cz_ares
from verify_vat_number.data import VerifiedCompany
from verify_vat_number.exceptions import (InvalidVatNumber, ServiceTemporarilyUnavailable, UnsupportedCountryCode,
                                          VatNotFound, VerifyVatException)
from verify_vat_number.utils import strip_vat_id_number, strip_vat_reg_number
from verify_vat_number.vies import get_from_eu_vies

from .response import StatusCode, VerifiedCompanyResponse
from .utils.cache import get_cache_key_ares, get_cache_key_vies
from .utils.country import get_country_name

LOGGER = logging.getLogger(__name__)


def fetch_from_ares(vat_id_number: str, keep_in_cache: int, lang: str) -> VerifiedCompanyResponse:
    """Fetch data from ARES."""
    vat_id_number = strip_vat_id_number(vat_id_number)
    if vat_id_number == '':
        return VerifiedCompanyResponse(status=StatusCode.ERROR, message=_('Invalid number.'))
    if len(vat_id_number) > 8:
        return VerifiedCompanyResponse(
            status=StatusCode.ERROR, message=_('Invalid number. It has more than 8 digits.'))
    cache_key = get_cache_key_ares(vat_id_number)
    response = cache.get(cache_key)
    if response is not None:
        LOGGER.info("Cached data: %s", response)
        if response.status == StatusCode.OK:
            response.country = get_country_name(response.company.country_code, lang)
        return response
    try:
        response = VerifiedCompanyResponse(status=StatusCode.OK, company=get_from_cz_ares(vat_id_number))
        response.country = get_country_name(cast(VerifiedCompany, response.company).country_code, lang)
        cache.set(cache_key, response, keep_in_cache)
    except VatNotFound:
        response = VerifiedCompanyResponse(status=StatusCode.NOTFOUND)
        cache.set(cache_key, response, keep_in_cache)
    except ServiceTemporarilyUnavailable as err:
        message = str(err)
        if not message:
            message = _("Service is temporarily unavailable. Please, try later.")
        response = VerifiedCompanyResponse(status=StatusCode.ERROR, message=message)
        LOGGER.info(message)
    except InvalidVatNumber as err:
        response = VerifiedCompanyResponse(status=StatusCode.INVALID_INPUT, message=_("Input error."))
        LOGGER.info(str(err))
    except VerifyVatException as err:
        response = VerifiedCompanyResponse(status=StatusCode.ERROR, message=str(err))
        LOGGER.error(err)
        LOGGER.error(err.source)
    return response


def fetch_from_vies(vat_reg_number: str, keep_in_cache: int, lang: str) -> VerifiedCompanyResponse:
    """Fetch data from VIES."""
    vat_reg_number = strip_vat_reg_number(vat_reg_number)
    if vat_reg_number == '':
        return VerifiedCompanyResponse(status=StatusCode.ERROR, message=_('Invalid number.'))
    cache_key = get_cache_key_vies(vat_reg_number)
    response = cache.get(cache_key)
    if response is not None:
        if response.status == StatusCode.OK:
            response.country = get_country_name(response.company.country_code, lang)
        return response
    try:
        response = VerifiedCompanyResponse(status=StatusCode.OK, company=get_from_eu_vies(vat_reg_number))
        response.country = get_country_name(cast(VerifiedCompany, response.company).country_code, lang)
        cache.set(cache_key, response, keep_in_cache)
    except VatNotFound:
        response = VerifiedCompanyResponse(status=StatusCode.NOTFOUND)
        cache.set(cache_key, response, keep_in_cache)
    except UnsupportedCountryCode:
        response = VerifiedCompanyResponse(status=StatusCode.INVALID_COUNTRY_CODE)
    except ServiceTemporarilyUnavailable as err:
        message = str(err)
        if not message:
            message = _("Service is temporarily unavailable. Please, try later.")
        response = VerifiedCompanyResponse(status=StatusCode.ERROR, message=message)
        LOGGER.info(message)
    except VerifyVatException as err:
        response = VerifiedCompanyResponse(status=StatusCode.ERROR, message=str(err))
        LOGGER.error(err)
        LOGGER.error(err.source)
    return response
