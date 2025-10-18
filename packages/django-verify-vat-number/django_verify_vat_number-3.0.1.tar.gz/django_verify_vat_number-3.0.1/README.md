# Django Verify VAT registration number

The *Django Verify VAT registration number* module is an extension of the [Verify VAT registration number](https://gitlab.nic.cz/utils/verify-vat-number) project for the [Django](https://www.djangoproject.com/) framework. It is used for verification *VAT registration number* in EU and *VAT identification number* in Czechia. This module is used in the [DjangoCMS Verify VAT registration number](https://gitlab.nic.cz/djangocms-apps/djangocms-verify-vat-number) module.


## VIES

[VIES VAT number validation for European union](https://ec.europa.eu/taxation_customs/vies). It is an electronic mean of validating VAT-identification numbers of economic operators registered in the European Union for cross border transactions on goods or services. Supported countries see README in project [Verify VAT - VIES](https://gitlab.nic.cz/utils/verify-vat-number#vies).

## ARES

[ARES](https://wwwinfo.mfcr.cz) - Access to Registers of Economic Subjects / Entities is an information system allowing a retrieval of information on economic entities registered in the Czech Republic. This system intermediates a display of data from particular registers of the state administration (called source registers) in which the data concerned is kept.


## Installation

This library is available on PyPI, it's recommended to install it using `pip`:

```shell
pip install django-verify-vat-number
```

### Append into Django apps and urls

Insert into site `settings.py`:

```python
INSTALLED_APPS = [
    ...
    'django_verify_vat_number',
]
```

Insert into site `urls.py`:

```python
from django.urls import path, include

urlpatterns = [
    ....
    path('verify-vat/', include('django_verify_vat_number.urls')),
]
```

## Usage

Follow instructions [Writing your first Django app](https://docs.djangoproject.com/en/4.0/intro/tutorial01/) to launch the site.
Then you can make verification:

```
curl http://127.0.0.1:8000/verify-vat/verify-vat-id-number/?number=67985726

{"status": "OK", "message": null, "company": {
    "company_name": "CZ.NIC, z.s.p.o.",
    "address": "Mile\u0161ovsk\u00e1 1136/5\n13000 Praha 3",
    "street_and_num": "Mile\u0161ovsk\u00e1 1136/5",
    "city": "Praha 3",
    "postal_code": "13000",
    "district": "Praha 3 - Vinohrady",
    "country_code": "CZ"
}, "country": "Czechia"}

curl http://127.0.0.1:8000/verify-vat/verify-vat-reg-number/?number=CZ67985726

{"status": "OK", "message": null, "company": {
    "company_name": "CZ.NIC, z.s.p.o.",
    "address": "Mile\u0161ovsk\u00e1 1136/5\nPRAHA 3 - VINOHRADY\n130 00  PRAHA 3",
    "street_and_num": "Mile\u0161ovsk\u00e1 1136/5",
    "city": "PRAHA 3",
    "postal_code": "130 00",
    "district": "PRAHA 3 - VINOHRADY",
    "country_code": "CZ"
}, "country": "Czechia"}
```

### Country name in current site language

The country name is translated into the current site language.

Define languages in `settings.py`:

```python
LANGUAGES = [
    ('en', 'English'),
    ('cs', 'Česky'),
    ('fr', 'Francais'),
]

MIDDLEWARE = [
    ...
    'django.middleware.locale.LocaleMiddleware',
]
```

Enable language prefix in `url.py`:

```python
urlpatterns += i18n_patterns(
    path('verify-vat/', include('django_verify_vat_number.urls')),
)
 ```

Get translated country name:

```
curl http://127.0.0.1:8000/cs/verify-vat/verify-vat-id-number/?number=67985726

{"status": "OK", "message": null, "company": {"company_name": ... "country_code": "CZ"},
 "country": "\u010cesko"}

curl http://127.0.0.1:8000/fr/verify-vat/verify-vat-id-number/?number=67985726
{"status": "OK", "message": null, "company": {"company_name": ... "country_code": "CZ"},
 "country": "Tch\u00e9quie"}
 ```

### Cache

The data downloaded from the server is cached. At the next query, they are no longer downloaded
from the verification service. The default cache value is one day.
The duration of the data in the cache can be reset in the settings by the constant `VERIFY_VAT_KEEP_IN_CACHE`.

### Logging

Temporary unavailability of the resource is logged in the `INFO` level.
An unexpected error is logged in the `ERROR` level, including the source response.

Example of a temporarily unavailable service:

```
2022-06-16 14:49:33,806 INFO     ares:get_xml_content:27 https://wwwinfo.mfcr.cz/cgi-bin/ares/darv_std.cgi?ico=67985726
2022-06-16 14:49:33,815 INFO     fetchers:fetch_from_ares:47 Service is temporarily unavailable. Please, try later.
```

Example of a unexpected service failure:

```
022-06-16 14:55:10,039 INFO     ares:get_xml_content:27 https://wwwinfo.mfcr.cz/cgi-bin/ares/darv_std.cgi?ico=67985726
2022-06-16 14:55:10,042 ERROR    fetchers:fetch_from_ares:49 not well-formed (invalid token): line 1, column 11
2022-06-16 14:55:10,042 ERROR    fetchers:fetch_from_ares:50 <are:Error><dtt:Error_kod> ...
```

If you want to debug complete communication, you can set it in loggers `django_verify_vat_number.fetchers` and `verify_vat_number.ares`, `verify_vat_number.vies`.

In `settings.py`:

```python
LOGGING = {
    ...
    'loggers': {
        'verify_vat_number.ares': {'handlers': ['console'], 'level': 'DEBUG'},
        'verify_vat_number.vies': {'handlers': ['console'], 'level': 'DEBUG'},
        'django_verify_vat_number.fetchers': {'handlers': ['console'], 'level': 'DEBUG'},
    }
}
```

```
2022-06-16 15:03:04,078 INFO     ares:get_xml_content:27 https://wwwinfo.mfcr.cz/cgi-bin/ares/darv_std.cgi?ico=67985726
2022-06-16 15:03:04,078 INFO     ares:get_xml_content:27 https://wwwinfo.mfcr.cz/cgi-bin/ares/darv_std.cgi?ico=67985726
2022-06-16 15:03:05,401 DEBUG    ares:get_xml_content:38 <?xml version="1.0" encoding="UTF-8"?><are:Ares_odpovedi
    ...
<are:Odpoved>
<are:Pocet_zaznamu>1</are:Pocet_zaznamu>
    ...
</are:Odpoved>
</are:Ares_odpovedi>
2022-06-16 15:10:39,020 INFO     fetchers:fetch_from_ares:30 Cached data: VerifiedCompanyResponse(status=<StatusCode.OK: 'OK'>, message=None, company=VerifiedCompany(company_name='CZ.NIC, z.s.p.o.', address='Milešovská 1136/5\n13000 Praha 3', street_and_num='Milešovská 1136/5', city='Praha 3', postal_code='13000', district='Praha 3 - Vinohrady', country_code='CZ'), country='Česko')
```

## License

[GPLv3+](https://www.gnu.org/licenses/gpl-3.0.html)
