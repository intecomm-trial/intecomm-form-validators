from edc_constants.constants import NO, YES
from edc_crf.crf_form_validator import CrfFormValidator
from edc_dx import get_diagnosis_labels
from edc_dx_review.form_validator_mixins import ClinicalReviewBaselineFormValidatorMixin
from edc_screening.utils import get_subject_screening_model_cls

INVALID_DX = "INVALID_DX"
PROTOCOL_INCIDENT = "PROTOCOL_INCIDENT"


class ClinicalReviewBaselineFormValidator(
    ClinicalReviewBaselineFormValidatorMixin, CrfFormValidator
):
    def clean(self) -> None:
        protocol_incident = NO
        for cond, label in get_diagnosis_labels().items():
            if (
                self.dx(cond)
                and self.subject_screening_dx(cond)
                and self.dx_at_screening(cond)
            ):
                self.validate_dx_at_screening_or_raise(cond, label)
                if self.dx_at_screening(cond) == YES and self.dx(cond) == NO:
                    protocol_incident = YES
                elif self.dx_at_screening(cond) == NO and self.dx(cond) == YES:
                    protocol_incident = YES
        if (
            self.cleaned_data.get("protocol_incident")
            and self.cleaned_data.get("protocol_incident") != protocol_incident
        ):
            self.raise_validation_error(
                {"protocol_incident": f"Expected {protocol_incident}"}, PROTOCOL_INCIDENT
            )

    @property
    def subject_screening(self):
        return get_subject_screening_model_cls().objects.get(
            subject_identifier=self.subject_identifier
        )

    def subject_screening_dx(self, cond: str):
        return getattr(self.subject_screening, f"{cond}_dx", "")

    def dx(self, cond: str):
        return self.cleaned_data.get(f"{cond}_dx")

    def dx_at_screening(self, cond: str):
        return self.cleaned_data.get(f"{cond}_dx_at_screening")

    def validate_dx_at_screening_or_raise(self, cond, label):
        if self.subject_screening_dx(cond) != self.dx_at_screening(cond):
            if self.subject_screening_dx(cond) == YES:
                self.raise_validation_error(
                    {
                        f"{cond}_dx_at_screening": (
                            f"{label.title()} diagnosis was reported at screening"
                        )
                    },
                    INVALID_DX,
                )
            elif self.subject_screening_dx(cond) == NO:
                self.raise_validation_error(
                    {
                        f"{cond}_dx_at_screening": (
                            f"{label.title()} diagnosis was not reported at screening"
                        )
                    },
                    INVALID_DX,
                )

    def create_protocol_incident(self):
        pass
