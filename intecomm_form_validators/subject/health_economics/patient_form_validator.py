from edc_constants.constants import DONT_KNOW, NONE, OTHER
from edc_crf.crf_form_validator_mixins import CrfFormValidatorMixin
from edc_crf.utils import raise_if_crf_does_not_exist
from edc_dx_review.utils import raise_if_clinical_review_does_not_exist
from edc_form_validators import FormValidator


class HealthEconomicsPatientFormValidator(
    CrfFormValidatorMixin,
    FormValidator,
):
    def clean(self):
        raise_if_clinical_review_does_not_exist(self.cleaned_data.get("subject_visit"))
        raise_if_crf_does_not_exist(
            self.cleaned_data.get("subject_visit"),
            model="intecomm_subject.healtheconomicshouseholdhead",
        )

        self.validate_other_specify(field="pat_religion")
        self.validate_other_specify(field="pat_ethnicity")
        self.validate_other_specify(field="pat_education")
        self.validate_other_specify(field="pat_marital_status")
        self.m2m_single_selection_if(DONT_KNOW, NONE, m2m_field="pat_insurance")
        self.m2m_other_specify(
            OTHER, m2m_field="pat_insurance", field_other="pat_insurance_other"
        )
