from edc_crf.crf_form_validator_mixins import CrfFormValidatorMixin
from edc_form_validators import FormValidator
from edc_rx.utils import validate_total_days

from .mixins import DrugRefillFormValidatorMixin


class DrugRefillHivFormValidator(
    DrugRefillFormValidatorMixin, CrfFormValidatorMixin, FormValidator
):
    def clean(self):
        validate_total_days(self, return_in_days=self.cleaned_data.get("return_in_days"))
