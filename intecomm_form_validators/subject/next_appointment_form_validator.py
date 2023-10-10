from edc_appointment.form_validator_mixins import NextAppointmentCrfFormValidatorMixin
from edc_crf.crf_form_validator import CrfFormValidator
from edc_dx_review.utils import raise_if_clinical_review_does_not_exist


class NextAppointmentFormValidator(NextAppointmentCrfFormValidatorMixin, CrfFormValidator):
    def clean(self):
        raise_if_clinical_review_does_not_exist(self.cleaned_data.get("subject_visit"))
        self.validate_date_is_on_clinic_day()
        super().clean()
