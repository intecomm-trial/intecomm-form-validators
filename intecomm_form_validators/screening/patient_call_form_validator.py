from edc_constants.constants import YES
from edc_form_validators import FormValidator


class PatientCallFormValidator(FormValidator):
    def clean(self):
        self.applicable_if(YES, field="answered", field_applicable="respondent")
        self.required_if(YES, field="willing_to_attend", field_required="attend_date")
