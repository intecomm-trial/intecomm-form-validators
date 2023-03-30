from dateutil.relativedelta import relativedelta
from edc_constants.constants import YES
from edc_crf.crf_form_validator_mixins import CrfFormValidatorMixin
from edc_dx_review.constants import DRUGS, INSULIN
from edc_dx_review.utils import (
    raise_if_both_ago_and_actual_date,
    raise_if_clinical_review_does_not_exist,
)
from edc_form_validators import INVALID_ERROR
from edc_form_validators.form_validator import FormValidator
from edc_glucose.form_validators import GlucoseFormValidatorMixin
from edc_model.utils import estimated_date_from_ago


class DmInitialReviewFormValidator(
    GlucoseFormValidatorMixin,
    CrfFormValidatorMixin,
    FormValidator,
):
    def clean(self):
        raise_if_clinical_review_does_not_exist(self.cleaned_data.get("subject_visit"))
        raise_if_both_ago_and_actual_date(cleaned_data=self.cleaned_data)
        self.required_if(
            DRUGS,
            INSULIN,
            field="managed_by",
            field_required="med_start_ago",
        )

        self.validate_other_specify(field="managed_by", other_specify_field="managed_by_other")

        if self.cleaned_data.get("dx_ago") and self.cleaned_data.get("med_start_ago"):
            est_dx_dte = estimated_date_from_ago(
                cleaned_data=self.cleaned_data, ago_field="dx_ago"
            )
            est_med_start_dte = estimated_date_from_ago(
                cleaned_data=self.cleaned_data, ago_field="med_start_ago"
            )
            if (est_dx_dte - est_med_start_dte).days > 1:
                self.raise_validation_error(
                    {"med_start_ago": "Invalid. Cannot be before diagnosis."}, INVALID_ERROR
                )
        self.required_if(YES, field="glucose_performed", field_required="glucose_date")
        if self.cleaned_data.get("glucose_date") and self.cleaned_data.get("report_datetime"):
            rdelta = relativedelta(
                self.cleaned_data.get("report_datetime"),
                self.cleaned_data.get("glucose_date"),
            )
            months = rdelta.months + (12 * rdelta.years)
            if months >= 6 or months < 0:
                if months < 0:
                    msg = "Invalid. Cannot be a future date."
                else:
                    msg = f"Invalid. Must be within the last 6 months. Got {abs(months)}m ago."
                self.raise_validation_error(
                    {"glucose_date": msg},
                    INVALID_ERROR,
                )
        self.validate_glucose_test()
