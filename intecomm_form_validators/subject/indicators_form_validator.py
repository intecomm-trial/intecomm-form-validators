from django import forms
from edc_constants.constants import NO, NOT_REQUIRED, YES
from edc_crf.crf_form_validator import CrfFormValidator
from edc_dx_review.utils import raise_if_clinical_review_does_not_exist
from edc_form_validators import FormValidator
from edc_visit_schedule.utils import is_baseline
from edc_vitals.form_validators import BloodPressureFormValidatorMixin


class IndicatorsFormValidator(
    BloodPressureFormValidatorMixin, CrfFormValidator, FormValidator
):
    def clean(self):
        raise_if_clinical_review_does_not_exist(self.cleaned_data.get("subject_visit"))
        self.required_if_true(
            is_baseline(self.cleaned_data.get("subject_visit")),
            field_required="weight",
            inverse=False,
        )
        self.required_if_true(
            is_baseline(self.cleaned_data.get("subject_visit")),
            field_required="height",
            inverse=False,
        )

        self.required_if(NO, field="r1_taken", field_required="r1_reason_not_taken")
        self.required_if(YES, field="r1_taken", field_required="sys_blood_pressure_r1")
        self.required_if(YES, field="r1_taken", field_required="dia_blood_pressure_r1")
        self.raise_on_systolic_lt_diastolic_bp(
            sys_field="sys_blood_pressure_r1",
            dia_field="dia_blood_pressure_r1",
        )

        # TODO: validate r2 != YES if r1 == NO

        if self.cleaned_data.get("r2_taken") == NOT_REQUIRED and self.htn_initial_review:
            raise forms.ValidationError(
                {"r2_taken": "Invalid. Expected YES or NO. Patient is hypertensive."}
            )
        self.required_if(NO, field="r2_taken", field_required="r2_reason_not_taken")
        self.required_if(YES, field="r2_taken", field_required="sys_blood_pressure_r2")
        self.required_if(YES, field="r2_taken", field_required="dia_blood_pressure_r2")
        self.raise_on_systolic_lt_diastolic_bp(
            sys_field="sys_blood_pressure_r2",
            dia_field="dia_blood_pressure_r2",
        )
