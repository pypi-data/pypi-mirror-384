"""Response data."""
from dataclasses import dataclass
from enum import Enum, unique
from typing import Optional

from verify_vat_number.data import VerifiedCompany


@unique
class StatusCode(str, Enum):
    """Status code."""

    OK = 'OK'
    ERROR = 'ERROR'
    NOTFOUND = 'NOTFOUND'
    INVALID_COUNTRY_CODE = 'INVALID_COUNTRY_CODE'
    INVALID_INPUT = 'INVALID_INPUT'


@dataclass
class VerifiedCompanyResponse:
    """Company name and address verified by VAT number."""

    status: StatusCode
    message: Optional[str] = None
    company: Optional[VerifiedCompany] = None
    country: Optional[str] = None
