from edc_adherence.form_validator_mixin import MedicationAdherenceFormValidatorMixin
from edc_crf.crf_form_validator_mixins import CrfFormValidatorMixin
from edc_form_validators import FormValidator


class DmMedicationAdherenceFormValidator(
    MedicationAdherenceFormValidatorMixin,
    CrfFormValidatorMixin,
    FormValidator,
):
    pass
