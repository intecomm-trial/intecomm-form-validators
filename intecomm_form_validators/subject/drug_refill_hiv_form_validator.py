from edc_crf.crf_form_validator_mixins import CrfFormValidatorMixin
from edc_dx_review.utils import medications_exists_or_raise
from edc_form_validators import FormValidator
from edc_rx.utils import TotalDaysMismatch, validate_total_days

from .mixins import DrugRefillFormValidatorMixin

TOTAL_DAYS_MISMATCH_ERROR = "TOTAL_DAYS_MISMATCH"


class DrugRefillHivFormValidator(
    DrugRefillFormValidatorMixin, CrfFormValidatorMixin, FormValidator
):
    def clean(self):
        medications_exists_or_raise(self.cleaned_data.get("subject_visit"))
        self.validate_rx_as_fk()
        self.validate_modifications()

        try:
            validate_total_days(self, rx_days=self.cleaned_data.get("rx_days"))
        except TotalDaysMismatch as e:
            self.raise_validation_error(
                {
                    "clinic_days": str(e),
                    "club_days": str(e),
                    "purchased_days": str(e),
                },
                TOTAL_DAYS_MISMATCH_ERROR,
            )
