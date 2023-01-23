from django import forms
from django.utils.html import format_html
from edc_consent.form_validators import SubjectConsentFormValidatorMixin
from edc_constants.constants import YES
from edc_form_validators import INVALID_ERROR, FormValidator


class SubjectConsentFormValidator(SubjectConsentFormValidatorMixin, FormValidator):
    def clean(self) -> None:
        link = (
            f'<a href="{self.patient_log.get_changelist_url()}?'
            f'q={str(self.patient_log.id)}">{self.patient_log}</a>'
        )
        if self.patient_log.stable != YES:
            errmsg = format_html(
                "Patient is not known to be stable and in-care. "
                f"See patient log for {link}."
            )
            self.raise_validation_error(errmsg, error_code=INVALID_ERROR)

    @property
    def patient_log(self):
        return self.cleaned_data.get("patient_log")

    def validate_identity(self) -> None:
        """Override to validate `identity_type` is a hospital
        number and `identity` matches the screening form.
        """
        if self.cleaned_data.get("identity_type") != "hospital_no":
            raise forms.ValidationError({"identity_type": "Expected 'hospital number'."})
