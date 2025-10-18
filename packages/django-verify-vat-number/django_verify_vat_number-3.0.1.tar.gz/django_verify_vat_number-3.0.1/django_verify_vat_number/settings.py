"""Verify VAT number settings."""
from appsettings import AppSettings, IntegerSetting


class VerifyVatSettings(AppSettings):
    """Verify VAT number class."""

    keep_in_cache = IntegerSetting(default=86400)  # Keep in cache for one day.

    class Meta:
        """Meta class."""

        setting_prefix = 'verify_vat_'


VERIFY_VAT_SETTINGS = VerifyVatSettings()
