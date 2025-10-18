import responses
from django.core import cache
from django.test import TestCase, override_settings
from django.urls import reverse_lazy
from django.utils import translation
from requests.exceptions import RequestException, Timeout
from verify_vat_number.ares import ECONOMIC_ENTITY, SERVICE_API_URL
from verify_vat_number.data import VerifiedCompany
from verify_vat_number.tests.test_ares import data_json_response
from verify_vat_number.tests.test_vies import get_envelope, get_envelope_vat_is_false, get_wsdl_content

from django_verify_vat_number.fetchers import StatusCode, VerifiedCompanyResponse


@override_settings(ROOT_URLCONF='django_verify_vat_number.tests.urls')
class TestGetFromAres(TestCase):

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
    verified_company_data = {
        "company_name": "CZ.NIC, z.s.p.o.",
        "address": "Milešovská 1136/5\n13000 Praha 3",
        "street_and_num": "Milešovská 1136/5",
        "city": "Praha 3",
        "postal_code": "13000",
        "district": "Praha 3 - Vinohrady",
        "country_code": "CZ",
        "legal_form": 751,
    }
    path = reverse_lazy('verify_vat_id_number')

    def setUp(self):
        cache.cache.clear()

    def test_not_param(self):
        response = self.client.get(self.path)
        self.assertJSONEqual(response.content.decode('utf-8'), {
            'status': 'ERROR',
            'message': "Parameter 'number' missing.",
            'company': None,
            'country': None,
        })

    def test_backend(self):
        with responses.RequestsMock() as mock:
            mock.add(responses.GET, f'{SERVICE_API_URL}/{ECONOMIC_ENTITY}/67985726/', body=data_json_response())
            response = self.client.get(f"{self.path}?number=67985726")
        self.assertJSONEqual(response.content.decode('utf-8'), {
            "status": "OK",
            "message": None,
            "company": self.verified_company_data,
            "country": "Czechia"
        })

    def test_cache(self):
        cache.cache.set('vvn_ares_67985726', self.response_ok)
        response = self.client.get(f"{self.path}?number=67985726")
        self.assertJSONEqual(response.content.decode('utf-8'), {
            "status": "OK",
            "message": None,
            "company": self.verified_company_data,
            "country": "Czechia"
        })

    def test_vat_not_found(self):
        with responses.RequestsMock() as mock:
            mock.add(responses.GET, f'{SERVICE_API_URL}/{ECONOMIC_ENTITY}/67985726/', status=404, body='')
            response = self.client.get(f"{self.path}?number=67985726")
        self.assertJSONEqual(response.content.decode('utf-8'), {
            "status": "NOTFOUND",
            "message": None,
            "company": None,
            "country": None,
        })

    def test_country_translation(self):
        cache.cache.set('vvn_ares_67985726', self.response_ok)
        with translation.override('cs'):
            response = self.client.get(f"{self.path}?number=67985726")
        self.assertJSONEqual(response.content.decode('utf-8'), {
            "status": "OK",
            "message": None,
            "company": self.verified_company_data,
            "country": "Česko"
        })

    def test_timeout(self):
        with responses.RequestsMock() as mock:
            mock.add(responses.GET, f'{SERVICE_API_URL}/{ECONOMIC_ENTITY}/67985726/', body=Timeout())
            response = self.client.get(f"{self.path}?number=67985726")
        self.assertJSONEqual(response.content.decode('utf-8'), {
            "status": "ERROR",
            "message": "Service is temporarily unavailable. Please, try later.",
            "company": None,
            "country": None
        })

    def test_verify_vat_exception(self):
        with responses.RequestsMock() as mock:
            mock.add(responses.GET, f'{SERVICE_API_URL}/{ECONOMIC_ENTITY}/67985726/',
                     body=RequestException('The error.'))
            response = self.client.get(f"{self.path}?number=67985726")
        self.assertJSONEqual(response.content.decode('utf-8'), {
            "status": "ERROR",
            "message": "The error.",
            "company": None,
            "country": None
        })


@override_settings(ROOT_URLCONF='django_verify_vat_number.tests.urls')
class TestGetFromVies(TestCase):

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
        country_code='CZ',
        legal_form=None
    )
    response_ok = VerifiedCompanyResponse(
        status=StatusCode.OK,
        message=None,
        company=verified_company,
        country='Czechia'
    )
    verified_company_data = {
        "company_name": "CZ.NIC, z.s.p.o.",
        "address": address,
        "street_and_num": "Milešovská 1136/5",
        "city": "PRAHA 3",
        "postal_code": "130 00",
        "district": "PRAHA 3 - VINOHRADY",
        "country_code": "CZ",
        "legal_form": None,
    }
    path = reverse_lazy('verify_vat_reg_number')

    def setUp(self):
        cache.cache.clear()

    def test_not_param(self):
        response = self.client.get(self.path)
        self.assertJSONEqual(response.content.decode('utf-8'), {
            'status': 'ERROR',
            'message': "Parameter 'number' missing.",
            'company': None,
            'country': None,
        })

    def test_backend(self):
        with responses.RequestsMock() as mock:
            mock.add(responses.GET, self.url, body=get_wsdl_content())
            mock.add(responses.POST, self.service_url, body=get_envelope(self.address))
            response = self.client.get(f"{self.path}?number=CZ67985726")
        self.assertJSONEqual(response.content.decode('utf-8'), {
            "status": "OK",
            "message": None,
            "company": self.verified_company_data,
            "country": "Czechia"
        })

    def test_vat_not_found(self):
        with responses.RequestsMock() as mock:
            mock.add(responses.GET, self.url, body=get_wsdl_content())
            mock.add(responses.POST, self.service_url, body=get_envelope_vat_is_false())
            response = self.client.get(f"{self.path}?number=CZ67985726")
        self.assertJSONEqual(response.content.decode('utf-8'), {
            "status": "NOTFOUND",
            "message": None,
            "company": None,
            "country": None,
        })

    def test_unsupported_country_code(self):
        response = self.client.get(f"{self.path}?number=GB123456789")
        self.assertJSONEqual(response.content.decode('utf-8'), {
            "status": "INVALID_COUNTRY_CODE",
            "message": None,
            "company": None,
            "country": None,
        })

    def test_service_temporarily_unavailable(self):
        with responses.RequestsMock() as mock:
            mock.add(responses.GET, self.url, body=Timeout())
            response = self.client.get(f"{self.path}?number=CZ67985726")
        self.assertJSONEqual(response.content.decode('utf-8'), {
            "status": "ERROR",
            "message": "Service is temporarily unavailable. Please, try later.",
            "company": None,
            "country": None,
        })

    def test_verify_vat_exception(self):
        with responses.RequestsMock() as mock:
            mock.add(responses.GET, self.url, body=RequestException('The error.'))
            response = self.client.get(f"{self.path}?number=CZ67985726")
        self.assertJSONEqual(response.content.decode('utf-8'), {
            "status": "ERROR",
            "message": "The error.",
            "company": None,
            "country": None,
        })
