from edc_adherence.form_validator_mixin import MedicationAdherenceFormValidatorMixin
from edc_crf.crf_form_validator_mixins import CrfFormValidatorMixin
from edc_form_validators import FormValidator


class HivMedicationAdherenceFormValidator(
    MedicationAdherenceFormValidatorMixin,
    CrfFormValidatorMixin,
    FormValidator,
):
    pass
