"""Get country name by code or numeric."""
import gettext
from typing import Optional

import pycountry


def get_country_name(country_code: Optional[str], lang: Optional[str] = None,
                     country_ident_type: str = 'alpha_2') -> str:
    """Get country name."""
    if country_code is None:
        return ''
    country = pycountry.countries.get(**{country_ident_type: country_code})
    if country is not None:
        if lang:
            try:
                trans = gettext.translation('iso3166-1', pycountry.LOCALES_DIR, languages=[lang])
            except FileNotFoundError:
                return country.name
            return trans.gettext(country.name)
        return country.name
    return ''
