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
        else:
            if DRUGS in self.get_m2m_selected("managed_by"):
                try:
                    RxDate(self.cleaned_data, reference_date=dx_date)
                except MedicalDateError as e:
                    self.raise_validation_error(e.message_dict, e.code)
            else:
                if self.cleaned_data.get("rx_init_date"):
                    self.raise_validation_error(
                        {"rx_init_date": "This field is not required"}, INVALID_ERROR
                    )
                if self.cleaned_data.get("rx_init_ago"):
                    self.raise_validation_error(
                        {"rx_init_ago": "This field is not required"}, INVALID_ERROR
                    )

        self.m2m_other_specify(m2m_field="managed_by", field_other="managed_by_other")
