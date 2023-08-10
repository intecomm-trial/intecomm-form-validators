from edc_constants.constants import FORMER_SMOKER, SMOKER, YES
from edc_crf.crf_form_validator_mixins import CrfFormValidatorMixin
from edc_dx_review.utils import raise_if_clinical_review_does_not_exist
from edc_form_validators import FormValidator


class OtherBaselineDataFormValidator(CrfFormValidatorMixin, FormValidator):
    def clean(self):
        raise_if_clinical_review_does_not_exist(self.cleaned_data.get("subject_visit"))
        self.required_if(SMOKER, field="smoking_status", field_required="smoker_duration")
        self.required_if(
            FORMER_SMOKER, field="smoking_status", field_required="smoker_quit_ago"
        )
        self.applicable_if(YES, field="alcohol", field_applicable="alcohol_consumption")
        self.required_if(
            YES, field="activity_work", field_required="activity_work_days_per_wk"
        )
        self.validate_other_specify(
            field="employment_status", other_specify_field="employment_status_other"
        )
