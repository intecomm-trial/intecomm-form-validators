from django import forms
from edc_crf.crf_form_validator_mixins import CrfFormValidatorMixin
from edc_dx_review.constants import DRUGS
from edc_dx_review.utils import (
    raise_if_both_ago_and_actual_date,
    raise_if_clinical_review_does_not_exist,
)
from edc_form_validators.form_validator import FormValidator
from edc_model.utils import estimated_date_from_ago


class HtnInitialReviewFormValidator(
    CrfFormValidatorMixin,
    FormValidator,
):
    def clean(self):
        raise_if_clinical_review_does_not_exist(self.cleaned_data.get("subject_visit"))
        raise_if_both_ago_and_actual_date(cleaned_data=self.cleaned_data)
        self.required_if(DRUGS, field="managed_by", field_required="med_start_ago")
        if self.cleaned_data.get("med_start_ago") and self.cleaned_data.get("dx_ago"):
            if estimated_date_from_ago(
                cleaned_data=self.cleaned_data, ago_field="med_start_ago"
            ) < estimated_date_from_ago(cleaned_data=self.cleaned_data, ago_field="dx_ago"):
                raise forms.ValidationError(
                    {"med_start_ago": "Invalid. Cannot be before diagnosis."}
                )
