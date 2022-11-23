from django import forms
from edc_consent.form_validators import SubjectConsentFormValidatorMixin
from edc_form_validators import FormValidator


class SubjectConsentFormValidator(SubjectConsentFormValidatorMixin, FormValidator):
    def validate_identity(self) -> None:
        """Override to validate `identity_type` is a hospital
        number and `identity` matches the screening form.
        """
        if self.cleaned_data.get("identity_type") != "hospital_no":
            raise forms.ValidationError({"identity_type": "Expected 'hospital number'."})
