import logging

import responses
from django.core import cache
from django.test import SimpleTestCase
from requests.exceptions import RequestException, Timeout
from verify_vat_number.ares import ECONOMIC_ENTITY, SERVICE_API_URL
from verify_vat_number.data import VerifiedCompany
from verify_vat_number.tests.test_ares import data_json_response
from verify_vat_number.tests.test_vies import get_envelope, get_envelope_vat_is_false, get_wsdl_content

from django_verify_vat_number.fetchers import StatusCode, VerifiedCompanyResponse, fetch_from_ares, fetch_from_vies

LOGGER_NAME = 'django_verify_vat_number.fetchers'


class TestFetcherAres(SimpleTestCase):

    keep_in_cache = 60
    lang_code = 'en'
    verified_company = VerifiedCompany(
        company_name='CZ.NIC, z.s.p.o.',
        address='Milešovská 1136/5\n13000 Praha 3',
        street_and_num='Milešovská 1136/5',
        city='Praha 3',
        postal_code='13000',
        district='Praha 3 - Vinohrady',
        country_code='CZ',
        legal_form=751
    )
    response_ok = VerifiedCompanyResponse(
        status=StatusCode.OK,
        message=None,
        company=verified_company,
        country='Czechia'
    )

    def setUp(self):
        cache.cache.clear()

    def test_invlaid_number(self):
        response = fetch_from_ares('!', self.keep_in_cache, self.lang_code)
        self.assertEqual(response, VerifiedCompanyResponse(status=StatusCode.ERROR, message='Invalid number.'))

    def test_too_long_number(self):
        response = fetch_from_ares('123456789', self.keep_in_cache, self.lang_code)
        self.assertEqual(response, VerifiedCompanyResponse(status=StatusCode.ERROR,
                         message='Invalid number. It has more than 8 digits.'))

    def test_get_from_backend(self):
        with self.assertLogs(LOGGER_NAME, level='INFO') as logs:
            with responses.RequestsMock() as mock:
                mock.add(responses.GET, f'{SERVICE_API_URL}/{ECONOMIC_ENTITY}/67985726/', body=data_json_response())
                response = fetch_from_ares('67985726', self.keep_in_cache, self.lang_code)
            logging.getLogger(LOGGER_NAME).info('OK')
        self.assertEqual(response, self.response_ok)
        self.assertEqual(cache.cache.get('vvn_ares_67985726'), self.response_ok)
        self.assertEqual(logs.output, ['INFO:django_verify_vat_number.fetchers:OK'])

    def test_get_from_cache(self):
        cache.cache.set('vvn_ares_67985726', self.response_ok)
        with responses.RequestsMock():
            response = fetch_from_ares('67985726', self.keep_in_cache, 'cz')
        self.assertEqual(response, VerifiedCompanyResponse(
            status=StatusCode.OK, message=None, company=self.verified_company, country='Česko'))

    def test_get_from_cache_not_ok(self):
        cache.cache.set('vvn_ares_67985726', VerifiedCompanyResponse(
            status=StatusCode.ERROR, message="Error", company=None, country='Czechia'))
        with responses.RequestsMock():
            response = fetch_from_ares('67985726', self.keep_in_cache, 'cz')
        self.assertEqual(response, VerifiedCompanyResponse(
            status=StatusCode.ERROR, message="Error", company=None, country='Czechia'))

    def test_vat_not_found(self):
        with responses.RequestsMock() as mock:
            mock.add(responses.GET, f'{SERVICE_API_URL}/{ECONOMIC_ENTITY}/67985726/', status=404, body='')
            response = fetch_from_ares('67985726', self.keep_in_cache, self.lang_code)
        self.assertEqual(response, VerifiedCompanyResponse(
            status=StatusCode.NOTFOUND, message=None, company=None, country=None))

    def test_invalid_number(self):
        with responses.RequestsMock() as mock:
            mock.add(responses.GET, f'{SERVICE_API_URL}/{ECONOMIC_ENTITY}/67985726/', status=400, body='')
            response = fetch_from_ares('67985726', self.keep_in_cache, self.lang_code)
        self.assertEqual(response, VerifiedCompanyResponse(
            status=StatusCode.INVALID_INPUT, message='Input error.', company=None, country=None))

    def test_timeout(self):
        with responses.RequestsMock() as mock:
            mock.add(responses.GET, f'{SERVICE_API_URL}/{ECONOMIC_ENTITY}/67985726/', body=Timeout())
            response = fetch_from_ares('67985726', self.keep_in_cache, self.lang_code)
        self.assertEqual(response, VerifiedCompanyResponse(
            status=StatusCode.ERROR, message='Service is temporarily unavailable. Please, try later.',
            company=None, country=None))

    def test_timeout_message(self):
        with responses.RequestsMock() as mock:
            mock.add(responses.GET, f'{SERVICE_API_URL}/{ECONOMIC_ENTITY}/67985726/', body=Timeout("Unavailable."))
            response = fetch_from_ares('67985726', self.keep_in_cache, self.lang_code)
        self.assertEqual(response, VerifiedCompanyResponse(
            status=StatusCode.ERROR, message='Unavailable.',
            company=None, country=None))

    def test_verify_vat_exception(self):
        with self.assertLogs(LOGGER_NAME, level='INFO') as logs:
            with responses.RequestsMock() as mock:
                mock.add(responses.GET, f'{SERVICE_API_URL}/{ECONOMIC_ENTITY}/67985726/',
                         body=RequestException('The error.'))
                response = fetch_from_ares('67985726', self.keep_in_cache, self.lang_code)
            self.assertEqual(response, VerifiedCompanyResponse(
                status=StatusCode.ERROR, message='The error.', company=None, country=None))
        self.assertEqual(logs.output, [
            'ERROR:django_verify_vat_number.fetchers:The error.',
            'ERROR:django_verify_vat_number.fetchers:'
        ])


