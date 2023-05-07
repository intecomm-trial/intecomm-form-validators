from edc_crf.crf_form_validator_mixins import CrfFormValidatorMixin
from edc_dx import get_diagnosis_labels
from edc_dx.form_validators import DiagnosisFormValidatorMixin
from edc_form_validators import FormValidator


class MedicationsFormValidator(
    DiagnosisFormValidatorMixin, CrfFormValidatorMixin, FormValidator
):
    def clean(self) -> None:
        for dx, label in get_diagnosis_labels().items():
            self.applicable_if_diagnosed(
                diagnoses=self.get_diagnoses(),
                prefix=dx,
                field_applicable=f"refill_{dx}",
                label=label,
            )
