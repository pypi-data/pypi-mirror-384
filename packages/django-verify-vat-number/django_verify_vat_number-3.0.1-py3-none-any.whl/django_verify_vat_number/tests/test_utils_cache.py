from django.test import SimpleTestCase

from django_verify_vat_number.utils.cache import get_cache_key_ares, get_cache_key_vies


class TestUtilsCache(SimpleTestCase):

    def test_get_cache_key_ares(self):
        self.assertEqual(get_cache_key_ares('123456789'), 'vvn_ares_123456789')

    def test_get_cache_key_vies(self):
        self.assertEqual(get_cache_key_vies('123456789'), 'vvn_vies_123456789')
