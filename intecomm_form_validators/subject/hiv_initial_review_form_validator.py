from django import forms
from edc_constants.constants import OTHER, PENDING, YES
from edc_crf.crf_form_validator_mixins import CrfFormValidatorMixin
from edc_dx_review.medical_date import DxDate, MedicalDateError, RxDate
from edc_dx_review.utils import raise_if_clinical_review_does_not_exist
from edc_form_validators import FormValidator


class HivInitialReviewFormValidator(
    CrfFormValidatorMixin,
    FormValidator,
):
    def __init__(self, **kwargs):
        self.dx_date = None
        self.rx_init_date = None
        super().__init__(**kwargs)

    def clean(self):
        raise_if_clinical_review_does_not_exist(self.cleaned_data.get("subject_visit"))

        try:
            self.dx_date = DxDate(self.cleaned_data)
        except MedicalDateError as e:
            self.raise_validation_error(e.message_dict, e.code)

        self.applicable_if(YES, field="receives_care", field_applicable="clinic")

        self.required_if(OTHER, field="clinic", field_required="clinic_other")

        self.applicable_if(YES, field="receives_care", field_applicable="rx_init")

        self.validate_rx_init_date()

        self.required_if(YES, field="rx_init", field_required="has_vl")

        self.validate_viral_load()

        self.required_if(YES, field="rx_init", field_required="has_cd4")

        self.validate_cd4()

    def validate_rx_init_date(self):
        if self.cleaned_data.get("rx_init") == YES:
            try:
                self.rx_init_date = RxDate(self.cleaned_data, reference_date=self.dx_date)
            except MedicalDateError as e:
                self.raise_validation_error(e.message_dict, e.code)
        else:
            self.not_required_if_true(
                self.cleaned_data.get("rx_init_date"),
                field="rx_init_date",
            )
            self.not_required_if_true(
                self.cleaned_data.get("rx_init_ago"),
                field="rx_init_ago",
            )

    def validate_viral_load(self):
        self.required_if(YES, PENDING, field="has_vl", field_required="drawn_date")
        if self.cleaned_data.get("drawn_date") and self.dx_date:
            if self.cleaned_data.get("drawn_date") < self.dx_date:
                raise forms.ValidationError(
                    {"drawn_date": "Invalid. Cannot be before HIV diagnosis."}
                )
        self.required_if(YES, field="has_vl", field_required="vl")
        self.required_if(YES, field="has_vl", field_required="vl_quantifier")

    def validate_cd4(self):
        self.required_if(YES, field="has_cd4", field_required="cd4")
        self.required_if(YES, field="has_cd4", field_required="cd4_date")
        if self.cleaned_data.get("cd4_date") and self.dx_date:
            if self.cleaned_data.get("cd4_date") < self.dx_date:
                raise forms.ValidationError(
                    {"cd4_date": "Invalid. Cannot be before HIV diagnosis."}
                )
