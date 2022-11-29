from edc_crf.crf_form_validator_mixins import CrfFormValidatorMixin
from edc_form_validators import FormValidator

from .mixins import DrugRefillFormValidatorMixin


class DrugRefillHtnFormValidator(
    DrugRefillFormValidatorMixin, CrfFormValidatorMixin, FormValidator
):
    pass
