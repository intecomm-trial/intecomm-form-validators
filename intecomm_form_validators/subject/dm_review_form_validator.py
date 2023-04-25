from edc_crf.crf_form_validator_mixins import CrfFormValidatorMixin
from edc_dx_review.utils import raise_if_clinical_review_does_not_exist
from edc_form_validators import FormValidator
from edc_glucose.form_validators import GlucoseFormValidatorMixin


class DmReviewFormValidator(
    GlucoseFormValidatorMixin,
    CrfFormValidatorMixin,
    FormValidator,
):
    prefix = "glucose"

    def clean(self):
        raise_if_clinical_review_does_not_exist(self.cleaned_data.get("subject_visit"))
        self.validate_glucose_test()
