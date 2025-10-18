from django.test import SimpleTestCase

from django_verify_vat_number.utils.country import get_country_name


class TestCountry(SimpleTestCase):

    def test_code_none(self):
        self.assertEqual(get_country_name(None), '')

    def test_lang_none(self):
        self.assertEqual(get_country_name('CZ'), 'Czechia')

    def test_lang_cs(self):
        self.assertEqual(get_country_name('CZ', 'cs'), 'Česko')

    def test_param_numeric(self):
        self.assertEqual(get_country_name('203', country_ident_type='numeric'), 'Czechia')

    def test_invalid_code(self):
        self.assertEqual(get_country_name('FOO'), '')
