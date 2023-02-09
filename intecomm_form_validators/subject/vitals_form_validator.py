from edc_constants.constants import ESTIMATED, MEASURED, NO, YES
from edc_crf.crf_form_validator_mixins import CrfFormValidatorMixin
from edc_dx_review.utils import raise_if_clinical_review_does_not_exist
from edc_form_validators import INVALID_ERROR, FormValidator
from edc_visit_schedule.utils import is_baseline
from edc_vitals.form_validators import BloodPressureFormValidatorMixin

from intecomm_form_validators.utils import is_end_of_study


class VitalsFormValidator(
    BloodPressureFormValidatorMixin,
    CrfFormValidatorMixin,
    FormValidator,
):
    def clean(self):
        raise_if_clinical_review_does_not_exist(self.cleaned_data.get("subject_visit"))

        self.weight_required_at_baseline_and_eos()

        self.required_if(
            MEASURED, ESTIMATED, field="weight_determination", field_required="weight"
        )

        self.required_if_true(
            is_baseline(self.cleaned_data.get("subject_visit")),
            field_required="height",
            inverse=False,
            required_msg="(at this timepoint)",
        )

        self.required_if(YES, field="bp_one_taken", field_required="sys_blood_pressure_one")
        self.required_if(YES, field="bp_one_taken", field_required="dia_blood_pressure_one")
        self.required_if(NO, field="bp_one_taken", field_required="bp_one_not_taken_reason")
        self.raise_on_systolic_lt_diastolic_bp(
            sys_field="sys_blood_pressure_one",
            dia_field="dia_blood_pressure_one",
            **self.cleaned_data,
        )

        self.required_if(YES, field="bp_two_taken", field_required="sys_blood_pressure_two")
        self.required_if(YES, field="bp_two_taken", field_required="dia_blood_pressure_two")
        self.required_if(NO, field="bp_two_taken", field_required="bp_two_not_taken_reason")
        self.applicable_if(YES, field="bp_one_taken", field_applicable="bp_two_taken")
        self.raise_on_systolic_lt_diastolic_bp(
            sys_field="sys_blood_pressure_two",
            dia_field="dia_blood_pressure_two",
            **self.cleaned_data,
        )

        self.applicable_if(YES, field="bp_one_taken", field_applicable="severe_htn")
        opts = {
            "severe_htn": self.cleaned_data.get("severe_htn"),
            "sys_blood_pressure_one": self.cleaned_data.get("sys_blood_pressure_one"),
            "dia_blood_pressure_one": self.cleaned_data.get("dia_blood_pressure_one"),
            "sys_blood_pressure_two": (
                self.cleaned_data.get("sys_blood_pressure_two")
                if self.cleaned_data.get("sys_blood_pressure_two") is not None
                else self.cleaned_data.get("sys_blood_pressure_one")
            ),
            "dia_blood_pressure_two": (
                self.cleaned_data.get("dia_blood_pressure_two")
                if self.cleaned_data.get("dia_blood_pressure_two") is not None
                else self.cleaned_data.get("dia_blood_pressure_one")
            ),
        }
        self.raise_on_avg_blood_pressure_suggests_severe_htn(**opts)

    def weight_required_at_baseline_and_eos(self):
        if (
            self.cleaned_data.get("weight_determination")
            and self.cleaned_data.get("weight_determination") != MEASURED
            and (
                is_baseline(self.cleaned_data.get("subject_visit"))
                or is_end_of_study(self.cleaned_data.get("subject_visit"))
            )
        ):
            self.raise_validation_error(
                {"weight_determination": "Expected weight to be measured at this timepoint"},
                INVALID_ERROR,
            )
