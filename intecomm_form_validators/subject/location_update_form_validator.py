from edc_constants.constants import CLINIC, COMMUNITY
from edc_crf.crf_form_validator_mixins import CrfFormValidatorMixin
from edc_dx_review.form_validator_mixins import ClinicalReviewFollowupFormValidatorMixin
from edc_form_validators import INVALID_ERROR, FormValidator
from edc_visit_schedule.utils import raise_if_baseline


class LocationUpdateFormValidator(
    ClinicalReviewFollowupFormValidatorMixin,
    CrfFormValidatorMixin,
    FormValidator,
):
    def clean(self):
        raise_if_baseline(self.cleaned_data.get("subject_visit"))
        if self.related_visit.appointment.appt_type.name == COMMUNITY:
            self.raise_validation_error(
                {"__all__": "This form is not required"}, error_code=INVALID_ERROR
            )
        elif (
            self.related_visit.appointment.appt_type.name == CLINIC
            and self.cleaned_data.get("location", "") == COMMUNITY
        ):
            self.raise_validation_error(
                {"location": "Invalid. Appointment is not in the community"},
                error_code=INVALID_ERROR,
            )

        self.validate_other_specify(field="location", other_specify_field="location_other")
