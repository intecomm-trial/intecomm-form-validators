from edc_crf.crf_form_validator_mixins import CrfFormValidatorMixin
from edc_dx_review.constants import DRUGS
from edc_dx_review.medical_date import DxDate, MedicalDateError, RxDate
from edc_dx_review.utils import raise_if_clinical_review_does_not_exist
from edc_form_validators import INVALID_ERROR
from edc_form_validators.form_validator import FormValidator


class HtnInitialReviewFormValidator(
    CrfFormValidatorMixin,
    FormValidator,
):
    def clean(self):
        raise_if_clinical_review_does_not_exist(self.cleaned_data.get("subject_visit"))

        try:
            dx_date = DxDate(self.cleaned_data)
        except MedicalDateError as e:
            self.raise_validation_error(e.message_dict, e.code)

        self.m2m_other_specify(m2m_field="managed_by", field_other="managed_by_other")

        selections = self.get_m2m_selected("managed_by")
        on_medications = DRUGS in selections
        if on_medications and not (
            self.cleaned_data.get("rx_init_date") or self.cleaned_data.get("rx_init_ago")
        ):
            self.raise_validation_error(
                {"rx_init_date": "This field is required (or the below)."},
                INVALID_ERROR,
            )
        self.not_required_if_true(not on_medications, "rx_init_date")
        self.not_required_if_true(not on_medications, "rx_init_ago")

        try:
            RxDate(self.cleaned_data, reference_date=dx_date)
        except MedicalDateError as e:
            self.raise_validation_error(e.message_dict, e.code)