class TestFetcherVies(SimpleTestCase):

    keep_in_cache = 60
    lang_code = 'en'
    url = 'https://ec.europa.eu/taxation_customs/vies/checkVatService.wsdl'
    service_url = 'https://ec.europa.eu/taxation_customs/vies/services/checkVatService'
    address = "Milešovská 1136/5\nPRAHA 3 - VINOHRADY\n130 00  PRAHA 3"
    verified_company = VerifiedCompany(
        company_name='CZ.NIC, z.s.p.o.',
        address='Milešovská 1136/5\nPRAHA 3 - VINOHRADY\n130 00  PRAHA 3',
        street_and_num='Milešovská 1136/5',
        city='PRAHA 3',
        postal_code='130 00',
        district='PRAHA 3 - VINOHRADY',
        country_code='CZ'
    )
    response_ok = VerifiedCompanyResponse(
        status=StatusCode.OK,
        message=None,
        company=verified_company,
        country='Czechia'
    )

    def setUp(self):
        cache.cache.clear()

    def test_invalid_number(self):
        response = fetch_from_vies('!', self.keep_in_cache, self.lang_code)
        self.assertEqual(response, VerifiedCompanyResponse(status=StatusCode.ERROR, message='Invalid number.'))

    def test_get_from_backend(self):
        with self.assertLogs(LOGGER_NAME, level='INFO') as logs:
            with responses.RequestsMock() as mock:
                mock.add(responses.GET, self.url, body=get_wsdl_content())
                mock.add(responses.POST, self.service_url, body=get_envelope(self.address))
                response = fetch_from_vies('CZ67985726', self.keep_in_cache, self.lang_code)
            logging.getLogger(LOGGER_NAME).info('OK')
        self.assertEqual(response, self.response_ok)
        self.assertEqual(logs.output, ['INFO:django_verify_vat_number.fetchers:OK'])

    def test_get_from_cache(self):
        cache.cache.set('vvn_vies_CZ67985726', self.response_ok)
        with responses.RequestsMock():
            response = fetch_from_vies('CZ67985726', self.keep_in_cache, 'cz')
        self.assertEqual(response, VerifiedCompanyResponse(
            status=StatusCode.OK, message=None, company=self.verified_company, country='Česko'))

    def test_get_from_cache_not_ok(self):
        cache.cache.set('vvn_vies_CZ67985726', VerifiedCompanyResponse(
            status=StatusCode.ERROR, message="Error", company=None, country='Czechia'))
        with responses.RequestsMock():
            response = fetch_from_vies('CZ67985726', self.keep_in_cache, 'cz')
        self.assertEqual(response, VerifiedCompanyResponse(
            status=StatusCode.ERROR, message="Error", company=None, country='Czechia'))

    def test_vat_not_found(self):
        with responses.RequestsMock() as mock:
            mock.add(responses.GET, self.url, body=get_wsdl_content())
            mock.add(responses.POST, self.service_url, body=get_envelope_vat_is_false())
            response = fetch_from_vies('CZ67985726', self.keep_in_cache, self.lang_code)
        self.assertEqual(response, VerifiedCompanyResponse(
            status=StatusCode.NOTFOUND, message=None, company=None, country=None))

    def test_unsupported_country_code(self):
        with responses.RequestsMock():
            response = fetch_from_vies('GB123456789', self.keep_in_cache, self.lang_code)
        self.assertEqual(response, VerifiedCompanyResponse(
            status=StatusCode.INVALID_COUNTRY_CODE, message=None, company=None, country=None))

    def test_service_temporarily_unavailable(self):
        with self.assertLogs(LOGGER_NAME, level='INFO') as logs:
            with responses.RequestsMock() as mock:
                mock.add(responses.GET, self.url, body=Timeout('Time is out.'))
                response = fetch_from_vies('CZ67985726', self.keep_in_cache, self.lang_code)
        self.assertEqual(response, VerifiedCompanyResponse(
            status=StatusCode.ERROR,
            message='Time is out.',
            company=None,
            country=None)
        )
        self.assertEqual(logs.output, [
            'INFO:django_verify_vat_number.fetchers:Time is out.'
        ])

    def test_verify_vat_exception(self):
        with self.assertLogs(LOGGER_NAME, level='INFO') as logs:
            with responses.RequestsMock() as mock:
                mock.add(responses.GET, self.url, body=RequestException('The error.'))
                response = fetch_from_vies('CZ67985726', self.keep_in_cache, self.lang_code)
        self.assertEqual(response, VerifiedCompanyResponse(
            status=StatusCode.ERROR, message='The error.', company=None, country=None)
        )
        self.assertEqual(logs.output, [
            'ERROR:django_verify_vat_number.fetchers:The error.',
            'ERROR:django_verify_vat_number.fetchers:'
        ])
