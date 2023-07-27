from edc_crf.crf_form_validator import CrfFormValidator
from edc_dx_review.utils import raise_if_clinical_review_does_not_exist
from edc_next_appointment.form_validators import NextAppointmentFormValidatorMixin


class NextAppointmentFormValidator(NextAppointmentFormValidatorMixin, CrfFormValidator):
    def clean(self):
        raise_if_clinical_review_does_not_exist(self.cleaned_data.get("subject_visit"))
        self.validate_date_is_on_clinic_day()
        super().clean()
