from edc_constants.constants import NO, YES
from edc_crf.crf_form_validator import CrfFormValidator
from edc_dx import get_diagnosis_labels
from edc_dx_review.form_validator_mixins import ClinicalReviewBaselineFormValidatorMixin
from edc_screening.utils import get_subject_screening_model_cls

INVALID_DX = "INVALID_DX"


class ClinicalReviewBaselineFormValidator(
    ClinicalReviewBaselineFormValidatorMixin, CrfFormValidator
):
    def clean(self) -> None:
        for dx, label in get_diagnosis_labels().items():
            screening_dx = getattr(self.subject_screening, f"{dx}_dx", "")
            dx = self.cleaned_data.get(f"{dx}_dx")
            if dx and screening_dx:
                if screening_dx == YES and dx != YES:
                    self.raise_validation_error(
                        f"Expected YES. {label.title()} "
                        "diagnosis was reported on Screening form",
                        INVALID_DX,
                    )
                elif screening_dx == NO and dx != NO:
                    self.raise_validation_error(
                        f"Expected {screening_dx}. {label.title()} "
                        "diagnosis was not reported on the screening form",
                        INVALID_DX,
                    )

    @property
    def subject_screening(self):
        return get_subject_screening_model_cls().objects.get(
            subject_identifier=self.subject_identifier
        )
