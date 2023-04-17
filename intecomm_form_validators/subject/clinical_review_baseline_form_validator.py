from edc_constants.constants import NO, YES
from edc_crf.crf_form_validator import CrfFormValidator
from edc_dx import get_diagnosis_labels
from edc_dx_review.form_validator_mixins import ClinicalReviewBaselineFormValidatorMixin
from edc_dx_review.medical_date import DATE_AND_AGO_CONFLICT
from edc_screening.utils import get_subject_screening_model_cls

INVALID_ALREADY_HAS_DX = "INVALID_ALREADY_HAS_DX"


class ClinicalReviewBaselineFormValidator(
    ClinicalReviewBaselineFormValidatorMixin,
    CrfFormValidator,
):
    @property
    def subject_screening(self):
        return get_subject_screening_model_cls().objects.get(
            subject_identifier=self.subject_identifier
        )

    def clean(self):
        for prefix, label in get_diagnosis_labels().items():
            cond = prefix.lower()
            self.validate_cond_tested_if_screening_dx(cond, label)

            self.not_required_if(
                NO, field=f"{cond}_test", field_not_required=f"{cond}_test_ago", inverse=False
            )
            self.not_required_if(
                NO, field=f"{cond}_test", field_not_required=f"{cond}_test_date", inverse=False
            )

            if self.cleaned_data.get(f"{cond}_test_date") and self.cleaned_data.get(
                f"{cond}_test_ago"
            ):
                self.raise_validation_error(
                    {
                        f"{cond}_test_ago": (
                            "Date conflict. Do not provide a response "
                            "here if test date is available."
                        )
                    },
                    DATE_AND_AGO_CONFLICT,
                )

            self.validate_date_against_report_datetime(f"{cond}_test_date")

            self.validate_cond_dx_if_screening_dx(cond, label)

    def validate_cond_tested_if_screening_dx(self, cond: str, label: str) -> None:
        """Conditions present at screening, should have been tested by baseline."""
        if (
            self.cleaned_data.get(f"{cond}_test") == NO
            and getattr(self.subject_screening, f"{cond}_dx") == YES
        ):
            self.raise_validation_error(
                {
                    f"{cond}_test": (
                        f"Invalid. "
                        f"Participant screened with `{label}` diagnosis. Expected `Yes`."
                    )
                },
                INVALID_ALREADY_HAS_DX,
            )

    def validate_cond_dx_if_screening_dx(self, cond: str, label: str) -> None:
        """Conditions present at screening, should be diagnosed at baseline."""
        if (
            self.cleaned_data.get(f"{cond}_test") == YES
            and self.cleaned_data.get(f"{cond}_dx") != YES
            and getattr(self.subject_screening, f"{cond}_dx") == YES
        ):
            self.raise_validation_error(
                {
                    f"{cond}_dx": (
                        f"Invalid. "
                        f"Participant screened with `{label}` diagnosis. Expected `Yes`."
                    )
                },
                INVALID_ALREADY_HAS_DX,
            )
