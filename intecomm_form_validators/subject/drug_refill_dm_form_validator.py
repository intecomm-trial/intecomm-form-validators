from edc_crf.crf_form_validator_mixins import CrfFormValidatorMixin
from edc_dx_review.utils import medications_exists_or_raise
from edc_form_validators import FormValidator

from .mixins import DrugRefillFormValidatorMixin


class DrugRefillDmFormValidator(
    DrugRefillFormValidatorMixin, CrfFormValidatorMixin, FormValidator
):
    def clean(self):
        medications_exists_or_raise(self.cleaned_data.get("subject_visit"))
        self.validate_rx_as_m2m()
        self.validate_modifications()
