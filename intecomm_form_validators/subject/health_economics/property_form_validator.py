from edc_constants.constants import YES
from edc_crf.crf_form_validator_mixins import CrfFormValidatorMixin
from edc_crf.utils import raise_if_crf_does_not_exist
from edc_dx_review.utils import raise_if_clinical_review_does_not_exist
from edc_form_validators import FormValidator


class HealthEconomicsPropertyFormValidator(
    CrfFormValidatorMixin,
    FormValidator,
):
    def clean(self):
        raise_if_clinical_review_does_not_exist(self.cleaned_data.get("subject_visit"))
        raise_if_crf_does_not_exist(
            self.cleaned_data.get("subject_visit"),
            model="intecomm_subject.healtheconomicshouseholdhead",
        )
        raise_if_crf_does_not_exist(
            self.cleaned_data.get("subject_visit"),
            model="intecomm_subject.healtheconomicspatient",
        )
        raise_if_crf_does_not_exist(
            self.cleaned_data.get("subject_visit"),
            model="intecomm_subject.healtheconomicsassets",
        )
        self.applicable_if(YES, field="land_owner", field_applicable="land_value_known")
        self.required_if(YES, field="land_value_known", field_required="land_value")
        self.applicable_if(
            YES, field="land_additional", field_applicable="land_additional_known"
        )
        self.required_if(
            YES, field="land_additional_known", field_required="land_additional_value"
        )
