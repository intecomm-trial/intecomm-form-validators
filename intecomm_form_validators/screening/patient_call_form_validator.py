from edc_constants.constants import NO, PATIENT, YES
from edc_form_validators import INVALID_ERROR, FormValidator


class PatientCallFormValidator(FormValidator):
    def clean(self):
        self.applicable_if(YES, field="answered", field_applicable="respondent")
        self.applicable_if(YES, field="answered", field_applicable="survival_status")
        if (
            self.cleaned_data.get("respondent") == PATIENT
            and self.cleaned_data.get("survival_status") != YES
        ):
            self.raise_validation_error(
                {"survival_status": "Invalid. Patient is the respondent"}, INVALID_ERROR
            )
        self.applicable_if(YES, field="answered", field_applicable="catchment_area")
        if self.cleaned_data.get("respondent") == PATIENT and self.cleaned_data.get(
            "catchment_area"
        ) not in [YES, NO]:
            self.raise_validation_error(
                {"catchment_area": "Invalid. Patient is the respondent"}, INVALID_ERROR
            )
