"""Test settings."""

SECRET_KEY = "secret"

INSTALLED_APPS = (
    # the project
    'django_verify_vat_number',
)

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": "tests",
    }
}

LANGUAGES = (
    ('en', 'English'),
    ('cs', 'Česky'),
)
