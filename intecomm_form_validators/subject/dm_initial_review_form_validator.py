from edc_constants.constants import YES
from edc_crf.crf_form_validator_mixins import CrfFormValidatorMixin
from edc_dx_review.constants import DRUGS, INSULIN
from edc_dx_review.form_validator_mixins import InitialReviewFormValidatorMixin
from edc_dx_review.utils import raise_if_clinical_review_does_not_exist
from edc_form_validators.form_validator import FormValidator
from edc_glucose.form_validators import GlucoseFormValidatorMixin


class DmInitialReviewFormValidator(
    InitialReviewFormValidatorMixin,
    GlucoseFormValidatorMixin,
    CrfFormValidatorMixin,
    FormValidator,
):
    fasting_fld = "glucose_fasting"

    def clean(self):
        raise_if_clinical_review_does_not_exist(self.cleaned_data.get("subject_visit"))
        self.raise_if_both_dx_ago_and_dx_date()
        self.required_if_m2m(
            DRUGS,
            INSULIN,
            field="managed_by",
            field_required="med_start_ago",
        )

        self.m2m_other_specify(m2m_field="managed_by", field_other="managed_by_other")

        reference_field = "dx_date" if self.cleaned_data.get("dx_date") else "dx_ago"
        self.date_is_after_or_raise(
            field="med_start_ago", reference_field=reference_field, inclusive=True
        )

        self.required_if(YES, field="glucose_performed", field_required="glucose_date")

        self.validate_test_date_within_6m(date_fld="glucose_date")

        self.validate_glucose_test()
