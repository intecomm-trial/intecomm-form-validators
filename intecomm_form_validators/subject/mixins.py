from django import forms
from edc_constants.constants import OTHER, YES
from edc_form_validators import FormValidator
from edc_visit_schedule.utils import is_baseline


class DrugRefillFormValidatorMixin(FormValidator):

    """For example:
    def clean(self):
        medications_exists_or_raise(self.cleaned_data.get("subject_visit"))
        self.validate_rx_as_m2m()
        self.validate_modifications()

    - or -

    def clean(self):
        medications_exists_or_raise(self.cleaned_data.get("subject_visit"))
        self.validate_rx_as_fk()
        self.validate_modifications()
    """

    def validate_rx_as_m2m(self):
        self.m2m_other_specify(OTHER, m2m_field="rx", field_other="rx_other")

    def validate_rx_as_fk(self):
        self.validate_other_specify(field="rx", other_specify_field="rx_other")

    def validate_modifications(self):
        if (
            self.cleaned_data.get("subject_visit")
            and is_baseline(self.cleaned_data.get("subject_visit"))
            and self.cleaned_data.get("rx_modified") == YES
        ):
            raise forms.ValidationError({"rx_modified": "Expected `No` at baseline."})
        self.m2m_required_if(YES, field="rx_modified", m2m_field="modifications")
        self.m2m_other_specify(
            OTHER, m2m_field="modifications", field_other="modifications_other"
        )
        self.m2m_required_if(YES, field="rx_modified", m2m_field="modifications_reason")
        self.m2m_other_specify(
            OTHER,
            m2m_field="modifications_reason",
            field_other="modifications_reason_other",
        )


class BPFormValidatorMixin:
    def validate_bp_reading(self, sys_field, dia_field):
        if self.cleaned_data.get(sys_field) and self.cleaned_data.get(dia_field):
            if self.cleaned_data.get(sys_field) < self.cleaned_data.get(dia_field):
                raise forms.ValidationError(
                    {dia_field: "Systolic must be greater than diastolic."}
                )
