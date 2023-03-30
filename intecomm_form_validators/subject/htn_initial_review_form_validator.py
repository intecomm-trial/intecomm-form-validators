from edc_crf.crf_form_validator_mixins import CrfFormValidatorMixin
from edc_dx_review.constants import DRUGS
from edc_dx_review.form_validator_mixins import InitialReviewFormValidatorMixin
from edc_dx_review.utils import (
    raise_if_both_ago_and_actual_date,
    raise_if_clinical_review_does_not_exist,
)
from edc_form_validators.form_validator import FormValidator


class HtnInitialReviewFormValidator(
    InitialReviewFormValidatorMixin,
    CrfFormValidatorMixin,
    FormValidator,
):
    def clean(self):
        raise_if_clinical_review_does_not_exist(self.cleaned_data.get("subject_visit"))
        raise_if_both_ago_and_actual_date(cleaned_data=self.cleaned_data)

        self.required_if(
            DRUGS,
            field="managed_by",
            field_required="med_start_ago",
        )

        self.validate_other_specify(field="managed_by", other_specify_field="managed_by_other")

        self.dx_before_reference_date_or_raise(reference_date_fld="med_start_ago")
