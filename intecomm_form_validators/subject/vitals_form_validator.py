from edc_crf.crf_form_validator_mixins import CrfFormValidatorMixin
from edc_dx_review.utils import raise_if_clinical_review_does_not_exist
from edc_form_validators import FormValidator
from edc_visit_schedule.utils import is_baseline
from edc_vitals.form_validators import BloodPressureFormValidatorMixin


class VitalsFormValidator(
    BloodPressureFormValidatorMixin,
    CrfFormValidatorMixin,
    FormValidator,
):
    def clean(self):
        raise_if_clinical_review_does_not_exist(self.cleaned_data.get("subject_visit"))
        self.required_if_true(
            is_baseline(self.cleaned_data.get("subject_visit")),
            field_required="weight",
            inverse=False,
        )
        # TODO: Require weight also at 12M

        for bp_reading in ["one", "two"]:
            self.raise_on_systolic_lt_diastolic_bp(
                sys_field=f"sys_blood_pressure_{bp_reading}",
                dia_field=f"dia_blood_pressure_{bp_reading}",
                **self.cleaned_data,
            )

        self.raise_on_avg_blood_pressure_suggests_severe_htn(**self.cleaned_data)

        self.required_if_true(
            is_baseline(self.cleaned_data.get("subject_visit")),
            field_required="height",
            inverse=False,
        )
