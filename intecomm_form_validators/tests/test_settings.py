import sys
from pathlib import Path

from edc_test_settings.default_test_settings import DefaultTestSettings

app_name = "intecomm_form_validators"
base_dir = Path(__file__).absolute().parent.parent.parent

project_settings = DefaultTestSettings(
    calling_file=__file__,
    BASE_DIR=base_dir,
    APP_NAME=app_name,
    SITE_ID=101,
    EDC_DX_LABELS=dict(hiv="HIV", dm="Diabetes", htn="Hypertension"),
    INSTALLED_APPS=[
        "django.contrib.admin",
        "django.contrib.auth",
        "django.contrib.sites",
        "django.contrib.contenttypes",
        "django.contrib.sessions",
        "django.contrib.messages",
        "django.contrib.staticfiles",
        "intecomm_form_validators.apps.AppConfig",
    ],
).settings

for k, v in project_settings.items():
    setattr(sys.modules[__name__], k, v)
